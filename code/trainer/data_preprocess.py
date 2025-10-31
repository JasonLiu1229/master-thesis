import difflib
import json
import os
from typing import Dict, List, Tuple

from helper import save_dataset_dict, load_dataset_dict

import yaml
from datasets import Dataset
from transformers import AutoTokenizer

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do NOT change logic, literals, comments, formatting, assertions, or method call structure.\n"
    "Only improve identifier names (methods, variables)."
)

USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated test:\n\n"
    "```java\n"
    "{obf}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else."
)


def diff_spans(obf: str, gt: str) -> List[Tuple[int, int]]:
    """checks the difference between obfuscated code and ground truth code and a list of tuples of where to where it is located

    Args:
        obf (str): obfuscated code
        gt (str): ground truth

    Returns:
        List[Tuple[int, int]]: list of indexes from where to where it is located (start, end)
    """
    sm = difflib.SequenceMatcher(a=obf, b=gt, autojunk=False)
    spans = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag in ("replace", "insert", "delete"):
            spans.append((b0, b1))
    return spans


def spans_overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """check for overlap between two spans
    Args:
        span1 (Tuple[int, int]): first span
        span2 (Tuple[int, int]): second span
    Returns:
        bool: whether they overlap
    """
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])


def build_chat_prompt(obf_code: str) -> str:
    pass


def preprocess_single(obf_code:str, gt_code:str, max_length:int, tokenizer: AutoTokenizer):
    pass

def preprocess(input_dir: str, output_dir: str):
    assert os.path.exists(input_dir), f"Input directory {input_dir} does not exist."
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


if __name__ == "__main__":
    pass
