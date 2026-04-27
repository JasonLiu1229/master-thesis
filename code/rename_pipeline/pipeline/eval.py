import logging
import re
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
    r = requests.post(f"{CODEREADER_URL}/grade", json={"text": code}, timeout=1200)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"codereader request failed ({r.status_code}):\n{detail}")

    raw = r.json()["output"]
    lines = _llm_formatter(raw.splitlines(True))
    return _llm_parser(lines)


def _subtokenize(name: str) -> List[str]:
    """Split a camelCase/snake_case identifier into lowercase subtokens."""
    tokens = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").split()
    return [t.lower() for t in tokens if t]


def _align_identifier_pairs(
    obf_code: str,
    oracle_code: str,
    predicted_code: str,
    mapping: Optional[dict] = None,
) -> List[Tuple[str, str]]:
    """
    Align predicted and oracle identifier names to produce per-identifier
    (oracle_name, predicted_name) pairs for subtoken-level evaluation.

    When `mapping` is provided (obf_name -> predicted_name), it is used as the
    ground truth alignment — no token counting or inference needed. Each
    obfuscated identifier token is looked up in the oracle to get the expected
    name, and in the mapping to get the predicted name.

    Falls back to positional token alignment when mapping is not available.

    Returns a list of (oracle_name, predicted_name) pairs, one per identifier
    occurrence (duplicates included so frequency weighs into metrics).
    """
    if mapping is not None:
        try:
            obf_toks = list(jtok.tokenize(obf_code))
            oracle_toks = list(jtok.tokenize(oracle_code))
        except Exception as e:
            logger.warning(
                f"_align_identifier_pairs (mapping mode): tokenization failed: {e}"
            )
            return []

        if len(obf_toks) != len(oracle_toks):
            logger.warning(
                "_align_identifier_pairs (mapping mode): obf/oracle token counts differ "
                f"(obf={len(obf_toks)}, oracle={len(oracle_toks)}); "
                "falling back to positional alignment."
            )
        else:
            pairs = []
            for o_tok, r_tok in zip(obf_toks, oracle_toks):
                if isinstance(o_tok, jtok.Identifier):
                    obf_name = o_tok.value
                    oracle_name = r_tok.value
                    predicted_name = mapping.get(
                        obf_name, obf_name
                    )  # default to obf if not in mapping
                    pairs.append((oracle_name, predicted_name))
            return pairs

    try:
        obf_toks = list(jtok.tokenize(obf_code))
        oracle_toks = list(jtok.tokenize(oracle_code))
        pred_toks = list(jtok.tokenize(predicted_code))
    except Exception as e:
        logger.warning(f"_align_identifier_pairs: tokenization failed: {e}")
        return []

    if not (len(obf_toks) == len(oracle_toks) == len(pred_toks)):
        logger.warning(
            "_align_identifier_pairs: token counts differ "
            f"(obf={len(obf_toks)}, oracle={len(oracle_toks)}, pred={len(pred_toks)}); "
            "aligning identifier subsequences instead."
        )
        oracle_ids = [t.value for t in oracle_toks if isinstance(t, jtok.Identifier)]
        pred_ids = [t.value for t in pred_toks if isinstance(t, jtok.Identifier)]
        # Pad shorter side with "" so missing predictions score 0 rather than
        # being silently dropped from the metric
        max_len = max(len(oracle_ids), len(pred_ids))
        oracle_ids += [""] * (max_len - len(oracle_ids))
        pred_ids += [""] * (max_len - len(pred_ids))
        return list(zip(oracle_ids, pred_ids))

    pairs = []
    for o_tok, r_tok, p_tok in zip(obf_toks, oracle_toks, pred_toks):
        if isinstance(o_tok, jtok.Identifier):
            pairs.append((r_tok.value, p_tok.value))
    return pairs


