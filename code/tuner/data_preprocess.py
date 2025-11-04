import difflib
import json
import os
import random
from typing import Any, Dict, List, Tuple

import yaml
from datasets import Dataset, DatasetDict

from model import LLM_Model

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

PLAIN_PROMPT_TEMPLATE = (
    "### PROMPT: \n"
    "Please refactor the following Java unit test by renaming identifiers to be meaningful and self-explanatory. Do NOT change logic, literals, comments, formatting, assertions, or method call structure. Only improve identifier names (methods, variables). \n\n"
    "Obfuscated code:\n"
    "```java\n"
    "{obf}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else.\n"
)

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


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


# for instruct models
def build_chat_prompt(obf_code: str) -> str:
    user_msg = SYSTEM_INSTRUCTION + "\n\n" + USER_PROMPT_TEMPLATE.format(obf=obf_code)

    prompt = "[INST] " + user_msg + " [/INST]\n"

    return prompt


# for base model
def build_prompt_plain(obf_code: str) -> str:
    """
    Build a plain prompt for CodeLlama base (no chat formatting).
    """
    prompt = PLAIN_PROMPT_TEMPLATE.format(obf=obf_code)

    return prompt


# Note this part of the code is partially made with the help of GPT-4, this is because i did not understand the logic behind the tokenization and label creation fully.
def preprocess_single(
    obf_code: str, gt_code: str, max_length: int, tokenizer: AutoTokenizer
) -> Dict[str, Any]:

    bos = tokenizer.bos_token or "<s>"
    eos = tokenizer.eos_token or "</s>"

    prompt = build_prompt_plain(obf_code)
    response_prefix = "```java\n"
    response_suffix = "\n```" + eos

    response_base = "### RESPONSE:\n"

    full_text = (
        bos + prompt + response_base + response_prefix + gt_code + response_suffix
    )

    changed_spans_local = diff_spans(obf_code, gt_code)

    # for later we need a supervision window (because we want loss only on code part)
    gt_code_start = len(bos + prompt + response_base + response_prefix)
    gt_code_end = gt_code_start + len(gt_code)

    encoder = tokenizer(
        full_text,
        return_offsets_mapping=True,
        max_length=max_length,
        truncation=True,
        padding=False,
    )

    input_ids = encoder["input_ids"]  # This is what the model sees as input.
    attn_mask = encoder[
        "attention_mask"
    ]  # This is a binary mask (1 or 0) telling the model which tokens are real and which are padding.
    offsets = encoder[
        "offset_mapping"
    ]  # An offset mask (or offset mapping) is a list of pairs that record, for each token, the start and end character positions of that token in the original text string.

    labels = (
        []
    )  # This is the expected answer for each token in the sequence — basically a shifted copy of input_ids, except with some tokens masked to -100.

    # create labels (-100 for non-code parts, token ids for code parts that overlap with changed spans)
    for (start, end), idx in zip(offsets, input_ids):
        label_id = -100  # Default to -100 (to ignore in loss)

        if start >= gt_code_start and end <= gt_code_end:
            local_start = start - gt_code_start
            local_end = end - gt_code_start

            # keep only if label overlaps with changed spans
            for c_start, c_end in changed_spans_local:
                if spans_overlap((local_start, local_end), (c_start, c_end)):
                    label_id = idx
                    break

        labels.append(label_id)

    return {
        "input_ids": input_ids,
        "attention_mask": attn_mask,
        "labels": labels,
    }


def preprocess(
    input_dir: str,
    output_dir: str,
    llm: LLM_Model,
    shuffle: bool = True,
    name_suffix: str = "",
    seed: int = 42,
) -> Dataset | DatasetDict:
    assert os.path.exists(input_dir), f"Input directory {input_dir} does not exist."
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith(".jsonl")]
    assert files, f"No .jsonl files found in {input_dir}."

    if shuffle:
        random.Random(seed).shuffle(files)

    tokenizer = llm.get_tokenizer()
    max_len = config["MAX_LENGTH"]

    all_data: List[Dict[str, Any]] = []

    for file in files:
        input_path = os.path.join(input_dir, file)
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                obf_code = entry.get("prompt")
                gt_code = entry.get("response")
                if not obf_code or not gt_code:
                    continue
                feat = preprocess_single(obf_code, gt_code, max_len, tokenizer)

                if not all(
                    k in feat for k in ("input_ids", "attention_mask", "labels")
                ):
                    continue
                all_data.append(feat)

    assert all_data, "No valid examples found after preprocessing."

    ds = Dataset.from_list(all_data)
    ds = ds.remove_columns(
        [
            c
            for c in ds.column_names
            if c not in ("input_ids", "attention_mask", "labels")
        ]
    )
    ds.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

    out_dir = os.path.join(output_dir, f"preprocessed_{name_suffix}".rstrip("_"))
    ds.save_to_disk(out_dir)
    return ds
