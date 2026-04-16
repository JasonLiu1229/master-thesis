import argparse
import json
import os
import subprocess
import sys
from typing import List

from t1_parser import parse


def run_and_capture(cmd: List[str], echo: bool = True) -> List[str]:
    """Run a command, return its stdout lines. On non-zero exit, print stderr and raise."""
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    lines = result.stdout.splitlines(keepends=True)
    if echo:
        print(result.stdout, end="")
    if result.returncode != 0:
        # Always show output when the process failed, even in silent mode
        if not echo:
            print(result.stdout, file=sys.stderr)
        raise SystemExit(result.returncode)
    return lines


def parse_args():
    ap = argparse.ArgumentParser(description="Execute run_t1.py and parse its metrics.")
    ap.add_argument(
        "--run-args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to run_t1.py (everything after this flag).",
    )
    return ap.parse_args()


def main():
    args = parse_args()

    cmd: List[str] = [sys.executable, "run_t1.py"]
    if args.run_args:
        cmd.extend(args.run_args)

    lines = run_and_capture(cmd, echo=False)
    metrics = parse(lines)

    print(json.dumps(metrics, indent=2, sort_keys=True))

    os.makedirs("./out/benchmark/", exist_ok=True)

    with open("./out/benchmark/t1_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
