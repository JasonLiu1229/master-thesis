import difflib
import json
import logging
import os
import re

from dataclasses import dataclass
from pathlib import Path
from typing import List

import javalang
import javalang.tokenizer as jtok
import yaml
from colorama import Fore, init, Style
from logger import setup_logging

METHOD_SIG_RE = re.compile(
    r"\b(?:public|protected|private)?\s*"
    r"(?:static\s+)?\s*"
    r"void\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"\(",
)

init(autoreset=True)

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

setup_logging("pipeline")
logger = logging.getLogger("pipeline")


@dataclass
class JavaTestSpan:  # A smaller form to save the test_cases
    name: str
    annotation_line: int
    method_line: int
    start_line: int
    end_line: int
    file_path: Path


@dataclass
class JavaTestCase:
    name: str  # Just for debugging purposes
    original_code: str
    code: str
    clean: bool = True


# === Preprocess helper functions ===
def wrap_test_case(test_case: str) -> str:
    """
    Wrap the test case so it matches as similar as the original training data

    public class TestClassX {
        @Test
        public void func_1() { ... }
    }
    """
    wrapped = []
    wrapped.append("public class TestClass1 {")
    wrapped.extend(test_case)
    wrapped.append("}")
    return "\n".join(wrapped)


def _extract_tests_from_source(source_code: str, file_path: str) -> List[JavaTestSpan]:
    lines = source_code.splitlines()

    i = 0
    n = len(lines)

    test_spans: List[JavaTestSpan] = list()

    while i < n:
        line = lines[i].strip()

        if "@Test" in line:
            annotation_line = i

            method_name = None
            method_line = None

            j = i
            while j < n:
                sig_line = lines[j].strip()

                if (
                    sig_line == ""
                    or sig_line.startswith("//")
                    or sig_line.startswith("/*")
                    or sig_line.endswith("*/")
                ):
                    j += 1
                    continue

                m = METHOD_SIG_RE.search(sig_line)

                if m:
                    method_name = m.group("name")
                    method_line = j
                    break

                if sig_line.startswith("@"):
                    j += 1
                    continue

                j += 1

            brace_count = 0
            found_open = False
            end_line = method_line

            k = method_line
            while k < n:
                for ch in lines[k]:
                    if ch == "{":
                        brace_count += 1
                        found_open = True
                    elif ch == "}":
                        brace_count -= 1
                if brace_count == 0 and found_open:
                    end_line = k
                    break
                k += 1

            else:
                # unbalanced count of braces
                end_line = n - 1

            # print(f"{method_name} starts at {annotation_line + 1} ands end at {end_line}")
            test_spans.append(
                JavaTestSpan(
                    name=method_name,
                    annotation_line=annotation_line,
                    method_line=method_line,
                    start_line=annotation_line,
                    end_line=end_line,
                    file_path=file_path,
                )
            )

            i = end_line + 1
            continue

        i += 1

    return test_spans


def extract_tests_from_file(file_path: Path) -> List[JavaTestSpan]:
    assert os.path.exists(file_path), f"File {file_path} does not exist"

    test_spans: List[JavaTestSpan] = list()

    with open(file_path, "r") as file:
        test_spans = _extract_tests_from_source(file.read(), file_path)

    return test_spans


def parse_test_case(test_span: JavaTestSpan):
    assert os.path.exists(test_span.file_path), f"{test_span.file_path} does not exists"

    with open(test_span.file_path, "r") as f:
        source_code = f.read()
        source_code = source_code.splitlines()
        return source_code[test_span.start_line : test_span.end_line + 1]


def pre_process_file(file_path: Path) -> List[str]:

    spans = extract_tests_from_file(file_path=file_path)

    pre_processed_tests: List[str] = []
    for span in spans:
        pre_processed_tests.append(wrap_test_case(parse_test_case(span)))

    return pre_processed_tests


def _normalize_java_tokens(code: str):  # Made using GPT
    """
    Tokenize Java code and normalize identifiers to placeholders (ID0, ID1, ...).
    Non-identifier tokens keep their exact value.
    The resulting sequence can be compared between original and transformed code
    to see if only identifiers changed.
    """
    tokens = list(jtok.tokenize(code))
    id_map = {}
    next_id = 0
    normalized = []

    for tok in tokens:
        ttype = type(tok).__name__

        if isinstance(tok, jtok.Identifier):
            name = tok.value
            if name not in id_map:
                id_map[name] = f"ID{next_id}"
                next_id += 1
            normalized.append((ttype, id_map[name]))
        else:
            normalized.append((ttype, tok.value))

    return normalized


def only_identifier_renames(original: str, transformed: str) -> bool:  # Made using GPT
    """
    Return True if the only differences between original and transformed code
    are identifier renamings (variable/method/class names).

    If tokenization fails or structural tokens differ, return False.
    """
    try:
        orig_norm = _normalize_java_tokens(original)
        new_norm = _normalize_java_tokens(transformed)
    except jtok.LexerError:
        return False

    return orig_norm == new_norm


def log_colored_diff(
    logger, original_name: str, attempt: int, original_code: str, candidate_code: str
) -> None:  # made using GPT
    logger.warning(
        Fore.YELLOW
        + f"The new test case has logic changes: {original_name} (attempt {attempt})"
        + Style.RESET_ALL
    )

    orig_lines = original_code.splitlines()
    cand_lines = candidate_code.splitlines()

    diff = difflib.unified_diff(
        orig_lines, cand_lines, fromfile="original", tofile="candidate", lineterm=""
    )

    colored_lines = []
    for line in diff:
        if line.startswith("@@"):
            colored_lines.append(Fore.MAGENTA + line + Style.RESET_ALL)
        elif line.startswith("+") and not line.startswith("+++"):
            colored_lines.append(Fore.GREEN + line + Style.RESET_ALL)
        elif line.startswith("-") and not line.startswith("---"):
            colored_lines.append(Fore.RED + line + Style.RESET_ALL)
        else:
            colored_lines.append(line)

    if colored_lines:
        logger.warning("\n" + "\n".join(colored_lines))
    else:
        logger.warning(
            Fore.CYAN
            + "No textual diff produced, dumping both versions:"
            + Style.RESET_ALL
        )
        logger.warning(
            Fore.CYAN + "\n--- candidate ---\n" + candidate_code + Style.RESET_ALL
        )
        logger.warning(
            Fore.MAGENTA + "\n--- original ---\n" + original_code + Style.RESET_ALL
        )


def extract_identifier_candidates(wrapped_test_case: str) -> list[str]:
    """
    Given a wrapped Java test case,
    return the list of identifier names we want the LLM to rename.

    We include:
      - test method name
      - parameter names
      - local variable names (only from the top-level test method)

    We exclude:
      - ALL_CAPS-style names (likely constants)
    """
    try:
        tree = javalang.parse.parse(wrapped_test_case)
    except Exception as e:
        logger.warning(
            f"extract_identifier_candidates: javalang parse failed, "
            f"no candidates extracted. Error: {e}"
        )
        return []

    class_decls = [
        t for t in tree.types if isinstance(t, javalang.tree.ClassDeclaration)
    ]
    
    if not class_decls:
        logger.error(
            "extract_identifier_candidates: no ClassDeclaration found in wrapped test case."
        )
        return []

    cls = class_decls[0]
    methods = list(cls.methods)

    if not methods:
        logger.error("extract_identifier_candidates: no methods found in TestClass1.")
        return []

    test_method = None
    if len(methods) == 1:
        test_method = methods[0]
    else:
        for m in methods:
            if getattr(m, "annotations", None):
                for ann in m.annotations:
                    if ann.name == "Test":
                        test_method = m
                        break
            if test_method is not None:
                break

    if test_method is None:
        logger.warning(
            "extract_identifier_candidates: multiple methods in TestClass1, "
            "but none annotated with @Test; using first method."
        )
        test_method = methods[0]

    names: set[str] = set()

    if test_method.name:
        names.add(test_method.name)

    for param in test_method.parameters:
        names.add(param.name)

    for _, var_decl in test_method.filter(javalang.tree.VariableDeclarator):
        names.add(var_decl.name)

    def is_constant_like(name: str) -> bool:
        return name.isupper()

    candidates = sorted(n for n in names if not is_constant_like(n))
    return candidates


def apply_rename_mapping(code: str, mapping: dict[str, str]) -> str:
    """
    Apply a rename mapping to Java code by replacing ONLY identifier tokens,
    leaving literals, comments, qualifiers, etc. untouched.

    Uses javalang.tokenizer to locate identifier positions and patches the
    original source string at those positions.
    """
    if not mapping:
        return code

    try:
        tokens = list(jtok.tokenize(code))
    except jtok.LexerError as e:
        logger.error(
            f"apply_rename_mapping: failed to tokenize code due to LexerError; "
            f"leaving code unchanged. Error: {e}"
        )
        return code

    # Precompute line start offsets to convert (line, col) -> absolute index
    lines = code.splitlines(keepends=True)
    line_offsets: list[int] = []
    offset = 0
    for line in lines:
        line_offsets.append(offset)
        offset += len(line)

    replacements: list[tuple[int, str, str]] = []

    for tok in tokens:
        if isinstance(tok, jtok.Identifier) and tok.value in mapping:
            line, col = tok.position
            abs_index = line_offsets[line - 1] + (col - 1)
            old = tok.value
            new = mapping[old]
            if old != new:
                replacements.append((abs_index, old, new))

    new_code = code
    for idx, old, new in sorted(replacements, key=lambda x: x[0], reverse=True):
        if new_code[idx : idx + len(old)] != old:
            logger.warning(
                f"Expected {old!r} at index {idx}, "
                f"found {new_code[idx:idx+len(old)]!r}; skipping this replacement."
            )
            continue
        new_code = new_code[:idx] + new + new_code[idx + len(old) :]

    return new_code


# def build_identifier_context_snippets(
#     wrapped_test_case: str,
#     identifier_candidates: list[str],
#     window: int = 2,
# ) -> dict[str, str]:
#     lines = wrapped_test_case.splitlines()
#     n = len(lines)
    
#     contexts: dict[str, str] = {}

#     for name in identifier_candidates:
#         first_idx = None
#         pattern = re.compile(rf"\b{name}\b")
#         for i, line in enumerate(lines):
#             if pattern.search(line):
#                 first_idx = i
#                 break

#         if first_idx is None:
#             continue

#         start = max(0, first_idx - window)
#         end = min(n, first_idx + window + 1)
#         snippet = "\n".join(lines[start:end])
#         contexts[name] = snippet

#     return contexts

# === Post process functions ===
def remove_wrap(code: str):
    pattern = (
        r"@Test(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+[A-Za-z_][A-Za-z0-9_]*\s*"  # method name
        r"\([^)]*\)\s*"
        r"(?:throws [A-Za-z0-9_.,\s]+)?\s*"
        r"\{[\s\S]*?\}"
    )

    m = re.search(pattern, code)
    return m.group(0) if m else ""


def _swap_test_case(source_code: str, new_test_case: JavaTestCase) -> str:
    """
    Replace the original test case with the new one in the given Java source.
    """
    old = new_test_case.original_code
    new = new_test_case.code

    old = old.strip()
    new = new.strip()

    if not new:
        logger.warning(
            f"New test code for {new_test_case.name!r} is empty; refusing to replace."
        )
        return source_code

    # logger.info(f"new source code: {new}, to be replaced: {old}")

    if old not in source_code:
        raise ValueError(
            f"Original test case for {new_test_case.name!r} not found in source_code"
        )

    return source_code.replace(old, new, 1)


def post_process_file(
    source_code: str, test_cases: List[JavaTestCase], output_file: Path, force=False
):
    """
    Replace all the old test cases with the newly generated ones and make file at the end
    """

    for test_case in test_cases:
        if test_case.clean:
            source_code = _swap_test_case(source_code, test_case)

    if os.path.exists(output_file):
        if force:
            logger.warning(f"Force enabled, overwriting file: {output_file}")
        else:
            raise FileExistsError(
                f"{output_file} already exists and force was not enabled"
            )
    else:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        f.write(source_code)

METHOD_NAME_FROM_TEST_RE = re.compile(
    r"""
    @Test                
    (?:\s*\([^)]*\))?    
    [^{;]*?              
    \bvoid\s+            
    (?P<name>[A-Za-z_][A-Za-z0-9_]*)  
    \s*\(                
    """,
    re.DOTALL | re.VERBOSE,
)

def parse_method_name(test_case: str) -> str:
    header_part = test_case
    brace_idx = test_case.find("{")
    if brace_idx != -1:
        header_part = test_case[: brace_idx + 200]

    m = METHOD_NAME_FROM_TEST_RE.search(header_part)
    if m:
        return m.group("name")

    m2 = re.search(
        r"\bvoid\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        header_part,
    )
    if m2:
        logger.warning(
            "parse_method_name: falling back to simple 'void name(' pattern."
        )
        return m2.group(1)

    raise ValueError("parse_method_name: Could not find test method name")


def strip_markdown_fences(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return code


def post_process_eval(metrics: dict, out: Path, force=False):
    output_file: Path = out.joinpath(config["EVAL_OUTPUT_FILE_NAME"])

    if os.path.exists(output_file):
        if force:
            logger.warning(f"Force enabled, overwriting file: {output_file}")
        else:
            raise FileExistsError(
                f"{output_file} already exists and force was not enabled"
            )
    else:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)

    logger.info(f"Evaluated metrics and outputed to: {output_file}")


if __name__ == "__main__":
    spans = extract_tests_from_file(
        "code/rename_pipeline/pipeline/assets/randoop_example_unit_test_calc.java"
    )

    source_code = None
    with open(
        "code/rename_pipeline/pipeline/assets/randoop_example_unit_test_calc.java", "r"
    ) as file:
        source_code = file.read()

    print(f"Original source code: \n\n {source_code}")

    test_to_replace = parse_test_case(spans[1])
    test_to_replace = "\n".join(test_to_replace)

    new_test = (
        "@Test public void calculator_test() throws Throwable {"
        "Calculator calc = new Calculator();"
        "int result = calc.multiply(4, 0);"
        "assertEquals(0, result);"
        "}"
    )

    print(
        f"New source code: \n\n{_swap_test_case(source_code, JavaTestCase("calculator_test", test_to_replace, new_test))}"
    )
