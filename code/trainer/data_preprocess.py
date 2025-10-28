import difflib
import json
import os
from typing import Dict, List, Tuple

import helper

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


def build_chat_prompt(obf_code: str) -> str:
    pass


def preprocess_file(input_file: str, output_file: str):
    """Preprocess dataset file to a standard format, easier for CodeLamma model to read and understand.

    The file will consist of tags to identify different sections of the code, this helps the tokenizer to better parse the input.

    Args:
        input_file (str): input jsonl file
        output_file (str): formatted jsonl file
    """
    assert os.path.exists(input_file), f"Input file {input_file} does not exist."
    assert input_file.endswith(".jsonl"), "Input file must be a .jsonl file."


def preprocess(input_dir: str, output_dir: str):
    assert os.path.exists(input_dir), f"Input directory {input_dir} does not exist."


if __name__ == "__main__":
    pass
