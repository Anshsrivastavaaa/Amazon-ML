"""Helper utilities for metrics, seeding, logging and image downloading."""
import os
import random
import logging
import numpy as np
import torch
from pathlib import Path

def seed_everything(seed: int = 42) -> None:
    """Sets random seeds across Python, NumPy, and PyTorch for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_logger(name: str = "amazon_ml", log_file: Path | None = None) -> logging.Logger:
    """Sets up a standardized logger for console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def calculate_metrics(y_true, y_pred):
    """Placeholder evaluation metrics commonly used in competition scoring (F1, Accuracy, MAPE, etc.)."""
    from sklearn.metrics import f1_score, accuracy_score
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_micro": f1_score(y_true, y_pred, average="micro", zero_division=0)
    }
