import argparse
import json
import logging
import os
import time
import random

from concurrent.futures import as_completed, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import yaml

from logger import setup_logging
from pipeline.eval import (
    compute_cohens,
    compute_final_metrics,
    evaluate,
    evaluate_f1,
    evaluate_llm,
    F1Metrics,
    LLMMetrics,
    PairMetrics,
)
from pipeline.helper import (
    extract_tests_from_file,
    post_process_eval,
    post_process_file,
)
from pipeline.renamer import rename, rename_eval
from pipeline.stats_tracker import init as sInit
from pipeline.usage_tracker import init as uInit

from tqdm import tqdm


setup_logging("pipeline")
logger = logging.getLogger("pipeline")

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

MODE = None
TIMESTAMP_RUN = datetime.now().strftime("%Y%m%d_%H%M%S")


def argument_parser():
    parser = argparse.ArgumentParser(description="Pipeline configuration")

    parser.add_argument(
        "--dir",
        help="Folder of files that will be fed into the pipeline. "
        "Valid only when mode is 'dir' or 'eval'. "
        "For 'eval', the directory must contain .jsonl files.",
        type=Path,
    )

    parser.add_argument(
        "--file",
        help="Single file that will be fed into the pipeline. "
        "Valid only when mode is 'single'.",
        type=Path,
    )

    parser.add_argument(
        "--mode",
        help="Different modes the pipeline can be set to",
        choices=["eval", "single", "dir"],
        required=True,
    )

    parser.add_argument(
        "--output",
        help="Directory where results/logs/output files should be written.",
        default="out",
        type=Path,
    )

    parser.add_argument(
        "--force",
        help="Overwrite existing output directory/files if they already exist.",
        action="store_true",
    )

    parser.add_argument(
        "--cohen",
        help=(
            "Compute Wilcoxon signed-rank effect sizes (rank-biserial r). "
            "Only valid with --mode eval. "
            "F1 is compared against a zero baseline (one-sample Wilcoxon) since "
            "obfuscated identifiers trivially score 0 against the oracle. "
            "LLM readability is a true paired comparison: the obfuscated code is "
            "scored alongside the renamed code for each test method. "
            "Results are embedded under 'effect_sizes' in the output JSON."
        ),
        action="store_true",
    )

    parser.add_argument("--version", action="version", version="Pipeline v1.0.0")

    return parser


def process_single(file: Path, out: Path, force: bool):
    test_cases_spans = extract_tests_from_file(file)

    test_cases = list()

    for test_span in tqdm(
        test_cases_spans,
        desc=f"Renaming tests in {file.name}",
        leave=False,
        unit="test",
    ):
        test_cases.append(rename(test_span))

    output_file = out / file.name

    with open(file, "r") as f:
        source_code = f.read()

    post_process_file(
        source_code=source_code,
        test_cases=test_cases,
        output_file=output_file,
        force=force,
    )

    logger.info(f"Renamed and outputed file: {file.name} to {output_file}")


def process_single_eval(
    file_path: Path,
    cohen: bool,
) -> Tuple[
    List[PairMetrics],
    List[F1Metrics],
    List[LLMMetrics],
    List[LLMMetrics],
    int,
    List[str],
]:

    logger.info(f"\nProcessing file: {file_path.name}")

    items = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    pair_metrics: List[PairMetrics] = []
    f1_metrics: List[F1Metrics] = []
    llm_obf_metrics: List[LLMMetrics] = []
    llm_renamed_metrics: List[LLMMetrics] = []
    failed_count = 0
    failed_files: List[str] = []

    for item in items:
        obf_code = item.get("prompt", "")
        oracle_code = item.get("response", "")

        if not obf_code or not oracle_code:
            logger.warning(
                f"One of the codes was missing to complete evaluation for that "
                f"oracle in file {file_path.name}"
            )
            continue

        predicted_code, clean, mapping = rename_eval(obf_code, file_path)

        if not clean:
            failed_count += 1
            failed_files.append(file_path.name)
            logger.warning(f"{file_path.name} added to the failed files")
            continue

        if cohen:
            f1_metrics.append(
                evaluate_f1(
                    oracle_code, predicted_code, obf_code=obf_code, mapping=mapping
                )
            )

            # LLM: obfuscated vs renamed  (did readability improve?)
            llm_obf = evaluate_llm(obf_code)
            llm_renamed = evaluate_llm(predicted_code)

            if llm_obf is not None and llm_renamed is not None:
                llm_obf_metrics.append(llm_obf)
                llm_renamed_metrics.append(llm_renamed)
            else:
                logger.warning(
                    f"Dropping LLM pair for one item in {file_path.name} "
                    "because one or both LLM scores failed."
                )
        else:
            pair_metrics.append(
                evaluate(
                    oracle_code, predicted_code, obf_code=obf_code, mapping=mapping
                )
            )

    return (
        pair_metrics,
        f1_metrics,
        llm_obf_metrics,
        llm_renamed_metrics,
        failed_count,
        failed_files,
    )


