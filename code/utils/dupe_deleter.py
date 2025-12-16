# GPT generated, not really needed but it was for files that appeared in multiple folders (idk why though)

import os
from pathlib import Path
from collections import defaultdict

# CHANGE THESE PATHS
BASE_DIR = Path("../out/dataset/train")

PRIORITY_DIRS = [
    BASE_DIR / "parse_ok",
    BASE_DIR / "no_id_tests",
    BASE_DIR / "parse_failed",
]

def list_files(base: Path):
    result = []
    for root, _, files in os.walk(base):
        for f in files:
            full = Path(root) / f
            rel = full.relative_to(base)
            result.append((rel, full))
    return result


# Map: relative_path -> list of (priority_index, full_path)
files_map = defaultdict(list)

for priority, folder in enumerate(PRIORITY_DIRS):
    for rel, full in list_files(folder):
        files_map[rel].append((priority, full))


deleted = 0

for rel, entries in files_map.items():
    if len(entries) > 1:
        # keep the one with highest priority (lowest index)
        entries.sort(key=lambda x: x[0])
        keep = entries[0][1]

        for _, path in entries[1:]:
            path.unlink()
            deleted += 1
            print(f"Deleted duplicate: {path} (kept {keep})")

print(f"\nTotal duplicates removed: {deleted}")
