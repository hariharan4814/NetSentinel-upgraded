"""Run an entirely local, payload-free SIMULATION experiment."""
import argparse
import json
from pathlib import Path
import sys

from .contracts import DEFAULTS, ExperimentCancelled, canonical_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("demo", "Generate, train, evaluate, explain and save artifacts"),
                            ("generate", "Generate a labelled metadata-only dataset"),
                            ("benchmark", "Repeated seeds, whole-run bootstrap and excluded-family study")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--out", required=True, type=Path)
        for key, value in DEFAULTS.items():
            command.add_argument("--" + key.replace("_", "-"), type=type(value), default=value)
        if name == "benchmark":
            command.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
            command.add_argument("--excluded-family", choices=["fanout", "syn_burst", "udp_burst"], default="fanout")
            command.add_argument("--bootstrap-repetitions", type=int, default=200)
    inspect = commands.add_parser("inspect", help="Read result summary without deserializing a model")
    inspect.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            path = args.directory / "result.json"
            if path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError("result is oversized")
            result = json.loads(path.read_text(encoding="utf-8"))
        else:
            config = {key: getattr(args, key) for key in DEFAULTS}
            previous = [None]
            def progress(stage, completed=None, total=None):
                if stage != previous[0] or completed == total:
                    print(f"{stage}: {completed}/{total}" if total is not None else stage, file=sys.stderr)
                    previous[0] = stage
            if args.command == "benchmark":
                from .artifacts import atomic_bytes
                from .benchmark import run_benchmark
                args.out.mkdir(parents=True, exist_ok=True)
                target = args.out / "benchmark.json"
                if target.exists():
                    raise ValueError("output already contains a benchmark")
                result = run_benchmark(config, seeds=args.seeds, excluded_family=args.excluded_family,
                                       repetitions=args.bootstrap_repetitions, progress=progress)
                atomic_bytes(target, canonical_json(result))
                print(json.dumps({"mode": result["mode"], "seeds": result["seeds"],
                                  "summary": result["summary"], "seconds": result["seconds"]}, indent=2))
                return 0
            if args.command == "generate":
                from .artifacts import atomic_bytes
                from .simulation import generate_dataset
                data = generate_dataset(config, progress=progress)
                args.out.mkdir(parents=True, exist_ok=True)
                if any((args.out / name).exists() for name in ("dataset.json", "truth.json")):
                    raise ValueError("output already contains a dataset")
                atomic_bytes(args.out / "dataset.json", canonical_json({key: value for key, value in data.items() if key != "truth"}))
                atomic_bytes(args.out / "truth.json", canonical_json(data["truth"]))
                print(json.dumps({"mode": data["mode"], "sha256": data["sha256"], "windows": len(data["samples"])}))
                return 0
            from .pipeline import run_experiment
            result = run_experiment(config, output_dir=args.out, progress=progress)
        print(json.dumps({"mode": result["mode"], "dataset": result["dataset"]["sha256"],
                          "windows": result["dataset"]["total_windows"],
                          "classification": [{"model": row["model"], "macro_f1": row["macro_f1"]} for row in result["classification"]],
                          "false_alerts_per_hour": result["anomaly"]["false_alerts_per_hour"],
                          "seconds": result["performance"]["total_seconds"]}, indent=2))
        return 0
    except (ValueError, OSError, ExperimentCancelled, KeyboardInterrupt) as error:
        print(f"Experiment did not complete: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