def process_folder(
    root: Path, out: Path, is_eval: bool, force: bool, cohen: bool = False
):
    out.mkdir(parents=True, exist_ok=True)

    workers = config["AMT_WORKERS"]
    if workers == -1:
        workers = os.cpu_count()

    if is_eval:
        logger.info(
            "Running evaluation" + (" with effect size (--cohen)" if cohen else "")
        )
        jsonl_files = list(root.glob("*.jsonl"))

        limit = len(jsonl_files)
        if config["AMOUNT_OF_EVAL_SAMPLES"] != -1:
            limit = config["AMOUNT_OF_EVAL_SAMPLES"]

        random.seed(config["SEED"])
        random.shuffle(jsonl_files)

        jsonl_files = jsonl_files[:limit]

        failed_count = 0
        total_pair_metrics: List[PairMetrics] = []
        total_f1_metrics: List[F1Metrics] = []
        total_llm_obf_metrics: List[LLMMetrics] = []
        total_llm_renamed_metrics: List[LLMMetrics] = []
        failed_files_all: List[str] = []

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_single_eval, file, cohen): file
                for file in jsonl_files
            }

            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Oracle files",
                unit="oracle",
            ):
                file = futures[fut]
                try:
                    (
                        pair_metrics,
                        f1_metrics,
                        llm_obf_metrics,
                        llm_renamed_metrics,
                        count,
                        failed_files,
                    ) = fut.result()
                except Exception as e:
                    logger.error(f"Error in eval for {file}: {e}")
                    continue

                total_pair_metrics.extend(pair_metrics)
                total_f1_metrics.extend(f1_metrics)
                total_llm_obf_metrics.extend(llm_obf_metrics)
                total_llm_renamed_metrics.extend(llm_renamed_metrics)
                failed_count += count
                failed_files_all.extend(failed_files)

        # Build final metrics from the right source depending on mode
        if cohen:
            combined = []
            llm_len = len(total_llm_renamed_metrics)
            for i, f1m in enumerate(total_f1_metrics):
                llm = total_llm_renamed_metrics[i] if i < llm_len else None
                combined.append(
                    PairMetrics(
                        cer=f1m.cer,
                        edit_distance=f1m.edit_distance,
                        correct_ordered=f1m.correct_ordered,
                        correct_unordered=f1m.correct_unordered,
                        precision=f1m.precision,
                        recall=f1m.recall,
                        f1=f1m.f1,
                        codereader_avg=llm.codereader_avg if llm else 0.0,
                        codereader_wavg=llm.codereader_wavg if llm else 0.0,
                    )
                )
            final_metric = compute_final_metrics(combined)
        else:
            final_metric = compute_final_metrics(total_pair_metrics)

        final_metric["fails"] = failed_count
        final_metric["total_time"] = time.time() - start_time
        final_metric["failed_files"] = sorted(set(failed_files_all))

        # Effect sizes
        if cohen:
            logger.info("Computing Wilcoxon signed-rank effect sizes...")
            effect_sizes = compute_cohens(
                f1_metrics=total_f1_metrics,
                llm_obf_metrics=total_llm_obf_metrics,
                llm_renamed_metrics=total_llm_renamed_metrics,
            )
            final_metric["effect_sizes"] = effect_sizes

            for metric_name, es in effect_sizes.items():
                logger.info(
                    f"[cohen] {metric_name}: "
                    f"r={es['effect_size_r']:.3f} ({es['effect_size_label']}), "
                    f"p={es['p_value']:.4f}, "
                    f"recommended_n={es['recommended_n']}"
                )

        post_process_eval(final_metric, force)
        logger.info("Folder evaluated")
        return

    java_files = sorted(root.glob("*.java"))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_single, file, out, force): file
            for file in java_files
        }

        for fut in tqdm(
            as_completed(futures), total=len(futures), desc="Files", unit="file"
        ):
            file = futures[fut]
            try:
                fut.result()
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")

    logger.info("Folder processed")


if __name__ == "__main__":
    args = argument_parser().parse_args()

    MODE = args.mode

    if args.cohen and MODE != "eval":
        raise ValueError("--cohen is only valid when --mode is 'eval'")

    sInit()
    uInit()

    if MODE == "single":
        logger.info("Processing single file")

        if not os.path.exists(args.file):
            logger.error(f"Path {args.file} does not exist")

        process_single(file=args.file, out=args.output, force=args.force)
    else:
        logger.info("Processing folder")

        if not os.path.exists(args.dir):
            logger.error(f"Path {args.dir} does not exist")

        process_folder(
            args.dir,
            out=args.output,
            is_eval=(MODE == "eval"),
            force=args.force,
            cohen=args.cohen,
        )
