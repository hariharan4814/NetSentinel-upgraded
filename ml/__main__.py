"""Explicit offline CLI. No automatic training, capture, retries or service startup."""
import argparse
import json
import os
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

from .pipeline import read_json, write_json, digest, rows, validate, train, load, score
from .exporter import export
from backend.detection.contract import validate_manifest


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Publication redirects are forbidden")


def publish(dataset, base_url, manifest=None, scores=None):
    """One bounded request at a time. Stop on failure; replay the saved batch to retry."""
    parts = urlsplit(base_url)
    if (parts.scheme != "http" or parts.hostname not in ("127.0.0.1", "localhost", "::1")
            or parts.username or parts.password or parts.path not in ("", "/") or parts.query or parts.fragment):
        raise ValueError("Publication requires an explicit loopback HTTP origin")
    records = rows(dataset, dataset["rows"][0]["session"]["mode"])
    if (manifest is None) != (scores is None):
        raise ValueError("Publish model manifest and scored batch together")
    def credential(name):
        token = os.environ.get(name, "")
        if not (32 <= len(token) <= 256 and token.isascii() and not any(c.isspace() for c in token)) or token.startswith("replace-with-"):
            raise ValueError(f"Configure {name} in the process environment before publication")
        return token
    ingest_token = credential("NETSENTINEL_INGEST_TOKEN")
    model_token = credential("NETSENTINEL_MODEL_TOKEN") if manifest is not None else None
    if model_token == ingest_token:
        raise ValueError("Ingestion and model publication require separate credentials")
    if manifest is not None:
        validate_manifest(manifest)
        if scores["dataset_sha256"] != digest(dataset) or scores["model_version_id"] != manifest["id"]:
            raise ValueError("Scored batch/dataset/model mismatch")
        if len(scores["results"]) != len(records):
            raise ValueError("Scored batch count mismatch")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    posted = 0
    def post(endpoint, value):
        nonlocal posted
        body = json.dumps(value, allow_nan=False).encode()
        if len(body) > 65536:
            raise ValueError("Publication record exceeds API body limit")
        request = Request(base_url.rstrip('/') + '/api/v1/' + endpoint + '/', data=body,
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + (
                              model_token if endpoint in ("model-versions", "anomaly-results") else ingest_token)}, method="POST")
        with opener.open(request, timeout=5) as response:
            if response.status not in (200, 201):
                raise ValueError("Unexpected publication response")
            if len(response.read(65537)) > 65536:
                raise ValueError("Oversized publication response")
        posted += 1
    sessions = set()
    for row in records:
        session = row["session"]
        if session["session_id"] not in sessions:
            post("monitoring-sessions", session)
            sessions.add(session["session_id"])
        post("windows", row["window"])
    if manifest is not None:
        post("model-versions", {"id": manifest["id"], "manifest": manifest})
        for result in scores["results"]:
            post("anomaly-results", result)
    return {"successful_requests": posted, "automatic_retries": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description="NetSentinel host-v1 offline baseline workflow. Anomaly != attack.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("export")
    p.add_argument("logs", nargs="+")
    p.add_argument("--source-id", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--mode", choices=("LIVE", "SIMULATION", "REPLAY"), default="LIVE")
    p.add_argument("--out", required=True)
    p = sub.add_parser("inspect-dataset")
    p.add_argument("dataset")
    for command in ("validate", "train"):
        p = sub.add_parser(command)
        p.add_argument("dataset")
        p.add_argument("--review", required=True)
        p.add_argument("--mode", choices=("LIVE", "SIMULATION", "REPLAY"), default="LIVE")
        if command == "train":
            p.add_argument("--out", required=True)
    p = sub.add_parser("inspect-model")
    p.add_argument("manifest")
    p = sub.add_parser("score")
    p.add_argument("dataset")
    p.add_argument("--model", required=True)
    p.add_argument("--trusted-sha256", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("publish")
    p.add_argument("dataset")
    p.add_argument("--base-url", required=True)
    p.add_argument("--manifest")
    p.add_argument("--scores")
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            result = export(args.logs, args.source_id, args.profile, args.mode)
            write_json(args.out, result)
            result = result["export"]
        elif args.command == "inspect-dataset":
            dataset = read_json(args.dataset)
            result = {"dataset_sha256": digest(dataset), "export": dataset.get("export"), "rows": len(dataset["rows"]),
                      "run_ids": sorted({r["session"]["run_id"] for r in dataset["rows"]}),
                      "notice": "Counts are not operator review or proof of benign activity."}
        elif args.command in ("validate", "train"):
            dataset, review = read_json(args.dataset), read_json(args.review)
            result = ({name: len(rs) for name, rs in validate(dataset, review, args.mode).items()}
                      if args.command == "validate" else train(dataset, review, args.out, args.mode))
        elif args.command == "inspect-model":
            result = validate_manifest(read_json(args.manifest))  # JSON only, no pickle loading
        elif args.command == "score":
            result = score(read_json(args.dataset), args.model, args.trusted_sha256)
            write_json(args.out, result)
        else:
            result = publish(read_json(args.dataset), args.base_url,
                             read_json(args.manifest) if args.manifest else None,
                             read_json(args.scores) if args.scores else None)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
