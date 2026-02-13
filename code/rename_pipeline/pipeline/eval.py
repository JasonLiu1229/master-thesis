import subprocess

from dataclasses import dataclass
from typing import Dict, List

import javalang.tokenizer as jtok

import yaml

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)


@dataclass
class PairMetrics:
    cer: float
    edit_distance: float
    correct_ordered: float
    correct_unordered: float
    precision: float
    recall: float
    f1: float


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[-1][-1]


def extract_identifiers(java_code: str):
    try:
        tokens = list(jtok.tokenize(java_code))
        return [t.value for t in tokens if isinstance(t, jtok.Identifier)]
    except Exception:
        return []


def llm_readability_score(prediction: str):
    cmd = (
        f'codereader grade -c {config["CODEREADER_CONFIG_FILE"]} --text "{prediction}"'
    )

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    ) as p:
        assert p.stdout is not None
        ...


def evaluate(oracle: str, prediction: str):  # function partially made using GPT
    """
    Evaluate a single prediction against a single oracle.
    """

    edit = levenshtein(oracle, prediction)
    total_chars = max(1, len(oracle))
    cer = 100.0 * edit / total_chars

    oracle_ids = extract_identifiers(oracle)
    pred_ids = extract_identifiers(prediction)

    if oracle_ids:
        same_positions = sum(
            1
            for i in range(min(len(oracle_ids), len(pred_ids)))
            if oracle_ids[i] == pred_ids[i]
        )
        correct_ordered = same_positions / len(oracle_ids)
    else:
        correct_ordered = 0.0

    oracle_set = set(oracle_ids)
    pred_set = set(pred_ids)

    if oracle_set or pred_set:
        inter = len(oracle_set & pred_set)
        union = len(oracle_set | pred_set)
        correct_unordered = inter / union if union > 0 else 0.0
    else:
        correct_unordered = 0.0

    tp = len(oracle_set & pred_set)  # true positives
    fp = len(pred_set - oracle_set)  # false positives
    fn = len(oracle_set - pred_set)  # false negatives

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    )

    return PairMetrics(
        cer,
        float(edit),
        correct_ordered,
        correct_unordered,
        precision,
        recall,
        f1,
    )


def compute_final_metrics(metrics: List[PairMetrics]) -> Dict[str, float]:
    """
    Compute average metrics for a whole dataset.

    Returns a dict with:
      - cer
      - edit_distance
      - correct_ordered
      - correct_unordered
      - precision
      - recall
      - f1
    """
    if not metrics:
        return {
            "cer": 0.0,
            "edit_distance": 0.0,
            "correct_ordered": 0.0,
            "correct_unordered": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    n = len(metrics)

    sum_cer = sum(m.cer for m in metrics)
    sum_edit = sum(m.edit_distance for m in metrics)
    sum_co = sum(m.correct_ordered for m in metrics)
    sum_cu = sum(m.correct_unordered for m in metrics)
    sum_prec = sum(m.precision for m in metrics)
    sum_rec = sum(m.recall for m in metrics)
    sum_f1 = sum(m.f1 for m in metrics)

    return {
        "cer": sum_cer / n,
        "edit_distance": sum_edit / n,
        "correct_ordered": sum_co / n,
        "correct_unordered": sum_cu / n,
        "precision": sum_prec / n,
        "recall": sum_rec / n,
        "f1": sum_f1 / n,
    }
