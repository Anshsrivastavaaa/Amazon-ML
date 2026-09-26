"""
Part 1 — Data Ingestion & Understanding
========================================
Complete EDA script for the Business Entity Resolution Challenge 2026.

Usage:
    python src/part1_eda.py

Outputs:
    Prints a comprehensive analysis of all source files and ground truth.
"""

import sys
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np

# ── Project imports ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (
    TRAIN_SOURCE1, TRAIN_SOURCE2, TRAIN_SOURCE3, TRAIN_GROUND_TRUTH,
    TEST_SOURCE1, TEST_SOURCE2, TEST_SOURCE3,
    COL_ENTITY_ID, COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS, COL_COUNTRY,
    COL_SOURCE1_ID, COL_MATCHED_IDS,
)
from src.utils import load_tsv, get_logger

logger = get_logger("part1_eda")


# ─────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def inspect_source(df: pd.DataFrame, label: str) -> None:
    """Task B & E: Full schema + quality inspection for a source file."""
    section(f"SOURCE INSPECTION: {label}")

    # Basic shape
    print(f"Rows:    {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes.to_string()}")

    # Unique IDs
    n_unique_ids = df[COL_ENTITY_ID].nunique()
    n_duplicate_ids = len(df) - n_unique_ids
    print(f"\nUnique entity_ids: {n_unique_ids:,}")
    print(f"Duplicate entity_ids: {n_duplicate_ids:,}")
    if n_duplicate_ids > 0:
        dups = df[df.duplicated(subset=[COL_ENTITY_ID], keep=False)]
        print(f"  ⚠ Duplicate IDs sample:\n{dups.head(10).to_string()}")

    # ID prefix check (Task C)
    prefixes = df[COL_ENTITY_ID].str.split("-", n=1).str[0].value_counts()
    print(f"\nID prefixes:\n{prefixes.to_string()}")

    # Missing / empty values (Task E)
    subsection("Missing & Empty Values")
    for col in df.columns:
        n_null = df[col].isna().sum()
        n_empty = (df[col].astype(str).str.strip() == "").sum()
        print(f"  {col:25s}  null={n_null:,}  empty_string={n_empty:,}")

    # Country distribution (Task E)
    if COL_COUNTRY in df.columns:
        subsection("Country Distribution")
        country_counts = df[COL_COUNTRY].value_counts(dropna=False)
        print(country_counts.to_string())

    # Field length statistics (Task E)
    subsection("Field Length Statistics")
    for col in [COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS]:
        if col in df.columns:
            lengths = df[col].astype(str).str.len()
            print(f"\n  {col}:")
            print(f"    min={lengths.min()}  max={lengths.max()}  "
                  f"mean={lengths.mean():.1f}  median={lengths.median():.0f}")
            # Very short
            n_very_short = (lengths <= 2).sum()
            if n_very_short > 0:
                print(f"    ⚠ Very short (≤2 chars): {n_very_short:,}")
                print(f"      Samples: {df.loc[lengths <= 2, col].head(5).tolist()}")
            # Very long
            n_very_long = (lengths > 200).sum()
            if n_very_long > 0:
                print(f"    ⚠ Very long (>200 chars): {n_very_long:,}")
                print(f"      Samples: {df.loc[lengths > 200, col].head(3).tolist()}")

    # Duplicate names/addresses (Task E)
    subsection("Duplicate Field Values")
    if COL_BUSINESS_NAME in df.columns:
        dup_names = df[COL_BUSINESS_NAME].value_counts()
        n_dup_names = (dup_names > 1).sum()
        print(f"  Duplicate business_name values: {n_dup_names:,}")
        if n_dup_names > 0:
            print(f"  Top repeated names:\n{dup_names.head(10).to_string()}")
    if COL_BUSINESS_ADDRESS in df.columns:
        dup_addrs = df[COL_BUSINESS_ADDRESS].value_counts()
        n_dup_addrs = (dup_addrs > 1).sum()
        print(f"\n  Duplicate business_address values: {n_dup_addrs:,}")
        if n_dup_addrs > 0:
            print(f"  Top repeated addresses:\n{dup_addrs.head(10).to_string()}")

    # Unusual characters (Task E)
    subsection("Character Analysis")
    for col in [COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS]:
        if col in df.columns:
            all_chars = set("".join(df[col].astype(str).tolist()))
            non_ascii = {c for c in all_chars if ord(c) > 127}
            if non_ascii:
                print(f"  {col}: {len(non_ascii)} non-ASCII characters found")
                # Show a sample
                sample_chars = list(non_ascii)[:30]
                print(f"    Sample: {sample_chars}")
            else:
                print(f"  {col}: ASCII only")

    # Sample records
    subsection("Sample Records (first 5)")
    print(df.head(5).to_string())
    subsection("Sample Records (last 5)")
    print(df.tail(5).to_string())


