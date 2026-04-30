import re
from typing import Dict, Iterable

LABELS = {
    "cor_ordered": "correct_ordered",
    "cor_unordered": "correct_unordered",
    "cer": "cer",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "edit": "edit_distance",
    "Correct ordered": "correct_ordered",
    "Correct unordered": "correct_unordered",
    "CER": "cer",
    "Precision": "precision",
    "Recall": "recall",
    "F1": "f1",
    "Edit distance": "edit_distance",
    "Execution time": "execution_time_s",
    "LLM score avg": "llm_score_avg",
    "LLM score wavg": "llm_score_wavg",
}

# Note regex are made using GPT
_LABELS_RE = re.compile(
    r"^(?P<label>"
    + "|".join(re.escape(k) for k in LABELS.keys())
    + r")\s*:\s*(?P<value>.+?)\s*$"
)

_NUM_RE = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?$")

_SEC_SUFFIX_RE = re.compile(r"^(?P<num>.+?)\s*(?:seconds?|s)\s*$", re.IGNORECASE)


def _parse_value(raw: str):
    raw = raw.strip()
    ms = _SEC_SUFFIX_RE.match(raw)
    if ms:
        return float(ms.group("num").replace(",", ""))
    if _NUM_RE.match(raw):
        return float(raw.replace(",", ""))
    return raw


def parse(lines: Iterable[str]) -> Dict[str, object]:
    """
    Parse T2 metrics from given output lines.
    Returns a dict with canonical keys; missing keys are simply absent.

    """
    out: Dict[str, object] = {}
    for line in lines:
        m = _LABELS_RE.match(line)
        if not m:
            continue
        label = m.group("label")
        value = m.group("value").strip()
        parsed = _parse_value(value)
        if isinstance(parsed, (int, float)):
            out[LABELS[label]] = parsed
    return out
