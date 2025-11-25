import argparse
import logging
import os

from pathlib import Path

import tqdm

from logger import setup_logging
from pipeline.helper import extract_tests_from_file, post_process_file
from pipeline.renamer import rename

setup_logging("pipeline")
logger = logging.getLogger("pipeline")


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

    # parser.add_argument(
    #     "--workers",
    #     help="Number of parallel workers to use for processing.",
    #     type=int,
    #     default=1
    # )

    # parser.add_argument(
    #     "--config",
    #     help="Optional YAML/JSON configuration file for pipeline parameters.",
    #     type=Path
    # )

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

    post_process_file(test_cases=test_cases, output_file=output_file, force=force)

    logger.info(f"Renamed and outputed file: {file} to {output_file}")


def process_folder(root: Path, out: Path, is_eval: bool, force: bool):
    out.mkdir(parents=True, exist_ok=True)

    if is_eval:
        logger.info("Running evaluation")
        logger.warning("not implemented yet")
        return

    java_files = sorted(root.glob("*.java"))

    for file in tqdm(java_files, desc="Files", unit="file"):
        process_single(file, out, force)

    logger.info("Folder processed")


if __name__ == "__main__":
    args = argument_parser().parse_args()

    if args.mode == "single":
        logger.info("Processing single file")

        if not os.path.exists(args.file):
            logger.error(f"Path {args.file} does not exists")

        process_single(file=args.file, out=args.out, force=args.force)
    else:
        logger.info("Processing folder")

        if not os.path.exists(args.dir):
            logger.error(f"Path {args.dir} does not exists")

        process_folder(
            args.dir, out=args.out, is_eval=(args.mode == "eval"), force=args.force
        )
