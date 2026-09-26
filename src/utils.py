"""Helper utilities for Business Entity Resolution Challenge 2026."""
import os
import random
import logging
import numpy as np
import pandas as pd
from pathlib import Path


def seed_everything(seed: int = 42) -> None:
    """Sets random seeds across Python and NumPy for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)


def get_logger(name: str = "entity_resolution", log_file: Path | None = None) -> logging.Logger:
    """Sets up a standardized logger for console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


def load_tsv(filepath: Path) -> pd.DataFrame:
    """Load a TSV file into a DataFrame. Raises FileNotFoundError if missing."""
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    return pd.read_csv(filepath, sep="\t", dtype=str, keep_default_na=False)


def compute_f05(precision: float, recall: float) -> float:
    """
    Compute F0.5 score.

    F0.5 = (1.25 * Precision * Recall) / (0.25 * Precision + Recall)

    Gives more weight to precision than recall.
    """
    if precision + recall == 0:
        return 0.0
    return (1.25 * precision * recall) / (0.25 * precision + recall)
