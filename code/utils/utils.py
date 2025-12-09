import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from typing import List

import javalang

from llm_client import LLMClient

from logger import setup_logging
from prompts import REASON_PROMPT, REASON_SYSTEM, SIMPLIFY_PROMPT, SIMPLIFY_SYSTEM
from tqdm import tqdm

setup_logging("utils")
logger = logging.getLogger("utils")

# File sizes in bytes -> medium is in between small and big
BIG = 30000
SMALL = 1000


@dataclass
class JavaReason:
    line_count: int
    need_simplify: bool = False
    notes: List[str]
    size_reasons: List[str]
    simplification_goals: List[str]


def check_size(file: Path):
    return file.stat().st_size


def sort_files(origin_folder: Path | str, out: Path | str):
    if not origin_folder.exists():
        raise FileNotFoundError(f"{origin_folder} does not exist")
    if not origin_folder.is_dir():
        raise NotADirectoryError(f"{origin_folder} is not a directory")

    files = [f for f in origin_folder.iterdir() if f.is_file()]

    out.mkdir(parents=True, exist_ok=True)

    big_path = out / "big"
    medium_path = out / "medium"
    small_path = out / "small"

    big_path.mkdir(exist_ok=True)
    medium_path.mkdir(exist_ok=True)
    small_path.mkdir(exist_ok=True)

    for file in tqdm(files, desc="files", unit="file"):
        size = check_size(file)
        if size >= BIG:
            shutil.copy(file, big_path / file.name)
        elif size >= SMALL:
            shutil.copy(file, medium_path / file.name)
        else:
            shutil.copy(file, small_path / file.name)


def simplify(input: Path, output: Path):
    """
    This code will just take in java files and look why it is big and prompt it so it simplifies it.

    This means it prompts the LLM once for the reason why it is big and based on that we make a prompt that simplifies it in the right way.
    """
    if not input.exists():
        raise FileNotFoundError(f"{input} does not exist")
    if not input.is_dir():
        raise NotADirectoryError(f"{input} is not a directory")
    
    def _prompt_reason(source_code: str) -> JavaReason:
        pass

    def _simplify_code(source_code: str, java_reason: JavaReason) -> str:
        pass

    java_files = sorted(input.glob("*.java"))

    output.mkdir(exist_ok=True, parents=True)

    for file in tqdm(java_files, desc="Java files", unit="file"):
        with open(file, "r") as f:
            java_reason = _prompt_reason(file.read())

            candidate_code = file.read()
            original_lines_of_code = len(f.splitlines())

            if java_reason.need_simplify:
                logger.info(f"Performing simplification on {file.name}")

                candidate_code = _simplify_code(candidate_code, java_reason)

            if original_lines_of_code < len(candidate_code.splitlines()):
                logger.error(
                    "Original code had less lines than new one, new code will not be made"
                )
                continue


def main():
    test_dir = Path("tools/java-dataset-converter-llm/dataset/test/java/")
    out_dir = Path("out/dataset/")

    sort_files(test_dir, out_dir)


if __name__ == "__main__":
    main()
