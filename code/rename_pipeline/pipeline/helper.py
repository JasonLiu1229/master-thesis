from dataclasses import dataclass
from pathlib import Path
from typing import List
import json

def _wrap_test_case(test_case: str) -> str:
    """
    Wrap the test case so it matches as similar as the original training data
    
    public class TestClassX {
        @Test
        public void func_1() { ... }
    }
    """
    pass

def _extract_tests_from_source(source_code: str) -> List[str]:
    pass

def extract_tests_from_file(file_path: Path) -> List[str]:
    pass

def combine_test_cases(test_cases: List[str]):
    """
    After the post processing of the test cases they need to be combined again to a single file
    """
    pass
