from pathlib import Path
import json


INDICES = [
    280,
    1404,
    1493,
    1937,
    2032,
    3285,
    4815,
    5272,
    8235,
    9158,
    9239,
    9409,
    10820,
    10826,
    11306,
    11441,
    11553,
    12100,
    13046,
    13159,
    13270,
    14053,
    15201,
    16329,
    16795,
    18539,
    18794,
    21387,
    22297,
    22301,
    22631,
    24619,
    25504,
    25630,
    27206,
    27655,
    27991,
    28172,
    29714,
    29734,
    30027,
    30767,
    31291,
    31888,
    32356,
    32918,
    33576,
    33790,
    34889,
    35878,
    36753,
    37093,
    39058,
    40145,
    40807,
    41555,
    41560,
    42038,
    42353,
    44152,
    45720,
    46195,
    46322,
    46951,
    46973,
    47446,
    48751,
    50694,
    51164,
    53206,
    54038,
    55091,
    55807,
    60339,
    61563,
    61739,
    61839,
    62845,
    65594,
    65931,
    66990,
    67337,
    69357,
    69394,
    69842,
    70472,
    70680,
    71651,
    71980,
    72159,
    72263,
    73044,
    74087,
    74838,
    75101,
    75184,
    75731,
    75947,
    76709,
    77515,
]

SOURCE_DIR = Path("./out/dataset/fixed_copy/")
OUTPUT_DIR = Path("./out/dataset/test/fixed/")


def extract_java_files(
    indices: list[int],
    source_dir: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    found, missing, errors = 0, [], []

    for idx in indices:
        jsonl_name = f"TestClass{idx}.java.jsonl"
        src = source_dir / jsonl_name

        if not src.exists():
            missing.append(jsonl_name)
            continue

        try:
            with open(src, encoding="utf-8") as f:
                # Take the first non-empty line (files have one record)
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        break
                else:
                    errors.append((jsonl_name, "file is empty"))
                    continue

            prompt = data.get("prompt", "")
            if not prompt:
                errors.append((jsonl_name, "no 'prompt' key found"))
                continue

            # Unescape \n / \r\n so the saved file has real newlines
            prompt = prompt.replace("\\r\\n", "\n").replace("\\n", "\n")

            out_file = output_dir / f"TestClass{idx}.java"
            out_file.write_text(prompt, encoding="utf-8")
            found += 1

        except (json.JSONDecodeError, OSError) as e:
            errors.append((jsonl_name, str(e)))

    print(f"Extracted : {found}/{len(indices)} files → {output_dir}")

    if missing:
        print(f"Missing   : {len(missing)} .jsonl file(s)")
        for name in missing:
            print(f"  ✗ {name}")

    if errors:
        print(f"Errors    : {len(errors)} file(s)")
        for name, reason in errors:
            print(f"  ✗ {name} — {reason}")


if __name__ == "__main__":
    extract_java_files(INDICES, SOURCE_DIR, OUTPUT_DIR)
