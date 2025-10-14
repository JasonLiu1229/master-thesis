import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable, List

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

def parse_args():
    ap = argparse.ArgumentParser(description="Execute run_t2.py and parse its metrics.")
    ap.add_argument(
        "--cmd",
        nargs=argparse.REMAINDER,
        help=(
            "Optional full command to run T2. "
            "If omitted, uses the built-in default command."
        ),
    )
    ap.add_argument(
        "--run-args",
        nargs=argparse.REMAINDER,
        help="If you want to keep the default command but add/override run_t2.py args, pass them here."
    )
    ap.add_argument("--out", default=None, help="Optional path to write parsed metrics JSON.")
    ap.add_argument("--no-echo", action="store_true", help="Do not echo raw output while running.")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON on stdout.")
    return ap.parse_args()

def default_cmd() -> List[str]:
    return [
        "python3.8", "run_t2.py",
        "--lp_model", "../lp_model",
        "--tg_model", "../tg_model",
        "--pretrain_model", "../pretrain_model",
        "--test_json", "Dataset/T2/test/test.json",
    ]

def main():
    args = parse_args()

    if args.cmd:
        cmd = args.cmd
    else:
        cmd = default_cmd()
        if args.run_args:
            cmd.extend(args.run_args)

    lines = list(run_and_capture(cmd, echo=not args.no_echo))
    metrics = parse(lines)

    if args.pretty:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print(json.dumps(metrics, separators=(",", ":"), sort_keys=True))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
