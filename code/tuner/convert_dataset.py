import json
import logging
import os
import re
import shutil
from logger import setup_logging

setup_logging("tuner_converter")
logger = logging.getLogger("tuner_converter")

OBF_RE = re.compile(r"\b(func_\d+|var_\d+)\b")


def _tokenize(code: str) -> list[str]:
    """
    Split Java source into a flat token list that preserves every character.
    Splits on word boundaries so that identifier tokens are isolated.
    """
    return re.findall(r"[A-Za-z_]\w*|[^\w\s]|\d+|\s+", code)


def extract_mapping(prompt: str, response: str) -> tuple[dict, list] | None:
    """
    Derive {obf_name: original_name} by aligning the token streams of the
    obfuscated prompt and the renamed response.

    Returns (mapping, identifiers) on success, or None when alignment fails.
    """
    p_toks = _tokenize(prompt)
    r_toks = _tokenize(response)

    if len(p_toks) != len(r_toks):
        return None

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
        return None

    identifiers = list(dict.fromkeys(OBF_RE.findall(prompt)))

    if not identifiers:
        return None

    missing = [i for i in identifiers if i not in mapping]
    if missing:
        for m in missing:
            mapping[m] = m

    return mapping, identifiers


def convert_file(input_path: str, output_path: str) -> tuple[int, int]:
    """Convert one .jsonl file. Returns (kept, skipped)."""
    kept = skipped = 0

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
                skipped += 1
                continue

            prompt = record.get("prompt", "")
            response = record.get("response", "")

            if not prompt or not response:
                logger.warning(
                    f"{input_path}:{line_idx} — missing prompt or response, skipping."
                )
                skipped += 1
                continue

            result = extract_mapping(prompt, response)
            if result is None:
                logger.warning(
                    f"{input_path}:{line_idx} — could not extract mapping "
                    f"(token mismatch or conflict), skipping."
                )
                skipped += 1
                continue

            mapping, identifiers = result

            new_record = {
                "obf_code": prompt,
                "mapping": mapping,
                "identifiers": identifiers,
            }
            fout.write(json.dumps(new_record, ensure_ascii=False) + "\n")
            kept += 1

    return kept, skipped


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

    total_kept = total_skipped = 0

    for i, filename in enumerate(sorted(jsonl_files), 1):
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)

        kept, skipped = convert_file(in_path, out_path)
        total_kept += kept
        total_skipped += skipped

        if i % 500 == 0 or i == 1:
            logger.info(
                f"[{i}/{len(jsonl_files)}] {filename} "
                f"kept={kept} skipped={skipped}"
            )

    logger.info(
        f"Conversion complete. "
        f"total_kept={total_kept}, total_skipped={total_skipped}, "
        f"files={len(jsonl_files)}"
    )
