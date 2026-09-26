"""Project Configuration for Business Entity Resolution Challenge 2026."""
from pathlib import Path

# ─── Base Directories ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
SUBMISSIONS_DIR = BASE_DIR / "submissions"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
for _dir in [
    RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR,
    SUBMISSIONS_DIR, NOTEBOOKS_DIR, OUTPUT_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)

# ─── Dataset Paths ──────────────────────────────────────────────────
# Training
TRAIN_DIR = RAW_DATA_DIR / "train"
TRAIN_SOURCE1 = TRAIN_DIR / "train_source1.tsv"
TRAIN_SOURCE2 = TRAIN_DIR / "train_source2.tsv"
TRAIN_SOURCE3 = TRAIN_DIR / "train_source3.tsv"
TRAIN_GROUND_TRUTH = TRAIN_DIR / "train_ground_truth.tsv"

# Test
TEST_DIR = RAW_DATA_DIR / "test"
TEST_SOURCE1 = TEST_DIR / "test_source1.tsv"
TEST_SOURCE2 = TEST_DIR / "test_source2.tsv"
TEST_SOURCE3 = TEST_DIR / "test_source3.tsv"

# ─── Output Files ───────────────────────────────────────────────────
MATCHING_RESULTS = OUTPUT_DIR / "matching_results.tsv"
CANDIDATE_PAIRS = OUTPUT_DIR / "candidate_pairs.tsv"

# ─── Reproducibility ────────────────────────────────────────────────
SEED = 42

# ─── Column Names ───────────────────────────────────────────────────
COL_ENTITY_ID = "entity_id"
COL_BUSINESS_NAME = "business_name"
COL_BUSINESS_ADDRESS = "business_address"
COL_COUNTRY = "country"
COL_SOURCE1_ID = "source1_entity_id"
COL_MATCHED_IDS = "matched_entity_ids"
COL_CANDIDATE_IDS = "candidate_entity_ids"
