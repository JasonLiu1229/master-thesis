from datasets import Dataset

import json
import os

def get_files(dir_path: str):
    """Get all files in the specified directory."""
    return [os.path.join(dir_path, f) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

def read_jsonl_files(file_paths: list) -> list:
    """Read multiple JSONL files and return a list of dictionaries."""
    data = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_path}: {e}")
    return data

def create_dataset_from_jsonl(dir_path: str) -> Dataset:
    """Create a Hugging Face Dataset from JSONL files in the specified directory."""
    file_paths = get_files(dir_path)
    jsonl_files = [f for f in file_paths if f.endswith('.jsonl')]
    
    if not jsonl_files:
        raise ValueError("No JSONL files found in the specified directory.")
    
    data = read_jsonl_files(jsonl_files)
    
    if not data:
        raise ValueError("No data found in the JSONL files.")
    
    return Dataset.from_list(data)
