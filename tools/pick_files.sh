#!/usr/bin/env bash
# Usage: ./pick_files.sh <source_dir> <target_dir> [indices_file]

set -euo pipefail

SOURCE_DIR="${1:?Usage: $0 <source_dir> <target_dir> [indices_file]}"
TARGET_DIR="${2:?Usage: $0 <source_dir> <target_dir> [indices_file]}"
INDICES_FILE="${3:-indices.txt}"

if [[ ! -f "$INDICES_FILE" ]]; then
  echo "Error: indices file '$INDICES_FILE' not found." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

found=0
missing=0

while IFS= read -r idx || [[ -n "$idx" ]]; do
  # Skip blank lines or comments
  [[ -z "$idx" || "$idx" == \#* ]] && continue

  filename="TestClass${idx}_java.jsonl"
  src="$SOURCE_DIR/$filename"

  if [[ -f "$src" ]]; then
    cp "$src" "$TARGET_DIR/$filename"
    echo "Copied: $filename"
    ((found++))
  else
    echo "Missing: $filename" >&2
    ((missing++))
  fi
done <"$INDICES_FILE"

echo ""
echo "Done — copied: $found, missing: $missing"
