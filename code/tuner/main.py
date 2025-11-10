import argparse

import yaml
import logging
import os

from data_preprocess import preprocess
from tuner import get_llm_model, tune

logger = logging.getLogger('tuner')

os.makedirs('out/logs/', exist_ok=True)

if not os.path.exists('out/logs/tuner.log'):
    with open('out/logs/tuner.log', 'w'):
        pass

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="out/logs/tuner.log",
    encoding="utf-8",
    level=logging.INFO,
)

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


def _preprocess_dataset():
    llm_model = get_llm_model()

    # train dataset
    logger.info("Preprocessing training dataset...")
    
    train_path = os.path.join(config["INPUT_DIR"], config["TRAIN_DIR"])
    train_output_path = os.path.join(config["OUTPUT_DIR"], config["TRAIN_DIR"])

    preprocess(
        input_dir=train_path,
        output_dir=train_output_path,
        llm=llm_model,
        shuffle=True,
        name_suffix="_train",
        seed=42,
    )

    # val dataset
    logger.info("Preprocessing validation dataset...")
    
    val_path = os.path.join(config["INPUT_DIR"], config["VAL_DIR"])
    val_output_path = os.path.join(config["OUTPUT_DIR"], config["VAL_DIR"])

    preprocess(
        input_dir=val_path,
        output_dir=val_output_path,
        llm=llm_model,
        shuffle=False,
        name_suffix="_val",
        seed=42,
    )

    # test dataset
    logger.info("Preprocessing test dataset...")
    
    test_path = os.path.join(config["INPUT_DIR"], config["TEST_DIR"])
    test_output_path = os.path.join(config["OUTPUT_DIR"], config["TEST_DIR"])

    preprocess(
        input_dir=test_path,
        output_dir=test_output_path,
        llm=llm_model,
        shuffle=False,
        name_suffix="_test",
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
        _preprocess_dataset()

    if args.tune:
        logging.info("Tuning model...")
        tune_model()