def inspect_ground_truth(gt: pd.DataFrame, s1: pd.DataFrame,
                          s2: pd.DataFrame, s3: pd.DataFrame) -> None:
    """Task D: Deep ground-truth analysis."""
    section("GROUND TRUTH ANALYSIS")

    print(f"Rows: {len(gt):,}")
    print(f"Columns: {list(gt.columns)}")

    # Parse matched IDs
    gt = gt.copy()
    gt["match_list"] = gt[COL_MATCHED_IDS].apply(
        lambda x: [m.strip() for m in str(x).split(",") if m.strip()] if pd.notna(x) and str(x).strip() else []
    )
    gt["match_count"] = gt["match_list"].apply(len)

    # Match count distribution
    subsection("Match Count Distribution")
    count_dist = gt["match_count"].value_counts().sort_index()
    print(count_dist.to_string())

    n_zero = (gt["match_count"] == 0).sum()
    n_one = (gt["match_count"] == 1).sum()
    n_many = (gt["match_count"] > 1).sum()
    total = len(gt)
    print(f"\nZero matches (singletons): {n_zero:,} ({100*n_zero/total:.1f}%)")
    print(f"Exactly one match:        {n_one:,} ({100*n_one/total:.1f}%)")
    print(f"Multiple matches:         {n_many:,} ({100*n_many/total:.1f}%)")

    # S2 vs S3 breakdown
    subsection("Source Breakdown in Matches")
    all_matched = [mid for lst in gt["match_list"] for mid in lst]
    s2_matches = [m for m in all_matched if m.startswith("S2")]
    s3_matches = [m for m in all_matched if m.startswith("S3")]
    other_matches = [m for m in all_matched if not m.startswith("S2") and not m.startswith("S3")]

    print(f"Total matched IDs: {len(all_matched):,}")
    print(f"  S2 matches:      {len(s2_matches):,}")
    print(f"  S3 matches:      {len(s3_matches):,}")
    if other_matches:
        print(f"  ⚠ OTHER matches: {len(other_matches):,}  →  {other_matches[:10]}")

    # How many S1 match S2 only, S3 only, or both
    gt["has_s2"] = gt["match_list"].apply(lambda lst: any(m.startswith("S2") for m in lst))
    gt["has_s3"] = gt["match_list"].apply(lambda lst: any(m.startswith("S3") for m in lst))

    has_matches = gt[gt["match_count"] > 0]
    s2_only = ((has_matches["has_s2"]) & (~has_matches["has_s3"])).sum()
    s3_only = ((~has_matches["has_s2"]) & (has_matches["has_s3"])).sum()
    both = ((has_matches["has_s2"]) & (has_matches["has_s3"])).sum()

    print(f"\nS1 entities with matches: {len(has_matches):,}")
    print(f"  S2 only:  {s2_only:,}")
    print(f"  S3 only:  {s3_only:,}")
    print(f"  Both:     {both:,}")

    # Uniqueness of matched IDs
    subsection("Matched ID Uniqueness")
    matched_id_counts = Counter(all_matched)
    n_unique_matched = len(matched_id_counts)
    n_reused = sum(1 for v in matched_id_counts.values() if v > 1)
    print(f"Unique matched IDs: {n_unique_matched:,}")
    print(f"Matched IDs appearing in >1 S1 entity: {n_reused:,}")
    if n_reused > 0:
        reused = {k: v for k, v in matched_id_counts.items() if v > 1}
        print(f"  ⚠ Samples: {dict(list(reused.items())[:10])}")

    # Verify all S1 IDs in ground truth exist in source1
    subsection("Ground Truth ↔ Source 1 Consistency")
    gt_s1_ids = set(gt[COL_SOURCE1_ID])
    s1_ids = set(s1[COL_ENTITY_ID])
    missing_from_s1 = gt_s1_ids - s1_ids
    extra_in_s1 = s1_ids - gt_s1_ids
    print(f"S1 IDs in ground truth: {len(gt_s1_ids):,}")
    print(f"S1 IDs in source1 file: {len(s1_ids):,}")
    print(f"In GT but not in S1:    {len(missing_from_s1):,}")
    print(f"In S1 but not in GT:    {len(extra_in_s1):,}")

    # Verify matched IDs exist in S2/S3
    subsection("Matched IDs ↔ Source 2/3 Consistency")
    s2_ids = set(s2[COL_ENTITY_ID])
    s3_ids = set(s3[COL_ENTITY_ID])
    s2_match_set = set(s2_matches)
    s3_match_set = set(s3_matches)

    missing_s2 = s2_match_set - s2_ids
    missing_s3 = s3_match_set - s3_ids
    print(f"S2 matched IDs not in source2: {len(missing_s2):,}")
    print(f"S3 matched IDs not in source3: {len(missing_s3):,}")
    if missing_s2:
        print(f"  ⚠ Missing S2 samples: {list(missing_s2)[:5]}")
    if missing_s3:
        print(f"  ⚠ Missing S3 samples: {list(missing_s3)[:5]}")

    # Country-level match patterns (Task F)
    subsection("Match Patterns by Country")
    gt_with_country = gt.merge(
        s1[[COL_ENTITY_ID, COL_COUNTRY]],
        left_on=COL_SOURCE1_ID, right_on=COL_ENTITY_ID, how="left"
    )
    for country, grp in gt_with_country.groupby(COL_COUNTRY):
        total_c = len(grp)
        zero_c = (grp["match_count"] == 0).sum()
        one_c = (grp["match_count"] == 1).sum()
        many_c = (grp["match_count"] > 1).sum()
        avg_matches = grp["match_count"].mean()
        print(f"\n  Country: {country}")
        print(f"    Total S1 entities:  {total_c:,}")
        print(f"    Zero matches:       {zero_c:,} ({100*zero_c/total_c:.1f}%)")
        print(f"    One match:          {one_c:,} ({100*one_c/total_c:.1f}%)")
        print(f"    Multiple matches:   {many_c:,} ({100*many_c/total_c:.1f}%)")
        print(f"    Avg match count:    {avg_matches:.2f}")


