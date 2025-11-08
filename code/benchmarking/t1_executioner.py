import argparse
import json
import os
import subprocess
import sys
from typing import Iterable, List

from t1_parser import parse


def run_and_capture(cmd: List[str], echo: bool = True) -> Iterable[str]:
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    ) as p:
        assert p.stdout is not None
        for line in p.stdout:
            if echo:
                print(line, end="")
            yield line
        rc = p.wait()
        if rc != 0:
            raise SystemExit(rc)


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

    cmd.extend(args.run_args)

    lines = list(run_and_capture(cmd, echo=False))
    metrics = parse(lines)

    print(json.dumps(metrics, indent=2, sort_keys=True))

    os.makedirs("./out/benchmark/", exist_ok=True)

    with open("./out/benchmark/t1_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
