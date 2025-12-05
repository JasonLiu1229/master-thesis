import argparse
import json
import logging
import os
import time

from pathlib import Path
from typing import List

import yaml

from logger import setup_logging
from pipeline.eval import compute_final_metrics, evaluate, PairMetrics
from pipeline.helper import (
    extract_tests_from_file,
    post_process_eval,
    post_process_file,
)
from pipeline.renamer import rename, rename_eval
from tqdm import tqdm

setup_logging("pipeline")
logger = logging.getLogger("pipeline")

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

MODE = None


def argument_parser():
    parser = argparse.ArgumentParser(description="Pipeline configuration")

    parser.add_argument(
        "--dir",
        help="Folder of files that will be fed into the pipeline. "
        "Valid only when mode is 'dir' or 'eval'. "
        "For 'eval', the directory must contain .jsonl files.",
        type=Path,
    )

    parser.add_argument(
        "--file",
        help="Single file that will be fed into the pipeline. "
        "Valid only when mode is 'single'.",
        type=Path,
    )

    parser.add_argument(
        "--mode",
        help="Different modes the pipeline can be set to",
        choices=["eval", "single", "dir"],
        required=True,
    )

    parser.add_argument(
        "--output",
        help="Directory where results/logs/output files should be written.",
        default="out",
        type=Path,
    )

    parser.add_argument(
        "--force",
        help="Overwrite existing output directory/files if they already exist.",
        action="store_true",
    )

    # Version
    parser.add_argument("--version", action="version", version="Pipeline v1.0.0")

    return parser


def process_single(file: Path, out: Path, force: bool):
    test_cases_spans = extract_tests_from_file(file)

    test_cases = list()

    for test_span in tqdm(
        test_cases_spans,
        desc=f"Renaming tests in {file.name}",
        leave=False,
        unit="test",
    ):
        test_cases.append(rename(test_span))

    output_file = out / file.name

    source_code = None

    with open(file, "r") as file:
        source_code = file.read()

    post_process_file(
        source_code=source_code,
        test_cases=test_cases,
        output_file=output_file,
        force=force,
    )

    logger.info(f"Renamed and outputed file: {file.name} to {output_file}")


def process_single_eval(file_path: Path) -> tuple[List[PairMetrics], int]:
    logger.info(f"\nProcessing file: {file_path.name}")

    items = []  # in case more than one oracle in one file

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    metrics: List[PairMetrics] = []

    failed_count = 0

    for item in items:
        obf_code = item.get("prompt", "")
        oracle_code = item.get("response", "")

        if not obf_code or not oracle_code:
            logger.warning(
                f"One of the codes was missing to complete evaluation for that oracle in file {file_path.name}"
            )
            continue

        predicted_code, clean = rename_eval(obf_code)

        if not clean:  # do not evaluate failed code
            failed_count += 1
        else:
            metrics.append(evaluate(oracle_code, predicted_code))

    return metrics, failed_count


def process_folder(root: Path, out: Path, is_eval: bool, force: bool):
    out.mkdir(parents=True, exist_ok=True)

    if is_eval:
        logger.info("Running evaluation")
        jsonl_files = sorted(root.glob("*.jsonl"))

        failed_count = 0
        total_metrics: List[PairMetrics] = []

        limit = len(jsonl_files)

        if config["AMOUNT_OF_EVAL_SAMPLES"] != -1:
            limit = config["AMOUNT_OF_EVAL_SAMPLES"]

        start_time = time.time()
        
        for file in tqdm(jsonl_files[:limit], desc="Oracle files", unit="oracle"):
            metrics, count = process_single_eval(file)
            total_metrics.extend(metrics)
            failed_count += count

        final_metric = compute_final_metrics(total_metrics)

        final_metric["failes"] = failed_count
        
        final_metric["total_time"] = time.time() - start_time

        post_process_eval(final_metric, force)

        logger.info("Folder evaluated")
        return

    java_files = sorted(root.glob("*.java"))

    for file in tqdm(java_files, desc="Files", unit="file"):
        process_single(file, out, force)

    logger.info("Folder processed")


if __name__ == "__main__":
    args = argument_parser().parse_args()

    MODE = args.mode

    if MODE == "single":
        logger.info("Processing single file")

        if not os.path.exists(args.file):
            logger.error(f"Path {args.file} does not exists")

        process_single(file=args.file, out=args.output, force=args.force)
    else:
        logger.info("Processing folder")

        if not os.path.exists(args.dir):
            logger.error(f"Path {args.dir} does not exists")

        process_folder(
            args.dir, out=args.output, is_eval=(MODE == "eval"), force=args.force
        )