def cross_source_analysis(s1: pd.DataFrame, s2: pd.DataFrame,
                           s3: pd.DataFrame, split: str) -> None:
    """Task F: Cross-source structural analysis."""
    section(f"CROSS-SOURCE ANALYSIS ({split})")

    subsection("Row Counts")
    print(f"  Source 1: {len(s1):,}")
    print(f"  Source 2: {len(s2):,}")
    print(f"  Source 3: {len(s3):,}")

    subsection("Country Overlap")
    c1 = set(s1[COL_COUNTRY].unique())
    c2 = set(s2[COL_COUNTRY].unique())
    c3 = set(s3[COL_COUNTRY].unique())
    print(f"  S1 countries: {sorted(c1)}")
    print(f"  S2 countries: {sorted(c2)}")
    print(f"  S3 countries: {sorted(c3)}")
    print(f"  Union:        {sorted(c1 | c2 | c3)}")
    print(f"  Intersection: {sorted(c1 & c2 & c3)}")

    subsection("Country × Source Counts")
    for src, label in [(s1, "S1"), (s2, "S2"), (s3, "S3")]:
        counts = src[COL_COUNTRY].value_counts()
        print(f"\n  {label}:")
        for country, n in counts.items():
            print(f"    {country}: {n:,}")


def test_vs_train_comparison(train_sources: dict, test_sources: dict) -> None:
    """Compare train and test distributions to spot domain shift."""
    section("TRAIN vs TEST COMPARISON")

    for src_name in ["S1", "S2", "S3"]:
        tr = train_sources[src_name]
        te = test_sources[src_name]
        subsection(f"Source {src_name}")
        print(f"  Train rows: {len(tr):,}")
        print(f"  Test rows:  {len(te):,}")

        # Country comparison
        tr_countries = set(tr[COL_COUNTRY].unique())
        te_countries = set(te[COL_COUNTRY].unique())
        new_countries = te_countries - tr_countries
        print(f"  Train countries: {sorted(tr_countries)}")
        print(f"  Test countries:  {sorted(te_countries)}")
        if new_countries:
            print(f"  ⚠ NEW countries in test: {sorted(new_countries)}")

        # Name length comparison
        tr_nlen = tr[COL_BUSINESS_NAME].str.len().describe()
        te_nlen = te[COL_BUSINESS_NAME].str.len().describe()
        print(f"  Name length — Train: mean={tr_nlen['mean']:.1f}, "
              f"Test: mean={te_nlen['mean']:.1f}")

        # Address length comparison
        tr_alen = tr[COL_BUSINESS_ADDRESS].str.len().describe()
        te_alen = te[COL_BUSINESS_ADDRESS].str.len().describe()
        print(f"  Addr length — Train: mean={tr_alen['mean']:.1f}, "
              f"Test: mean={te_alen['mean']:.1f}")


