import logging
import os
import sys


def setup_logging(name: str = "log", log_level = logging.INFO):
    os.makedirs("out/logs", exist_ok=True)

    if not os.path.exists(f"out/logs/{name}.log"):
        with open(f"out/logs/{name}.log", "w"):
            pass

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(f"out/logs/{name}.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    def _excepthook(exc_type, exc, tb):
        logging.critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _excepthook
