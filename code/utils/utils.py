import shutil
from pathlib import Path

from llm_client import LLMClient
from prompts import SIMPLFY_PROMPT, SIMPLFY_SYSTEM
from tqdm import tqdm

# File sizes in bytes -> medium is in between small and big
BIG = 50000
SMALL = 2000


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

    for file in tqdm(files, desc="JsonL files", unit="file"):
        size = check_size(file)
        if size >= BIG:
            shutil.copy(file, big_path / file.name)
        elif size >= SMALL:
            shutil.copy(file, medium_path / file.name)
        else:
            shutil.copy(file, small_path / file.name)


def simplify():
    pass


def main():
    test_dir = Path("tools/java-dataset-converter-llm/dataset/test/jsonl/")
    out_dir = Path("out/dataset/")

    sort_files(test_dir, out_dir)


if __name__ == "__main__":
    main()
