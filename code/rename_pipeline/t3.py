import argparse
from pathlib import Path

from logger import setup_logging
import logging

setup_logging("pipeline")
logger = logging.getLogger("pipeline")

def argument_parser():
    parser = argparse.ArgumentParser(
        description="Pipeline configuration"
    )

    parser.add_argument(
        "--dir",
        help="Folder of files that will be fed into the pipeline. "
             "Valid only when mode is 'dir' or 'eval'. "
             "For 'eval', the directory must contain .jsonl files.",
        type=Path
    )

    parser.add_argument(
        "--file",
        help="Single file that will be fed into the pipeline. "
             "Valid only when mode is 'single'.",
        type=Path
        
    )

    parser.add_argument(
        "--mode",
        help="Different modes the pipeline can be set to",
        choices=["eval", "single", "dir"],
        required=True
    )

    parser.add_argument(
        "--output",
        help="Directory where results/logs/output files should be written.",
        default="out",
        type=Path
    )

    # parser.add_argument(
    #     "--workers",
    #     help="Number of parallel workers to use for processing.",
    #     type=int,
    #     default=1
    # )

    parser.add_argument(
        "--config",
        help="Optional YAML/JSON configuration file for pipeline parameters.",
        type=Path
    )

    parser.add_argument(
        "--force",
        help="Overwrite existing output directory/files if they already exist.",
        action="store_true"
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="Pipeline v1.0.0"
    )

    return parser

if __name__ == "__main__":
    
    args = argument_parser()
