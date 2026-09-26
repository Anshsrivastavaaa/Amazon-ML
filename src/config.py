"""Project Configuration for Amazon ML Challenge."""
from pathlib import Path
import torch

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
SUBMISSIONS_DIR = BASE_DIR / "submissions"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# Ensure directories exist
for path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, SUBMISSIONS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Training & Modeling Configuration
SEED = 42
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Default Model & Hyperparameters
BATCH_SIZE = 16
NUM_WORKERS = 2
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
EPOCHS = 5
MAX_SEQ_LENGTH = 256
IMAGE_SIZE = (224, 224)

# File names (Amazon ML challenge typical names)
TRAIN_CSV = RAW_DATA_DIR / "train.csv"
TEST_CSV = RAW_DATA_DIR / "test.csv"
SAMPLE_SUBMISSION_CSV = RAW_DATA_DIR / "sample_submission.csv"
FINAL_SUBMISSION_CSV = SUBMISSIONS_DIR / "submission.csv"