def evaluate_f1(
    oracle: str,
    predicted: str,
    obf_code: Optional[str] = None,
    mapping: Optional[dict] = None,
) -> F1Metrics:
    """
    Compute subtoken-level F1 metrics.

    When `mapping` is provided (obf_name -> predicted_name), it is used directly
    for alignment — exact and immune to token count differences.

    When only `obf_code` is provided, alignment is done by positional token zip.

    Without either, falls back to positional alignment of identifier lists.
    """
    if obf_code is not None:
        pairs = _align_identifier_pairs(obf_code, oracle, predicted, mapping=mapping)
    else:
        oracle_ids = extract_identifiers(oracle)
        pred_ids = extract_identifiers(predicted)
        n = min(len(oracle_ids), len(pred_ids))
        pairs = [(oracle_ids[i], pred_ids[i]) for i in range(n)]

    if not pairs:
        return F1Metrics(
            cer=0.0,
            edit_distance=0.0,
            correct_ordered=0.0,
            correct_unordered=0.0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
        )

    total_tp = total_fp = total_fn = 0
    total_correct_pos = 0
    total_expected_subtokens = 0
    n_correct = 0
    total_edit = 0
    total_expected_chars = 0

    for oracle_name, pred_name in pairs:
        exp_subs = _subtokenize(oracle_name)
        pred_subs = _subtokenize(pred_name)

        exp_set = set(exp_subs)
        pred_set = set(pred_subs)
        tp = len(exp_set & pred_set)
        fp = len(pred_set - exp_set)
        fn = len(exp_set - pred_set)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        total_correct_pos += sum(1 for a, b in zip(exp_subs, pred_subs) if a == b)
        total_expected_subtokens += len(exp_subs)

        if exp_subs == pred_subs:
            n_correct += 1

        edit = levenshtein(oracle_name, pred_name)
        total_edit += edit
        total_expected_chars += max(1, len(oracle_name))

    n = len(pairs)
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    )
    correct_ordered = (
        total_correct_pos / total_expected_subtokens
        if total_expected_subtokens
        else 0.0
    )
    correct_unordered = n_correct / n
    cer = 100.0 * total_edit / total_expected_chars
    avg_edit = total_edit / n

    return F1Metrics(
        cer=cer,
        edit_distance=avg_edit,
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


def evaluate(
    oracle: str,
    predicted: str,
    obf_code: Optional[str] = None,
    mapping: Optional[dict] = None,
) -> PairMetrics:
    f1m = evaluate_f1(oracle, predicted, obf_code=obf_code, mapping=mapping)
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


def compute_final_metrics_with_oracle(
    metrics: List[PairMetrics],
    oracle_llm_metrics: Optional[List[LLMMetrics]] = None,
) -> Dict[str, float]:

    result = compute_final_metrics(metrics)

    if oracle_llm_metrics:
        n = len(oracle_llm_metrics)
        result["oracle_llm_score_avg"] = (
            sum(m.codereader_avg for m in oracle_llm_metrics) / n
        )
        result["oracle_llm_score_wavg"] = (
            sum(m.codereader_wavg for m in oracle_llm_metrics) / n
        )

    return result


def compute_cohens(
    f1_metrics: List[F1Metrics],
    llm_obf_metrics: List[LLMMetrics],
    llm_renamed_metrics: List[LLMMetrics],
    llm_oracle_metrics: Optional[List[LLMMetrics]] = None,
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

    # LLM: paired obfuscated vs renamed (did renaming improve readability?)
    if len(llm_obf_metrics) != len(llm_renamed_metrics):
        logger.error(
            "compute_cohens: LLM obf and renamed lists have different lengths "
            f"({len(llm_obf_metrics)} vs {len(llm_renamed_metrics)}). "
            "Skipping LLM obf-vs-renamed effect size."
        )
    elif llm_obf_metrics:
        results.append(
            compute_effect_size(
                scores_original=[m.codereader_avg for m in llm_obf_metrics],
                scores_renamed=[m.codereader_avg for m in llm_renamed_metrics],
                metric_name="llm_score_avg__obf_vs_renamed",
            )
        )
        results.append(
            compute_effect_size(
                scores_original=[m.codereader_wavg for m in llm_obf_metrics],
                scores_renamed=[m.codereader_wavg for m in llm_renamed_metrics],
                metric_name="llm_score_wavg__obf_vs_renamed",
            )
        )

    if llm_oracle_metrics is not None and llm_oracle_metrics:
        # renamed vs oracle: how close did we get to human-written quality?
        if len(llm_renamed_metrics) == len(llm_oracle_metrics):
            results.append(
                compute_effect_size(
                    scores_original=[m.codereader_avg for m in llm_renamed_metrics],
                    scores_renamed=[m.codereader_avg for m in llm_oracle_metrics],
                    metric_name="llm_score_avg__renamed_vs_oracle",
                )
            )
            results.append(
                compute_effect_size(
                    scores_original=[m.codereader_wavg for m in llm_renamed_metrics],
                    scores_renamed=[m.codereader_wavg for m in llm_oracle_metrics],
                    metric_name="llm_score_wavg__renamed_vs_oracle",
                )
            )
        else:
            logger.warning(
                "compute_cohens: renamed and oracle LLM lists have different lengths "
                f"({len(llm_renamed_metrics)} vs {len(llm_oracle_metrics)}). "
                "Skipping renamed-vs-oracle effect size."
            )

        # obf vs oracle: how unreadable was the starting point?
        if len(llm_obf_metrics) == len(llm_oracle_metrics):
            results.append(
                compute_effect_size(
                    scores_original=[m.codereader_avg for m in llm_obf_metrics],
                    scores_renamed=[m.codereader_avg for m in llm_oracle_metrics],
                    metric_name="llm_score_avg__obf_vs_oracle",
                )
            )
            results.append(
                compute_effect_size(
                    scores_original=[m.codereader_wavg for m in llm_obf_metrics],
                    scores_renamed=[m.codereader_wavg for m in llm_oracle_metrics],
                    metric_name="llm_score_wavg__obf_vs_oracle",
                )
            )
        else:
            logger.warning(
                "compute_cohens: obf and oracle LLM lists have different lengths "
                f"({len(llm_obf_metrics)} vs {len(llm_oracle_metrics)}). "
                "Skipping obf-vs-oracle effect size."
            )

    return effect_size_report([r for r in results if r is not None])
