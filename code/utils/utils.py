from __future__ import annotations

import codecs
import logging

import multiprocessing as mp
import os
import shutil
from concurrent.futures import as_completed, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from typing import Any, List, Optional, Tuple

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
class ParseResult:
    ok: bool
    tree: Optional[Any] = None
    error: Optional[str] = None
    timed_out: bool = False


@dataclass
class JavaReason:
    line_count: int
    notes: List[str]
    size_reasons: List[str]
    simplification_goals: List[str]
    need_simplify: bool = False


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


def _parse_worker(code: str, q: mp.Queue) -> None:
    try:
        tree = javalang.parse.parse(code)
        q.put(("ok", tree))
    except Exception as e:
        q.put(("err", repr(e)))


def parse_with_timeout(code: str, timeout_s: float = 2.0) -> ParseResult:
    q: mp.Queue = mp.Queue(maxsize=1)
    p = mp.Process(target=_parse_worker, args=(code, q), daemon=True)
    p.start()
    p.join(timeout_s)

    if p.is_alive():
        p.terminate()
        p.join()
        return ParseResult(
            ok=False, timed_out=True, error=f"timeout after {timeout_s}s"
        )

    if q.empty():
        return ParseResult(
            ok=False, error="parse worker finished but no result returned"
        )

    status, payload = q.get()
    if status == "ok":
        return ParseResult(ok=True, tree=payload)
    return ParseResult(ok=False, error=payload)


def extract_identifier_candidates(wrapped_test_case: str) -> Tuple[List[str], bool]:
    res = parse_with_timeout(wrapped_test_case)

    if not res.ok:
        return [], False

    tree = res.tree

    class_decls = [
        t for t in tree.types if isinstance(t, javalang.tree.ClassDeclaration)
    ]
    if not class_decls:
        return [], True  # parsed, but no class in the snippet

    cls = class_decls[0]
    methods = list(cls.methods)
    if not methods:
        return [], True

    def is_test_annotation(ann) -> bool:
        return ann.name == "Test" or ann.name.endswith(".Test")

    if len(methods) == 1:
        test_method = methods[0]
    else:
        test_method = next(
            (
                m
                for m in methods
                if any(is_test_annotation(a) for a in getattr(m, "annotations", []))
            ),
            None,
        )
        if test_method is None:
            return [], True

    names: set[str] = set()

    for p in getattr(test_method, "parameters", []) or []:
        if getattr(p, "name", None):
            names.add(p.name)

    for _, var_decl in test_method.filter(javalang.tree.VariableDeclarator):
        if getattr(var_decl, "name", None):
            names.add(var_decl.name)

    def is_constant_like(name: str) -> bool:
        return name.isupper()

    return sorted(n for n in names if n and not is_constant_like(n)), True


def looks_stringified(text: str) -> bool:
    return '\\"' in text or "\\\\n" in text


def unescape_java_stringified_source(text: str) -> str:
    try:
        return codecs.decode(text, "unicode_escape")
    except Exception:
        return text


def classify_and_copy(
    file: Path, no_id_dir: Path, parse_fail_dir: Path, parsed_ok_dir: Path
) -> Tuple[Path, str]:
    """
    Returns (file, category) where category in {"parse_failed", "no_id", "parse_ok"}.
    """
    text = file.read_text(encoding="utf-8", errors="replace")

    if looks_stringified(text):
        text = unescape_java_stringified_source(text)

    candidates, parsed_ok = extract_identifier_candidates(text)    
    
    if not parsed_ok:
        if (parse_fail_dir / file.name).exists():
            return file, "parse_failed"
        shutil.copy2(file, parse_fail_dir / file.name)
        return file, "parse_failed"
    elif len(candidates) == 0:
        if (no_id_dir / file.name).exists():
            return file, "no_id"
        shutil.copy2(file, no_id_dir / file.name)
        return file, "no_id"
    else:
        if (parsed_ok_dir / file.name).exists():
            return file, "parse_ok"
        shutil.copy2(file, parsed_ok_dir / file.name)
        return file, "parse_ok"


def sort_identifiers_tests(input: Path, output: Path, workers: int | None = 2):
    files = [f for f in input.iterdir() if f.is_file()]
    output.mkdir(parents=True, exist_ok=True)

    no_id_dir = output / "no_id_tests"
    parse_fail_dir = output / "parse_failed"
    parsed_ok_dir = output / "parse_ok"

    no_id_dir.mkdir(exist_ok=True)
    parse_fail_dir.mkdir(exist_ok=True)
    parsed_ok_dir.mkdir(exist_ok=True)

    if workers is None:
        workers = os.cpu_count()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(classify_and_copy, f, no_id_dir, parse_fail_dir, parsed_ok_dir)
            for f in files
        ]

        for _ in tqdm(
            as_completed(futures), total=len(futures), desc="files", unit="file"
        ):
            _.result()


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
    # input_dir = Path("../tools/java-dataset-converter-llm/dataset/test/java_temp/")
    # out_dir = Path("../out/dataset/test/")

    # sort_identifiers_tests(input_dir, out_dir)
    
    # input_dir = Path("../tools/java-dataset-converter-llm/dataset/val/java_temp/")
    # out_dir = Path("../out/dataset/val/")

    # sort_identifiers_tests(input_dir, out_dir)
    
    input_dir = Path("../tools/java-dataset-converter-llm/dataset/train/java_temp/")
    out_dir = Path("../out/dataset/train/")

    sort_identifiers_tests(input_dir, out_dir)


if __name__ == "__main__":
    main()
