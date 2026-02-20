import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import javalang.tokenizer as jtok
import requests

import yaml
from logger import setup_logging

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

CODEREADER_URL = "http://codereader_ollama:8080"

setup_logging("pipeline")
logger = logging.getLogger("pipeline")


@dataclass
class PairMetrics:
    cer: float
    edit_distance: float
    correct_ordered: float
    correct_unordered: float
    precision: float
    recall: float
    f1: float
    codereader_avg: float
    codereader_wavg: float


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


def _llm_formatter(stdout) -> Iterable[str]:
    for line in stdout:
        yield line


def _llm_parser(lines: Iterable[str]) -> Tuple[float, float]:
    avg = None
    wavg = None

    for line in lines:
        line = line.strip()

        if line.startswith("Average:"):
            avg = float(line.split(":", 1)[1].strip())

        elif line.startswith("Weighted average:"):
            wavg = float(line.split(":", 1)[1].strip())

    if avg is None or wavg is None:
        raise ValueError(
            f"Could not parse expected averages from output:\n{''.join(lines)}"
        )

    return avg, wavg


def llm_readability_score(prediction: str) -> Tuple[float, float]:
    r = requests.post(f"{CODEREADER_URL}/grade", json={"text": prediction}, timeout=120)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"codereader request failed ({r.status_code}):\n{detail}")

    raw = r.json()["output"]

    lines = _llm_formatter(raw.splitlines(True))
    return _llm_parser(lines)


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

    try:
        codereader_avg, codereader_wavg = llm_readability_score(prediction)
    except Exception as e:
        codereader_avg, codereader_wavg = 0, 0
        logger.error(f"Code not evaluated using codereader: {e}")

    return PairMetrics(
        cer,
        float(edit),
        correct_ordered,
        correct_unordered,
        precision,
        recall,
        f1,
        codereader_avg,
        codereader_wavg,
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
            "llm_score_avg": 0.0,
            "llm_score_wavg": 0.0,
        }

    n = len(metrics)

    sum_cer = sum(m.cer for m in metrics)
    sum_edit = sum(m.edit_distance for m in metrics)
    sum_co = sum(m.correct_ordered for m in metrics)
    sum_cu = sum(m.correct_unordered for m in metrics)
    sum_prec = sum(m.precision for m in metrics)
    sum_rec = sum(m.recall for m in metrics)
    sum_f1 = sum(m.f1 for m in metrics)
    sum_llm_avg = sum(m.codereader_avg for m in metrics)
    sum_llm_wavg = sum(m.codereader_wavg for m in metrics)

    return {
        "cer": sum_cer / n,
        "edit_distance": sum_edit / n,
        "correct_ordered": sum_co / n,
        "correct_unordered": sum_cu / n,
        "precision": sum_prec / n,
        "recall": sum_rec / n,
        "f1": sum_f1 / n,
        "llm_score_avg": sum_llm_avg / n,
        "llm_score_wavg": sum_llm_wavg / n,
    }
