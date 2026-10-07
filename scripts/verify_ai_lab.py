"""Real local HTTP integration smoke: Next session/CSRF -> Django -> spawned ML worker.

Uses labelled generated SIMULATION data, new isolated storage and ephemeral secrets.
No external services, private traffic, browser automation or PostgreSQL validation.
"""
import http.cookiejar
import json
from pathlib import Path
import secrets
import time
import urllib.error
import urllib.request

from run_ai_lab import LabStack, ROOT


def main():
    output = ROOT / "artifacts/lab" / ("integration-" + time.strftime("%Y%m%d-%H%M%S"))
    stack = LabStack(secrets.token_hex(24), state=output)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf = None
    checks = []

    def call(path, body=None, expected=200, *, origin=None, include_csrf=True):
        headers = {"Origin": origin or stack.url, "X-NetSentinel-Request": "local-ui-v1"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if csrf and include_csrf:
            headers["X-CSRF-Token"] = csrf
        request = urllib.request.Request(stack.url + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            response = opener.open(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            if response.status != expected:
                raise AssertionError(f"{path}: expected HTTP {expected}, received {response.status}")
            return json.load(response)

    def await_job(job, terminal="SUCCEEDED"):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            result = call("/api/lab/jobs/" + job["id"])
            if result["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                assert result["status"] == terminal, result["status"]
                return result
            time.sleep(0.5)
        raise AssertionError("Worker did not reach a terminal state within 120 seconds")

    try:
        stack.start()
        call("/api/lab/jobs", expected=401)
        checks.append("Unauthenticated job access denied")
        auth = call("/api/local-auth", {"password": stack.password})
        csrf = auth["csrf"]
        call("/api/lab/jobs", {"config": {}}, expected=403, include_csrf=False)
        call("/api/lab/jobs", {"config": {}}, expected=403, origin="https://hostile.invalid")
        call("/api/lab/jobs", {"config": {"target": "http://example.invalid"}}, expected=400)
        checks.append("Session, CSRF, hostile-origin and arbitrary-input boundaries enforced")
        config = {"seed": 42, "runs_per_family": 6, "windows_per_run": 12,
                  "intensity": 1.0, "noise": 0.15, "gap_probability": 0.02}
        job = call("/api/lab/jobs", {"config": config}, expected=201)
        completed = await_job(job)
        result = completed["result"]
        assert result["mode"] == "SIMULATION" and result["schema_version"] == "lab-result-v1"
        assert result["dataset"]["total_windows"] == 360
        assert len(result["classification"]) >= 3 and result["explanations"]
        assert all(abs(case["additivity_error"]) < 1e-5 for case in result["explanations"])
        checks.append("Real worker generated 360 windows, trained models and returned measured SHAP results")
        (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        cancel = call("/api/lab/jobs", {"config": {**config, "seed": 43, "runs_per_family": 30, "windows_per_run": 120}}, expected=201)
        call("/api/lab/jobs/" + cancel["id"] + "/cancel", {})
        await_job(cancel, "CANCELLED")
        checks.append("User cancellation persisted through the API")
        stack.stop()
        stack.start()
        csrf = call("/api/local-auth", {"password": stack.password})["csrf"]
        restored = call("/api/lab/jobs/" + job["id"])
        assert restored["result"]["dataset"]["sha256"] == result["dataset"]["sha256"]
        checks.append("Saved experiment survived complete stack restart")
        evidence = {"scope": "SIMULATION; explicit SQLite standalone runtime", "checks": checks,
                    "not_verified": ["PostgreSQL", "browser interaction", "PDF rendering", "LIVE traffic"],
                    "result": "PASS"}
        (output / "verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
        print("Evidence:", output)
    finally:
        stack.stop()


if __name__ == "__main__":
    main()
