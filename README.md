# Business Entity Resolution Challenge 2026

End-to-end entity resolution pipeline that matches business records across three
independent data sources (Source 1, Source 2, Source 3) by resolving noisy names,
addresses, and other attributes.

## Project Structure

```
Amazon-ML-Challenge/
├── data/
│   ├── raw/
│   │   ├── train/              # Training TSVs
│   │   │   ├── train_source1.tsv
│   │   │   ├── train_source2.tsv
│   │   │   ├── train_source3.tsv
│   │   │   └── train_ground_truth.tsv
│   │   └── test/               # Test TSVs
│   │       ├── test_source1.tsv
│   │       ├── test_source2.tsv
│   │       └── test_source3.tsv
│   └── processed/              # Normalized / intermediate data
├── models/                     # Saved model artifacts
├── notebooks/                  # EDA and experimentation notebooks
├── output/                     # Final submission files
│   ├── matching_results.tsv
│   └── candidate_pairs.tsv
├── src/                        # Source code modules
│   ├── config.py               # Paths, constants, column names
│   └── utils.py                # Shared helpers (load_tsv, F0.5, logging)
├── submissions/                # Packaged submission ZIPs
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate       # Windows
   source venv/bin/activate      # Linux / macOS
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Place competition data** into `data/raw/train/` and `data/raw/test/`.

## Pipeline Overview

```
Source Data → Normalize → Block/Candidate Generation → Feature Engineering
    → ML Matching Model → Threshold → Entity-Level Resolution → Output
```

## Evaluation

The competition uses **F₀.₅**, which weights precision more heavily than recall.
False merges are especially costly.
