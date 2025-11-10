import argparse
import logging
import os

import yaml

from data_preprocess import preprocess
from logger import setup_logging
from tuner import get_llm_model, tune

setup_logging("tuner")

logger = logging.getLogger("tuner")

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


def _preprocess_dataset(force: bool = False):
    llm_model = get_llm_model()
    
    os.makedirs(config["OUTPUT_DIR"], exist_ok=True)

    # train dataset
    logger.info("Preprocessing training dataset...")

    train_path = os.path.join(config["INPUT_DIR"], config["TRAIN_DIR"])
    train_output_path = os.path.join(config["OUTPUT_DIR"], config["TRAIN_DIR"])

    if os.path.exists(
        os.path.join(
            train_output_path,
        )
    ) and not force and os.listdir(train_output_path):
        logger.info(
            f"Preprocessed training dataset already exists at {train_output_path}/preprocessed__train. Skipping preprocessing."
        )
    else:
        preprocess(
            input_dir=train_path,
            output_dir=train_output_path,
            llm=llm_model,
            shuffle=True,
            seed=42,
        )

    # val dataset
    logger.info("Preprocessing validation dataset...")

    val_path = os.path.join(config["INPUT_DIR"], config["VAL_DIR"])
    val_output_path = os.path.join(config["OUTPUT_DIR"], config["VAL_DIR"])

    if os.path.exists(
        os.path.join(
            val_output_path,
        )
    ) and not force and os.listdir(val_output_path):
        logger.info(
            f"Preprocessed validation dataset already exists at {val_output_path}/preprocessed_val. Skipping preprocessing."
        )
    else:
        preprocess(
            input_dir=val_path,
            output_dir=val_output_path,
            llm=llm_model,
            shuffle=False,
            seed=42,
        )

    # test dataset
    logger.info("Preprocessing test dataset...")

    test_path = os.path.join(config["INPUT_DIR"], config["TEST_DIR"])
    test_output_path = os.path.join(config["OUTPUT_DIR"], config["TEST_DIR"])

    if os.path.exists(
        os.path.join(
            test_output_path,
        )
    ) and not force and os.listdir(test_output_path):
        logger.info(
            f"Preprocessed test dataset already exists at {test_output_path}/preprocessed_test. Skipping preprocessing."
        )
    else:
        preprocess(
            input_dir=test_path,
            output_dir=test_output_path,
            llm=llm_model,
            shuffle=False,
            seed=42,
        )


def tune_model():
    tune()


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Preprocess dataset and tune LLM model."
    )
    parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Preprocess the dataset.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force re-preprocessing even if processed data exists. Else skip if processed data exists.",
    )

    parser.add_argument(
        "--tune",
        action="store_true",
        help="Tune the LLM model.",
    )
    return parser


if __name__ == "__main__":
    parser = argument_parser()
    args = parser.parse_args()

    if args.preprocess:
        logging.info("Preprocessing dataset...")
        _preprocess_dataset(force=args.force)

    if args.tune:
        logging.info("Tuning model...")
        tune_model()
