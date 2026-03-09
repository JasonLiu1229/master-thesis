import csv
import os
from datetime import datetime


ERROR_LOG_PATH = "pipeline/errors.csv"

_FIELDNAMES = [
    "timestamp",
    "file_path",
    "attempt",
    "error_type",
    "error_message",
    "raw_response",
]

def init():
    """Reset the error log at the start of a new run."""
    os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)
    with open(ERROR_LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()
        
def _ensure_header():
    """Write the CSV header if the file doesn't exist yet."""
    if not os.path.exists(ERROR_LOG_PATH):
        os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)
        with open(ERROR_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
            writer.writeheader()


def log_error(
    file_path: str,
    attempt: int,
    error_type: str,
    error_message: str,
    raw_response: str = "",
):
    """
    Append one error event to the CSV log.

    Args:
        file_path:     The Java file being processed (java_test_span.file_path).
        method_name:   The test method name, or empty string if extraction failed.
        attempt:       The loop index i (0-based) from the retry loop.
        error_type:    Short label, e.g. 'JSONDecodeError', 'MissingKeys', 'NotADict'.
        error_message: Full error detail string.
        raw_response:  The raw LLM output that caused the error (optional).
    """
    _ensure_header()
    with open(ERROR_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "file_path": file_path,
                "attempt": attempt,
                "error_type": error_type,
                "error_message": error_message,
                "raw_response": raw_response,
            }
        )
