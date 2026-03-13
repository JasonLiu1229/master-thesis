import csv
import os
from datetime import datetime
import yaml

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

USAGE_LOG_PATH = config["USAGE_LOG_PATH"]

_FIELDNAMES = [
    "timestamp",
    "file_path",
    "method_name",
    "new_method_name",
    "attempt",
    "call_type",           # rename | rename_retry | eval
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "latency_ms",
    "success",
]

_session: dict = {}


def _reset_session():
    global _session
    _session = {
        "calls":             0,
        "retries":           0,
        "failures":          0,
        "prompt_tokens":     0,
        "completion_tokens": 0,
        "total_tokens":      0,
        "total_latency_ms":  0.0,
    }


_reset_session()


def init():
    """Reset the usage CSV and in-memory counters at the start of a new run."""
    _reset_session()
    os.makedirs(os.path.dirname(USAGE_LOG_PATH), exist_ok=True)
    with open(USAGE_LOG_PATH, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=_FIELDNAMES).writeheader()


def record_llm_call(
    *,
    file_path: str,
    method_name: str,
    new_method_name:str,
    attempt: int,
    call_type: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    success: bool,
):
    total_tokens = prompt_tokens + completion_tokens

    os.makedirs(os.path.dirname(USAGE_LOG_PATH), exist_ok=True)
    if not os.path.exists(USAGE_LOG_PATH):
        with open(USAGE_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=_FIELDNAMES).writeheader()

    with open(USAGE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=_FIELDNAMES).writerow({
            "timestamp":         datetime.now().isoformat(timespec="seconds"),
            "file_path":         file_path or "",
            "method_name":       method_name or "",
            "new_method_name": new_method_name or "",
            "attempt":           attempt,
            "call_type":         call_type,
            "prompt_tokens":     prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens":      total_tokens,
            "latency_ms":        round(latency_ms, 1),
            "success":           success,
        })

    _session["calls"]             += 1
    _session["retries"]           += int(attempt > 1)
    _session["failures"]          += int(not success)
    _session["prompt_tokens"]     += prompt_tokens
    _session["completion_tokens"] += completion_tokens
    _session["total_tokens"]      += total_tokens
    _session["total_latency_ms"]  += latency_ms


def get_summary() -> dict:
    """
    Return a serialisable summary dict of the current session.
    Suitable for merging into the eval metrics JSON.
    """
    calls = max(_session["calls"], 1)

    return {
        "total_llm_calls":            _session["calls"],
        "total_retries":              _session["retries"],
        "total_failures":             _session["failures"],
        "retry_rate":                 round(_session["retries"] / calls, 4),
        "failure_rate":               round(_session["failures"] / calls, 4),

        "total_prompt_tokens":        _session["prompt_tokens"],
        "total_completion_tokens":    _session["completion_tokens"],
        "total_tokens":               _session["total_tokens"],
        "avg_prompt_tokens":          round(_session["prompt_tokens"] / calls, 1),
        "avg_completion_tokens":      round(_session["completion_tokens"] / calls, 1),
        "completion_to_prompt_ratio": round(
            _session["completion_tokens"] / max(_session["prompt_tokens"], 1), 4
        ),

        "avg_latency_ms":             round(_session["total_latency_ms"] / calls, 1),
        "total_latency_s":            round(_session["total_latency_ms"] / 1000, 2),
    }