def validation_design_notes(gt: pd.DataFrame, s1: pd.DataFrame) -> None:
    """Task G: Print validation strategy considerations."""
    section("VALIDATION STRATEGY CONSIDERATIONS")

    gt = gt.copy()
    gt_with_country = gt.merge(
        s1[[COL_ENTITY_ID, COL_COUNTRY]],
        left_on=COL_SOURCE1_ID, right_on=COL_ENTITY_ID, how="left"
    )

    countries = gt_with_country[COL_COUNTRY].unique()
    print(f"Training countries: {sorted(countries)}")
    for c in sorted(countries):
        n = (gt_with_country[COL_COUNTRY] == c).sum()
        print(f"  {c}: {n:,} S1 entities")

    print("""
DESIGN NOTES:
  1. Split should be at the S1-entity level (not pair level) to avoid leakage.
  2. Stratify by country to ensure representation.
  3. Stratify by match_count bucket (0, 1, 2+) to preserve distribution.
  4. Consider 80/20 or 5-fold CV.
  5. The blocking stage must be re-applied to the validation fold independently
     (do NOT leak candidate pairs from training into validation).
  6. France appears only in test → our model must generalize to unseen countries.
     This means country should be a feature, NOT a hard filter.
""")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    section("PART 1 — DATA INGESTION & UNDERSTANDING")
    print("Business Entity Resolution Challenge 2026")
    print("=" * 80)

    # ── Task A: Dataset inventory ────────────────────────────────────
    section("TASK A: DATASET INVENTORY")
    files = {
        "train_source1": TRAIN_SOURCE1,
        "train_source2": TRAIN_SOURCE2,
        "train_source3": TRAIN_SOURCE3,
        "train_ground_truth": TRAIN_GROUND_TRUTH,
        "test_source1": TEST_SOURCE1,
        "test_source2": TEST_SOURCE2,
        "test_source3": TEST_SOURCE3,
    }

    missing = []
    for name, path in files.items():
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        status = f"✓ {size:>12,} bytes" if exists else "✗ MISSING"
        print(f"  {name:25s}  {status}  →  {path}")
        if not exists:
            missing.append(name)

    if missing:
        print(f"\n⚠ MISSING FILES: {missing}")
        print("Please place the competition TSV files in the paths above.")
        print("Aborting remaining analysis.")
        sys.exit(1)

    # ── Load all data ────────────────────────────────────────────────
    logger.info("Loading all datasets...")
    train_s1 = load_tsv(TRAIN_SOURCE1)
    train_s2 = load_tsv(TRAIN_SOURCE2)
    train_s3 = load_tsv(TRAIN_SOURCE3)
    train_gt = load_tsv(TRAIN_GROUND_TRUTH)
    test_s1 = load_tsv(TEST_SOURCE1)
    test_s2 = load_tsv(TEST_SOURCE2)
    test_s3 = load_tsv(TEST_SOURCE3)
    logger.info("All datasets loaded successfully.")

    # ── Task B & C & E: Source inspections ───────────────────────────
    inspect_source(train_s1, "TRAIN Source 1")
    inspect_source(train_s2, "TRAIN Source 2")
    inspect_source(train_s3, "TRAIN Source 3")
    inspect_source(test_s1, "TEST Source 1")
    inspect_source(test_s2, "TEST Source 2")
    inspect_source(test_s3, "TEST Source 3")

    # ── Task D: Ground truth analysis ────────────────────────────────
    inspect_ground_truth(train_gt, train_s1, train_s2, train_s3)

    # ── Task F: Cross-source analysis ────────────────────────────────
    train_sources = {"S1": train_s1, "S2": train_s2, "S3": train_s3}
    test_sources = {"S1": test_s1, "S2": test_s2, "S3": test_s3}

    cross_source_analysis(train_s1, train_s2, train_s3, "TRAIN")
    cross_source_analysis(test_s1, test_s2, test_s3, "TEST")
    test_vs_train_comparison(train_sources, test_sources)

    # ── Task G: Validation design ────────────────────────────────────
    validation_design_notes(train_gt, train_s1)

    # ── Summary ──────────────────────────────────────────────────────
    section("PART 1 COMPLETE — SUMMARY")
    print(f"  Train S1: {len(train_s1):,} rows")
    print(f"  Train S2: {len(train_s2):,} rows")
    print(f"  Train S3: {len(train_s3):,} rows")
    print(f"  Train GT: {len(train_gt):,} rows")
    print(f"  Test S1:  {len(test_s1):,} rows")
    print(f"  Test S2:  {len(test_s2):,} rows")
    print(f"  Test S3:  {len(test_s3):,} rows")
    print(f"\n  Countries in train: {sorted(train_s1[COL_COUNTRY].unique())}")
    print(f"  Countries in test:  {sorted(test_s1[COL_COUNTRY].unique())}")


if __name__ == "__main__":
    main()
