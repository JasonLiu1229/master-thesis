#!/bin/sh
set -e

echo "=== Step 1: Converting raw dataset ==="
python3 -c "
from convert_dataset import convert_dir
convert_dir('in/raw/train', 'in/train')
convert_dir('in/raw/val',   'in/val')
convert_dir('in/raw/test',  'in/test')
"

echo "=== Step 2: Preprocessing dataset ==="
python3 main.py --preprocess
