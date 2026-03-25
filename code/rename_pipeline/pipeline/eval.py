import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

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
class F1Metrics:
    cer: float
    edit_distance: float
    correct_ordered: float
    correct_unordered: float
    precision: float
    recall: float
    f1: float


@dataclass
class LLMMetrics:
    codereader_avg: float
    codereader_wavg: float


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


def extract_identifiers(java_code: str) -> List[str]:
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


def llm_readability_score(code: str) -> Tuple[float, float]:
    r = requests.post(f"{CODEREADER_URL}/grade", json={"text": code}, timeout=900)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"codereader request failed ({r.status_code}):\n{detail}")

    raw = r.json()["output"]
    lines = _llm_formatter(raw.splitlines(True))
    return _llm_parser(lines)


def evaluate_f1(oracle: str, predicted: str) -> F1Metrics:
    edit = levenshtein(oracle, predicted)
    total_chars = max(1, len(oracle))
    cer = 100.0 * edit / total_chars

    oracle_ids = extract_identifiers(oracle)
    pred_ids = extract_identifiers(predicted)

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

    tp = len(oracle_set & pred_set)
    fp = len(pred_set - oracle_set)
    fn = len(oracle_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    )

    return F1Metrics(
        cer=cer,
        edit_distance=float(edit),
        correct_ordered=correct_ordered,
        correct_unordered=correct_unordered,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def evaluate_llm(code: str) -> Optional[LLMMetrics]:
    try:
        avg, wavg = llm_readability_score(code)
        return LLMMetrics(codereader_avg=avg, codereader_wavg=wavg)
    except Exception as e:
        logger.error(f"LLM readability scoring failed: {e}")
        return None


def evaluate(oracle: str, predicted: str) -> PairMetrics:
    f1m = evaluate_f1(oracle, predicted)
    llm = evaluate_llm(predicted)

    return PairMetrics(
        cer=f1m.cer,
        edit_distance=f1m.edit_distance,
        correct_ordered=f1m.correct_ordered,
        correct_unordered=f1m.correct_unordered,
        precision=f1m.precision,
        recall=f1m.recall,
        f1=f1m.f1,
        codereader_avg=llm.codereader_avg if llm is not None else 0.0,
        codereader_wavg=llm.codereader_wavg if llm is not None else 0.0,
    )


def compute_final_metrics(metrics: List[PairMetrics]) -> Dict[str, float]:
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

    return {
        "cer": sum(m.cer for m in metrics) / n,
        "edit_distance": sum(m.edit_distance for m in metrics) / n,
        "correct_ordered": sum(m.correct_ordered for m in metrics) / n,
        "correct_unordered": sum(m.correct_unordered for m in metrics) / n,
        "precision": sum(m.precision for m in metrics) / n,
        "recall": sum(m.recall for m in metrics) / n,
        "f1": sum(m.f1 for m in metrics) / n,
        "llm_score_avg": sum(m.codereader_avg for m in metrics) / n,
        "llm_score_wavg": sum(m.codereader_wavg for m in metrics) / n,
    }


def compute_cohens(
    f1_metrics: List[F1Metrics],
    llm_obf_metrics: List[LLMMetrics],
    llm_renamed_metrics: List[LLMMetrics],
) -> dict:
    from pipeline.effect_size import compute_effect_size, effect_size_report

    results = []

    # F1: one-sample Wilcoxon (f1 scores vs zero)
    if f1_metrics:
        f1_scores = [m.f1 for m in f1_metrics]
        results.append(
            compute_effect_size(
                scores_original=[0.0] * len(f1_scores),
                scores_renamed=f1_scores,
                metric_name="f1_vs_zero_baseline",
            )
        )

    # LLM: paired obfuscated vs renamed
    if len(llm_obf_metrics) != len(llm_renamed_metrics):
        logger.error(
            "compute_cohens: LLM obf and renamed lists have different lengths "
            f"({len(llm_obf_metrics)} vs {len(llm_renamed_metrics)}). "
            "Skipping LLM effect size."
        )
    elif llm_obf_metrics:
        results.append(
            compute_effect_size(
                scores_original=[m.codereader_avg for m in llm_obf_metrics],
                scores_renamed=[m.codereader_avg for m in llm_renamed_metrics],
                metric_name="llm_score_avg",
            )
        )
        results.append(
            compute_effect_size(
                scores_original=[m.codereader_wavg for m in llm_obf_metrics],
                scores_renamed=[m.codereader_wavg for m in llm_renamed_metrics],
                metric_name="llm_score_wavg",
            )
        )

    return effect_size_report([r for r in results if r is not None])
