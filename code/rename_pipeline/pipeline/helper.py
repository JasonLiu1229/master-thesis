from dataclasses import dataclass
from pathlib import Path
from typing import List
import re
import os

METHOD_SIG_RE = re.compile(
    r"\b(?:public|protected|private)?\s*"
    r"(?:static\s+)?\s*"
    r"void\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"\(",
)


@dataclass
class JavaTestSpan:  # A smaller form to save the test_cases
    name: str
    annotation_line: int
    method_line: int
    start_line: int
    end_line: int
    file_path: str


def convert_json_to_java(json_file):
    """
    For jsonl files that contain java code, this needs to be converted to a valid java format for testing/eval function
    """
    pass


def wrap_test_case(test_case: str) -> str:
    """
    Wrap the test case so it matches as similar as the original training data

    public class TestClassX {
        @Test
        public void func_1() { ... }
    }
    """
    lines = test_case.splitlines()

    wrapped = []
    wrapped.append("public class TestClass1 {")
    wrapped.extend(lines)
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
                    or sig_line.startswith("@")
                ):
                    j += 1
                    continue

                m = METHOD_SIG_RE.search(sig_line)

                if m:
                    method_name = m.group("name")
                    method_line = j
                    break

                j += 1

            brace_count = 0
            found_open = False
            k = end_line = method_line

            while k < n:
                for ch in lines[k]:
                    if ch == "{":
                        brace_count += 1
                        found_open = True
                    elif ch == "}":
                        brace_count -= 1
                if brace_count == 0 and found_open:
                    end_line == k
                    break
                k += 1

            else:
                # unbalanced count of braces
                end_line = n - 1

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
    assert file_path.exists(), f"File {file_path} does not exist"

    test_spans: List[JavaTestSpan] = list()

    with open(file_path, "r") as file:
        test_spans = _extract_tests_from_source(file.read(), file_path)

    return test_spans


def parse_test_case(test_span: JavaTestSpan):
    assert os.path.exists(test_span.file_path), f"{test_span.file_path} does not exists"

    with open(test_span.file_path, "r") as f:
        source_code = f.read()
        return source_code[test_span.start_line : test_span.end_line + 1]


def combine_test_cases(test_cases: List[str]):
    """
    After the post processing of the test cases they need to be combined again to a single file
    """
    pass


if __name__ == "__main__":
    spans = extract_tests_from_file("assets/randoop_example_unit_test.java")
    print(wrap_test_case(parse_test_case(spans[0])))
