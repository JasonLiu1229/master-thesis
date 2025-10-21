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
}

# Note regex are made using GPT
_LABELS_RE = re.compile(
    r"^(?P<label>" + "|".join(re.escape(k) for k in LABELS.keys()) + r")\s*:\s*(?P<value>.+?)\s*$"
)

_NUM_RE = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?$")

def _to_float(s: str) -> float:
    return float(s.replace(",", "").strip())

def parse(lines: Iterable[str]) -> Dict[str, float]:
    """
    Parse T2 metrics from given output lines.
    Returns a dict with canonical keys; missing keys are simply absent.
    """
    out: Dict[str, float] = {}
    for line in lines:
        m = _LABELS_RE.match(line)
        if not m:
            continue
        label = m.group("label")
        value = m.group("value").strip()
        if _NUM_RE.match(value):
            out[LABELS[label]] = _to_float(value)
        else:
            continue
    return out
