import json
import logging
import os
import re
import shutil
from datetime import datetime
from enum import Enum
from logger import setup_logging

setup_logging("tuner_converter")
logger = logging.getLogger("tuner_converter")

OBF_RE = re.compile(r"\b(func_\d+|var_\d+)\b")


class SkipReason(Enum):
    NO_IDENTIFIERS = "no_obf_identifiers"
    TOKEN_MISMATCH = "token_mismatch"
    CONFLICT = "mapping_conflict"


def _get_skip_log_path(output_dir: str) -> str:
    """
    Generate a timestamped skip log file path inside output_dir.
    E.g. output_dir/skipped_20240317_143205.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(output_dir, f"skipped_{timestamp}.log")


def _tokenize(code: str) -> list[str]:
    """
    Split Java source into a flat token list that preserves every character.
    Splits on word boundaries so that identifier tokens are isolated.
    """
    return re.findall(r"[A-Za-z_$][\w$]*|[^\w\s$]|\d+|\s+", code)


def sanitize(code: str) -> str:
    code = code.replace("\\'", "'")
    code = code.replace('\\\\\\"', '\\"')
    code = code.replace('\\\\"', '\\"')
    code = code.replace("\r\n", "\n")
    code = code.replace("\0", "")
    return code


def extract_mapping(prompt: str, response: str) -> tuple[dict, list] | SkipReason:
    """
    Derive {obf_name: original_name} by aligning the token streams of the
    obfuscated prompt and the renamed response.

    Returns (mapping, identifiers) on success, or a SkipReason on failure.
    """
    prompt = sanitize(prompt)
    response = sanitize(response)

    p_toks = _tokenize(prompt)
    r_toks = _tokenize(response)

    if len(p_toks) != len(r_toks):
        return SkipReason.TOKEN_MISMATCH

    identifiers = list(dict.fromkeys(OBF_RE.findall(prompt)))
    if not identifiers:
        return SkipReason.NO_IDENTIFIERS

    mapping: dict[str, str] = {}
    conflicts: list[tuple] = []

    for pt, rt in zip(p_toks, r_toks):
        pt_s, rt_s = pt.strip(), rt.strip()
        if not OBF_RE.fullmatch(pt_s):
            continue
        if not rt_s or pt_s == rt_s:
            continue

        if pt_s not in mapping:
            mapping[pt_s] = rt_s
        elif mapping[pt_s] != rt_s:
            conflicts.append((pt_s, mapping[pt_s], rt_s))

    if conflicts:
        return SkipReason.CONFLICT

    for ident in identifiers:
        if ident not in mapping:
            mapping[ident] = ident

    return mapping, identifiers


def convert_file(
    input_path: str,
    output_path: str,
    skip_log_writer,
) -> tuple[int, int, dict]:
    """
    Convert one .jsonl file.
    Returns (kept, skipped, skip_counts) where skip_counts breaks down reasons.
    Writes each skipped record as a JSON line to skip_log_writer.
    """
    kept = 0
    skip_counts: dict[str, int] = {r.value: 0 for r in SkipReason}
    skip_counts["bad_json"] = 0
    skip_counts["missing_fields"] = 0

    filename = os.path.basename(input_path)

    with (
        open(input_path, "r", encoding="utf-8") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):
        for line_idx, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"{input_path}:{line_idx} — bad JSON: {e}")
                skip_counts["bad_json"] += 1
                _write_skip_entry(
                    skip_log_writer,
                    file=filename,
                    line=line_idx,
                    reason="bad_json",
                    detail=str(e),
                    prompt=None,
                )
                continue

            prompt = record.get("prompt", "")
            response = record.get("response", "")

            if not prompt or not response:
                logger.warning(
                    f"{input_path}:{line_idx} — missing prompt or response, skipping."
                )
                skip_counts["missing_fields"] += 1
                _write_skip_entry(
                    skip_log_writer,
                    file=filename,
                    line=line_idx,
                    reason="missing_fields",
                    detail="prompt or response is empty",
                    prompt=prompt or None,
                )
                continue

            result = extract_mapping(prompt, response)

            if isinstance(result, SkipReason):
                skip_counts[result.value] += 1

                if result == SkipReason.TOKEN_MISMATCH:
                    detail = (
                        f"prompt_tokens={len(_tokenize(prompt))}, "
                        f"response_tokens={len(_tokenize(response))}"
                    )
                    logger.warning(
                        f"{input_path}:{line_idx} — token count mismatch "
                        f"({detail}), skipping."
                    )
                elif result == SkipReason.CONFLICT:
                    detail = "same obf name maps to multiple targets"
                    logger.warning(
                        f"{input_path}:{line_idx} — mapping conflict ({detail}), skipping."
                    )
                else:
                    detail = "no obfuscated identifiers found"
                    logger.debug(f"{input_path}:{line_idx} — {detail}, skipping.")

                _write_skip_entry(
                    skip_log_writer,
                    file=filename,
                    line=line_idx,
                    reason=result.value,
                    detail=detail,
                    prompt=prompt,
                )
                continue

            mapping, identifiers = result

            new_record = {
                "obf_code": prompt,
                "mapping": mapping,
                "identifiers": identifiers,
            }
            fout.write(json.dumps(new_record, ensure_ascii=False) + "\n")
            kept += 1

    skipped = sum(skip_counts.values())
    return kept, skipped, skip_counts


def _write_skip_entry(
    writer,
    file: str,
    line: int,
    reason: str,
    detail: str,
    prompt: str | None,
) -> None:
    """Write a single skipped-record entry as a JSON line to the skip log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file": file,
        "line": line,
        "reason": reason,
        "detail": detail,
    }
    # Include a truncated snippet of the prompt to help with debugging,
    # but cap at 300 chars to keep the log readable.
    if prompt is not None:
        entry["prompt_snippet"] = prompt[:300] + ("..." if len(prompt) > 300 else "")
    writer.write(json.dumps(entry, ensure_ascii=False) + "\n")


def convert_dir(input_dir: str, output_dir: str) -> None:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if os.path.exists(output_dir):
        logger.warning(f"Output dir {output_dir!r} exists — overwriting.")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    jsonl_files = [f for f in os.listdir(input_dir) if f.endswith(".jsonl")]
    if not jsonl_files:
        raise RuntimeError(f"No .jsonl files found in {input_dir}")

    skip_log_path = _get_skip_log_path("out/logs/")
    logger.info(f"Skip log will be written to: {skip_log_path}")

    total_kept = 0
    total_skip_counts: dict[str, int] = {}

    with open(skip_log_path, "w", encoding="utf-8") as skip_log:
        for i, filename in enumerate(sorted(jsonl_files), 1):
            in_path = os.path.join(input_dir, filename)
            out_path = os.path.join(output_dir, filename)

            kept, skipped, skip_counts = convert_file(in_path, out_path, skip_log)
            total_kept += kept
            for reason, count in skip_counts.items():
                total_skip_counts[reason] = total_skip_counts.get(reason, 0) + count

            if i % 500 == 0 or i == 1:
                logger.info(
                    f"[{i}/{len(jsonl_files)}] {filename} "
                    f"kept={kept} skipped={skipped} breakdown={skip_counts}"
                )

    total_skipped = sum(total_skip_counts.values())
    logger.info(
        f"Conversion complete. "
        f"total_kept={total_kept}, total_skipped={total_skipped}, "
        f"files={len(jsonl_files)}, "
        f"skip_breakdown={total_skip_counts}, "
        f"skip_log={skip_log_path}"
    )
