from dataclasses import dataclass
from pathlib import Path
from typing import List
import json

class JavaTestSpan: # A smaller form to save the test_cases
    name: str
    annotation_line: int 
    method_line: int
    start_line: int
    end_line: int
    file_path: str


def wrap_test_case(test_case: str) -> str:
    """
    Wrap the test case so it matches as similar as the original training data
    
    public class TestClassX {
        @Test
        public void func_1() { ... }
    }
    """
    pass
    
def _extract_tests_from_source(source_code: str, file_path: str) -> List[JavaTestSpan]:
    pass

def extract_tests_from_file(file_path: Path) -> List[JavaTestSpan]:
    assert file_path.exists(), f"File {file_path} does not exist"
    
    test_cases: List[JavaTestSpan] = list()

    with open(file_path, 'r') as file:
        test_cases = _extract_tests_from_source(file.read(), file_path)

    return test_cases

def parse_test_case(file_path: str, test_span: JavaTestSpan):
    pass

def combine_test_cases(test_cases: List[str]):
    """
    After the post processing of the test cases they need to be combined again to a single file
    """
    pass

if __name__ == '__main__':
    pass
