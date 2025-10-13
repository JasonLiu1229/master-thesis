import re
import ast
from typing import Dict, Iterable

_KEY_MAP = {
    "Average amount of predicted subtokens": "avg_predicted_subtokens",
    "Average amount of expected subtokens": "avg_expected_subtokens",
    "Average amount of predicted subtokens in a correct prediction": "avg_predicted_subtokens_correct",
    "Average amount of predicted subtokens in an incorrect prediction": "avg_predicted_subtokens_incorrect",
    "Average amount of expected subtokens in an incorrect prediction": "avg_expected_subtokens_incorrect",
    "Average length of predicted names": "avg_len_predicted_names",
    "Average length of expected names": "avg_len_expected_names",
    "Average length of correct names": "avg_len_correct_names",
    "Distribution of expected lengths": "dist_expected_lengths",
    "Distribution of predicted lengths": "dist_predicted_lengths",
    "Precision": "precision",
    "Recall": "recall",
    "F1": "f1",
    "Correct ordered": "correct_ordered",
    "Correct unordered": "correct_unordered",
    "CER": "cer",
    "Edit distance": "edit_distance",
    "Execution time": "execution_time_s",
}

_LABELS_RE = re.compile(
    r"^(?P<label>"
    + "|".join(re.escape(k) for k in _KEY_MAP.keys())
    + r")\s*:\s*(?P<value>.+?)\s*$"
)

_NUM_RE = re.compile(
    r"^[+-]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?$"
)

_SEC_SUFFIX_RE = re.compile(r"^(?P<num>.+?)\s*(?:seconds?|s)\s*$", re.IGNORECASE)

def _parse_value(raw: str):
    """Parse a scalar float/int, a seconds-suffixed number, or a dict literal."""
    raw = raw.strip()

    ms = _SEC_SUFFIX_RE.match(raw)
    if ms:
        num = ms.group("num").replace(",", "")
        return float(num)

    if _NUM_RE.match(raw):
        return float(raw.replace(",", ""))

    if raw.startswith("{") and raw.endswith("}"):
        try:
            d = ast.literal_eval(raw)
            # ensure int keys (some logs may have stringified ints)
            return {int(k): int(v) for k, v in d.items()}
        except Exception:
            # fallthrough to raw
            pass

    # fallback to raw string
    return raw

def parse(lines: Iterable[str]) -> Dict[str, object]:
    """
    Parse the metrics block from t1 output lines.
    Returns a dict with canonical keys; missing keys are simply absent.
    """
    out: Dict[str, object] = {}
    for line in lines:
        m = _LABELS_RE.match(line)
        if not m:
            continue
        label = m.group("label")
        value_str = m.group("value")
        key = _KEY_MAP[label]
        out[key] = _parse_value(value_str)
    return out
