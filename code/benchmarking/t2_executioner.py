import json
import subprocess
from pathlib import Path
from typing import Iterable, List
import sys

from t2_parser import parse

def run_and_capture(cmd: List[str], echo: bool = True) -> Iterable[str]:
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    ) as p:
        assert p.stdout is not None
        for line in p.stdout:
            if echo:
                print(line, end="")
            yield line
        rc = p.wait()
        if rc != 0:
            raise SystemExit(rc)

def default_cmd() -> List[str]:
    return [sys.executable, "run_t2.py",
        "--lp_model", "../lp_model",
        "--tg_model", "../tg_model",
        "--pretrain_model", "../pretrain_model",
        "--test_json", "Dataset/T2/test/test.json",
    ]

def main():
    cmd = default_cmd()

    lines = list(run_and_capture(cmd, echo=False))
    
    metrics = parse(lines)

    print(json.dumps(metrics, indent=2, sort_keys=True))

    out_path = Path('./out/t2_benchmark_results.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
