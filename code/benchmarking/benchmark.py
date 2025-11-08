# Converts json output to a csv file for easier analysis
# Note the input files needs to be of the format <name>_benchmark_results.json
# This is to derive the name of the technique being benchmarked

import json
import csv
import os

INPUT_DIR = 'out/benchmark/'
OUTPUT_FILE = 'out/benchmark/benchmark.csv'

def main():
    assert os.path.exists(INPUT_DIR), f"Input directory '{INPUT_DIR}' does not exist."
    
    benchmark_data = {}
    
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith('.json'):
            continue
        
        technique_name = filename.replace('_benchmark_results.json', '')
        file_path = os.path.join(INPUT_DIR, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            benchmark_data[technique_name] = data
    
    
        
    with open(OUTPUT_FILE, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        if not benchmark_data:
            print("No benchmark data found in the input directory.")
            return
            
        headers = ['Technique'] + list(next(iter(benchmark_data.values())).keys())
        
        csv_writer.writerow(headers)
        
        for technique, results in benchmark_data.items():
            row = [technique]
            for key in headers[1:]:
                row.append(results.get(key, 'N/A'))
            csv_writer.writerow(row)
            
        print(f"Benchmark results have been written to '{OUTPUT_FILE}'")
    
if __name__ == '__main__':
    main()
