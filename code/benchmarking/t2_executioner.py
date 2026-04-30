import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

from t2_parser import parse


def run_and_capture(cmd: List[str], echo: bool = True) -> List[str]:
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    lines = result.stdout.splitlines(keepends=True)
    if echo:
        print(result.stdout, end="")
    if result.returncode != 0:
        if not echo:
            print(result.stdout, file=sys.stderr)
        raise SystemExit(result.returncode)
    return lines


def default_cmd() -> List[str]:
    return [
        sys.executable,
        "run_t2.py",
        "--mode",
        "dataset",
        "--lp_model",
        "/app/lp_model",
        "--tg_model",
        "/app/tg_model",
        "--pretrain_model",
        "/app/pretrain_model",
        "--dataset_dir",
        "/app/code/in/test",
        "--output_dir",
        "/app/code/out/benchmark/",
        "--indices_file",
        "/app/code/indices.txt",
    ]


def main():
    cmd = default_cmd()

    lines = list(run_and_capture(cmd, echo=False))

    metrics = parse(lines)

    print(json.dumps(metrics, indent=2, sort_keys=True))

    os.makedirs("./out/benchmark/", exist_ok=True)

    out_path = Path("./out/benchmark/t2_benchmark_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
