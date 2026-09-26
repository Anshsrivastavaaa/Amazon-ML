"""
Part 1 — Data Ingestion & Understanding (Refined)
===================================================
Comprehensive EDA for the Business Entity Resolution Challenge 2026.

Covers all 7 tasks (A–G) with:
  - Ground-truth integrity validation (requirement 1)
  - Leakage-aware validation analysis (requirement 2)
  - Observational only — no normalization, blocking, or ML (requirement 3)
  - All numbers from actual data (requirement 4)

Usage:
    python src/part1_eda.py
"""

import io
import sys
import json
from pathlib import Path
from collections import Counter

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

# ── Output file for structured results ───────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
EDA_RESULTS_FILE = OUTPUT_DIR / "part1_eda_results.json"


# ═══════════════════════════════════════════════════════════════════════
# Formatting helpers
# ═══════════════════════════════════════════════════════════════════════

def section(title: str) -> None:
    width = 80
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def subsection(title: str) -> None:
    print(f"\n--- {title} ---")


# ═══════════════════════════════════════════════════════════════════════
# TASK A — Dataset Inventory
# ═══════════════════════════════════════════════════════════════════════

def task_a_dataset_inventory(results: dict) -> bool:
    """Check all 7 TSV files exist and are loadable. Returns False if any missing."""
    section("TASK A: DATASET INVENTORY")

    files = {
        "train_source1":      TRAIN_SOURCE1,
        "train_source2":      TRAIN_SOURCE2,
        "train_source3":      TRAIN_SOURCE3,
        "train_ground_truth": TRAIN_GROUND_TRUTH,
        "test_source1":       TEST_SOURCE1,
        "test_source2":       TEST_SOURCE2,
        "test_source3":       TEST_SOURCE3,
    }

    inventory = {}
    all_present = True
    for name, path in files.items():
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        status = f"✓ {size:>15,} bytes" if exists else "✗ MISSING"
        print(f"  {name:25s}  {status}")
        inventory[name] = {"exists": exists, "size_bytes": size, "path": str(path)}
        if not exists:
            all_present = False

    results["inventory"] = inventory

    if not all_present:
        print("\n⚠ SOME FILES ARE MISSING. Cannot proceed with analysis.")
        return False

    print("\n✓ All 7 files present.")
    return True


# ═══════════════════════════════════════════════════════════════════════
# TASK B — Schema Inspection
# ═══════════════════════════════════════════════════════════════════════

def task_b_schema_inspection(df: pd.DataFrame, label: str, results: dict) -> None:
    """Inspect schema: columns, dtypes, row count, unique IDs, sample records."""
    subsection(f"Schema: {label}")

    id_col = COL_ENTITY_ID if COL_ENTITY_ID in df.columns else (
        COL_SOURCE1_ID if COL_SOURCE1_ID in df.columns else df.columns[0]
    )

    info = {
        "rows": len(df),
        "columns": list(df.columns),
        "id_column": id_col,
        "unique_entity_ids": int(df[id_col].nunique()),
    }

    print(f"  Rows:              {info['rows']:,}")
    print(f"  Columns:           {info['columns']}")
    print(f"  ID Column:         {id_col}")
    print(f"  Dtypes:")
    for col in df.columns:
        print(f"    {col:25s}  {df[col].dtype}")

    n_dup_ids = len(df) - info["unique_entity_ids"]
    info["duplicate_entity_ids"] = n_dup_ids
    print(f"  Unique {id_col}: {info['unique_entity_ids']:,}")
    print(f"  Duplicate IDs:     {n_dup_ids:,}")
    if n_dup_ids > 0:
        dups = df[df.duplicated(subset=[id_col], keep=False)]
        print(f"  ⚠ Duplicate ID samples:")
        print(dups.head(10).to_string(index=False))

    print(f"\n  First 3 records:")
    print(df.head(3).to_string(index=False))
    print(f"\n  Last 3 records:")
    print(df.tail(3).to_string(index=False))

    results[f"schema_{label}"] = info


# ═══════════════════════════════════════════════════════════════════════
# TASK C — Source Verification
# ═══════════════════════════════════════════════════════════════════════

def task_c_source_verification(df: pd.DataFrame, expected_prefix: str,
                                 label: str, results: dict) -> None:
    """Verify entity_id prefixes match the expected source."""
    subsection(f"Source Verification: {label}")

    prefixes = df[COL_ENTITY_ID].str.split("-", n=1).str[0].value_counts()
    print(f"  ID prefixes found:")
    for prefix, count in prefixes.items():
        match = "✓" if prefix == expected_prefix else "✗ UNEXPECTED"
        print(f"    {prefix}: {count:,}  {match}")

    unexpected = set(prefixes.index) - {expected_prefix}
    info = {
        "expected_prefix": expected_prefix,
        "prefix_counts": prefixes.to_dict(),
        "all_match": len(unexpected) == 0,
        "unexpected_prefixes": list(unexpected),
    }
    results[f"source_verify_{label}"] = info

    if unexpected:
        print(f"  ⚠ UNEXPECTED PREFIXES: {unexpected}")
    else:
        print(f"  ✓ All IDs have expected prefix '{expected_prefix}'")


# ═══════════════════════════════════════════════════════════════════════
# TASK D — Ground-Truth Analysis + Integrity Validation
# ═══════════════════════════════════════════════════════════════════════

def task_d_ground_truth(gt: pd.DataFrame, s1: pd.DataFrame,
                         s2: pd.DataFrame, s3: pd.DataFrame,
                         results: dict) -> None:
    """Deep ground-truth analysis including full integrity validation."""
    section("TASK D: GROUND TRUTH ANALYSIS & INTEGRITY VALIDATION")

    # ── Parse matched IDs ────────────────────────────────────────────
    gt = gt.copy()
    gt["match_list"] = gt[COL_MATCHED_IDS].apply(
        lambda x: [m.strip() for m in str(x).split(",") if m.strip()]
                  if pd.notna(x) and str(x).strip() else []
    )
    gt["match_count"] = gt["match_list"].apply(len)

    # ── D.1: Match count distribution ────────────────────────────────
    subsection("D.1: Match Count Distribution")
    count_dist = gt["match_count"].value_counts().sort_index()
    total = len(gt)
    for count, n in count_dist.items():
        print(f"  {count} matches: {n:,} entities ({100*n/total:.2f}%)")

    n_zero = int((gt["match_count"] == 0).sum())
    n_one = int((gt["match_count"] == 1).sum())
    n_many = int((gt["match_count"] > 1).sum())
    max_matches = int(gt["match_count"].max())
    avg_matches = float(gt["match_count"].mean())
    avg_nonzero = float(gt.loc[gt["match_count"] > 0, "match_count"].mean()) if n_one + n_many > 0 else 0.0

    print(f"\n  Zero matches (singletons): {n_zero:,} ({100*n_zero/total:.2f}%)")
    print(f"  Exactly one match:         {n_one:,} ({100*n_one/total:.2f}%)")
    print(f"  Multiple matches (≥2):     {n_many:,} ({100*n_many/total:.2f}%)")
    print(f"  Max matches for one S1:    {max_matches}")
    print(f"  Average matches (all):     {avg_matches:.3f}")
    print(f"  Average matches (non-zero):{avg_nonzero:.3f}")

    gt_stats = {
        "total_s1_entities": total,
        "zero_matches": n_zero,
        "one_match": n_one,
        "multiple_matches": n_many,
        "max_matches": max_matches,
        "avg_matches_all": round(avg_matches, 4),
        "avg_matches_nonzero": round(avg_nonzero, 4),
        "distribution": {str(k): int(v) for k, v in count_dist.items()},
    }

    # ── D.2: S2 vs S3 breakdown ─────────────────────────────────────
    subsection("D.2: S2 vs S3 Match Breakdown")
    all_matched = [mid for lst in gt["match_list"] for mid in lst]
    s2_matches = [m for m in all_matched if m.startswith("S2")]
    s3_matches = [m for m in all_matched if m.startswith("S3")]
    other_matches = [m for m in all_matched
                     if not m.startswith("S2") and not m.startswith("S3")]

    print(f"  Total matched IDs:    {len(all_matched):,}")
    print(f"    S2 matches:         {len(s2_matches):,}")
    print(f"    S3 matches:         {len(s3_matches):,}")
    if other_matches:
        print(f"    ⚠ OTHER matches:   {len(other_matches):,}  →  {other_matches[:10]}")

    gt["has_s2"] = gt["match_list"].apply(lambda lst: any(m.startswith("S2") for m in lst))
    gt["has_s3"] = gt["match_list"].apply(lambda lst: any(m.startswith("S3") for m in lst))

    has_matches = gt[gt["match_count"] > 0]
    s2_only = int((has_matches["has_s2"] & ~has_matches["has_s3"]).sum())
    s3_only = int(((~has_matches["has_s2"]) & has_matches["has_s3"]).sum())
    both = int((has_matches["has_s2"] & has_matches["has_s3"]).sum())

    print(f"\n  S1 entities with matches: {len(has_matches):,}")
    print(f"    S2 only:   {s2_only:,}")
    print(f"    S3 only:   {s3_only:,}")
    print(f"    Both:      {both:,}")

    gt_stats["s2_match_count"] = len(s2_matches)
    gt_stats["s3_match_count"] = len(s3_matches)
    gt_stats["other_match_count"] = len(other_matches)
    gt_stats["s2_only_entities"] = s2_only
    gt_stats["s3_only_entities"] = s3_only
    gt_stats["both_entities"] = both

    # ── D.3: INTEGRITY VALIDATION (Requirement 1) ───────────────────
    subsection("D.3: Ground-Truth Integrity Validation")

    issues = []
    s1_ids = set(s1[COL_ENTITY_ID])
    s2_ids = set(s2[COL_ENTITY_ID])
    s3_ids = set(s3[COL_ENTITY_ID])
    gt_s1_ids = set(gt[COL_SOURCE1_ID])

    # Check 1: Every source1_entity_id exists in train_source1.tsv
    missing_from_s1 = gt_s1_ids - s1_ids
    print(f"\n  [Check 1] S1 IDs in GT not in source1: {len(missing_from_s1):,}")
    if missing_from_s1:
        issues.append(f"S1 IDs in ground truth but not in source1: {list(missing_from_s1)[:10]}")
        print(f"    ⚠ Samples: {list(missing_from_s1)[:10]}")
    else:
        print(f"    ✓ All S1 IDs in GT exist in train_source1.tsv")

    # Check 1b: Every source1 entity has a ground truth row
    extra_in_s1 = s1_ids - gt_s1_ids
    print(f"  [Check 1b] S1 IDs in source1 but not in GT: {len(extra_in_s1):,}")
    if extra_in_s1:
        issues.append(f"S1 IDs in source1 but missing from ground truth: {list(extra_in_s1)[:10]}")
        print(f"    ⚠ Samples: {list(extra_in_s1)[:10]}")
    else:
        print(f"    ✓ Every source1 entity has a ground truth row")

    # Check 2: Every matched_entity_id exists in S2 or S3
    s2_match_set = set(s2_matches)
    s3_match_set = set(s3_matches)
    missing_s2 = s2_match_set - s2_ids
    missing_s3 = s3_match_set - s3_ids
    print(f"  [Check 2a] S2 matched IDs not in source2: {len(missing_s2):,}")
    if missing_s2:
        issues.append(f"S2 matched IDs not in source2: {list(missing_s2)[:10]}")
        print(f"    ⚠ Samples: {list(missing_s2)[:10]}")
    else:
        print(f"    ✓ All S2 matched IDs exist in train_source2.tsv")

    print(f"  [Check 2b] S3 matched IDs not in source3: {len(missing_s3):,}")
    if missing_s3:
        issues.append(f"S3 matched IDs not in source3: {list(missing_s3)[:10]}")
        print(f"    ⚠ Samples: {list(missing_s3)[:10]}")
    else:
        print(f"    ✓ All S3 matched IDs exist in train_source3.tsv")

    # Check 3: No S1 entity incorrectly listed as a match
    s1_in_matches = [m for m in all_matched if m.startswith("S1")]
    print(f"  [Check 3] S1 IDs appearing as matched IDs: {len(s1_in_matches):,}")
    if s1_in_matches:
        issues.append(f"S1 IDs found in matched_entity_ids (self-match): {s1_in_matches[:10]}")
        print(f"    ⚠ Samples: {s1_in_matches[:10]}")
    else:
        print(f"    ✓ No S1 IDs appear as matched entities")

    # Check 4: No duplicate IDs inside a matched_entity_ids list
    rows_with_internal_dups = [
        s1_id for s1_id, mlist in zip(gt[COL_SOURCE1_ID], gt["match_list"])
        if len(mlist) != len(set(mlist))
    ]
    print(f"  [Check 4] Rows with duplicate IDs in match list: {len(rows_with_internal_dups):,}")
    if rows_with_internal_dups:
        issues.append(f"Rows with internal duplicate matched IDs: {rows_with_internal_dups[:10]}")
        print(f"    ⚠ Samples: {rows_with_internal_dups[:10]}")
    else:
        print(f"    ✓ No internal duplicates in any matched_entity_ids list")

    # Check 5: All IDs have valid S1-/S2-/S3- prefixes
    invalid_s1_ids = [sid for sid in gt_s1_ids if not sid.startswith("S1-")]
    invalid_match_ids = [m for m in all_matched
                         if not m.startswith("S2-") and not m.startswith("S3-")]
    print(f"  [Check 5a] source1_entity_ids without S1- prefix: {len(invalid_s1_ids):,}")
    if invalid_s1_ids:
        issues.append(f"Invalid S1 ID prefixes: {invalid_s1_ids[:10]}")
    else:
        print(f"    ✓ All source1_entity_ids have S1- prefix")

    print(f"  [Check 5b] matched IDs without S2-/S3- prefix: {len(invalid_match_ids):,}")
    if invalid_match_ids:
        issues.append(f"Invalid matched ID prefixes: {invalid_match_ids[:10]}")
    else:
        print(f"    ✓ All matched IDs have S2- or S3- prefix")

    # Check 6: No malformed or unexpected IDs
    import re
    id_pattern = re.compile(r'^S[123]-\d+$')
    malformed_s1 = [sid for sid in gt_s1_ids if not id_pattern.match(sid)]
    malformed_match = [m for m in set(all_matched) if not id_pattern.match(m)]
    print(f"  [Check 6a] Malformed S1 IDs: {len(malformed_s1):,}")
    if malformed_s1:
        issues.append(f"Malformed S1 IDs: {malformed_s1[:10]}")
        print(f"    ⚠ Samples: {malformed_s1[:10]}")
    else:
        print(f"    ✓ All S1 IDs match pattern S1-DIGITS")

    print(f"  [Check 6b] Malformed matched IDs: {len(malformed_match):,}")
    if malformed_match:
        issues.append(f"Malformed matched IDs: {malformed_match[:10]}")
        print(f"    ⚠ Samples: {malformed_match[:10]}")
    else:
        print(f"    ✓ All matched IDs match pattern S[23]-DIGITS")

    # Check 7: Count of empty matched_entity_ids
    print(f"  [Check 7] S1 entities with empty matched_entity_ids: {n_zero:,}")

    # Check 8: Duplicate source1_entity_id rows
    dup_gt_rows = gt[gt.duplicated(subset=[COL_SOURCE1_ID], keep=False)]
    n_dup_gt = dup_gt_rows[COL_SOURCE1_ID].nunique()
    print(f"  [Check 8] Duplicate S1 ID rows in GT: {n_dup_gt:,}")
    if n_dup_gt > 0:
        issues.append(f"Duplicate source1_entity_id rows: {dup_gt_rows[COL_SOURCE1_ID].unique()[:10].tolist()}")
        print(f"    ⚠ Samples: {dup_gt_rows[COL_SOURCE1_ID].unique()[:10].tolist()}")
    else:
        print(f"    ✓ No duplicate source1_entity_id rows")

    # Summary
    print(f"\n  INTEGRITY SUMMARY: {len(issues)} issue(s) found")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
    if not issues:
        print(f"    ✓ Ground truth passed all integrity checks")

    gt_stats["integrity_issues"] = issues
    gt_stats["integrity_passed"] = len(issues) == 0
    results["ground_truth"] = gt_stats


# ═══════════════════════════════════════════════════════════════════════
# TASK E — Data Quality Analysis
# ═══════════════════════════════════════════════════════════════════════

def task_e_data_quality(df: pd.DataFrame, label: str, results: dict) -> None:
    """Comprehensive data quality analysis for a source file."""
    subsection(f"Data Quality: {label}")
    quality = {}

    # Missing / empty values
    print(f"\n  Missing & Empty Values:")
    missing_info = {}
    for col in df.columns:
        n_null = int(df[col].isna().sum())
        n_empty = int((df[col].astype(str).str.strip() == "").sum())
        print(f"    {col:25s}  null={n_null:,}  empty_string={n_empty:,}")
        missing_info[col] = {"null": n_null, "empty": n_empty}
    quality["missing"] = missing_info

    # Country distribution
    if COL_COUNTRY in df.columns:
        print(f"\n  Country Distribution:")
        country_counts = df[COL_COUNTRY].value_counts(dropna=False)
        country_dict = {}
        for country, n in country_counts.items():
            pct = 100 * n / len(df)
            print(f"    {str(country):20s}  {n:>10,}  ({pct:.2f}%)")
            country_dict[str(country)] = int(n)
        quality["country_distribution"] = country_dict

    # Field length statistics
    print(f"\n  Field Length Statistics:")
    length_info = {}
    for col in [COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS]:
        if col not in df.columns:
            continue
        lengths = df[col].astype(str).str.len()
        stats = {
            "min": int(lengths.min()),
            "max": int(lengths.max()),
            "mean": round(float(lengths.mean()), 1),
            "median": int(lengths.median()),
            "std": round(float(lengths.std()), 1),
            "p5": int(lengths.quantile(0.05)),
            "p95": int(lengths.quantile(0.95)),
        }
        print(f"\n    {col}:")
        print(f"      min={stats['min']}  max={stats['max']}  "
              f"mean={stats['mean']}  median={stats['median']}  "
              f"std={stats['std']}")
        print(f"      5th pct={stats['p5']}  95th pct={stats['p95']}")

        n_very_short = int((lengths <= 2).sum())
        n_empty_str = int((lengths == 0).sum())
        stats["very_short_le2"] = n_very_short
        stats["empty_length"] = n_empty_str
        if n_very_short > 0:
            samples = df.loc[lengths <= 2, col].head(5).tolist()
            print(f"      ⚠ Very short (≤2 chars): {n_very_short:,}")
            print(f"        Samples: {samples}")
            stats["very_short_samples"] = samples

        n_very_long = int((lengths > 200).sum())
        stats["very_long_gt200"] = n_very_long
        if n_very_long > 0:
            samples = df.loc[lengths > 200, col].head(3).tolist()
            print(f"      ⚠ Very long (>200 chars): {n_very_long:,}")
            print(f"        Samples: {[s[:100]+'...' for s in samples]}")

        length_info[col] = stats
    quality["field_lengths"] = length_info

    # Duplicate field values
    print(f"\n  Duplicate Field Values:")
    dup_info = {}
    for col in [COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS]:
        if col not in df.columns:
            continue
        val_counts = df[col].value_counts()
        n_dup_vals = int((val_counts > 1).sum())
        total_dup_rows = int(val_counts[val_counts > 1].sum())
        print(f"    {col}:")
        print(f"      Unique values: {len(val_counts):,}")
        print(f"      Values appearing >1 time: {n_dup_vals:,} "
              f"(covering {total_dup_rows:,} rows)")
        if n_dup_vals > 0:
            top5 = val_counts.head(5)
            print(f"      Top repeated:")
            for val, cnt in top5.items():
                print(f"        ({cnt}×) {val[:80]}")
        dup_info[col] = {
            "unique_values": int(len(val_counts)),
            "duplicated_values": n_dup_vals,
            "rows_in_duplicates": total_dup_rows,
        }
    quality["duplicates"] = dup_info

    # Non-ASCII character analysis
    print(f"\n  Character Analysis:")
    char_info = {}
    for col in [COL_BUSINESS_NAME, COL_BUSINESS_ADDRESS]:
        if col not in df.columns:
            continue
        all_text = "".join(df[col].astype(str).tolist())
        non_ascii = {c for c in all_text if ord(c) > 127}
        n_non_ascii = len(non_ascii)
        print(f"    {col}: {n_non_ascii} distinct non-ASCII characters")
        if non_ascii:
            sample = sorted(list(non_ascii))[:30]
            print(f"      Sample chars: {sample}")
            # Count how many records contain non-ASCII
            has_non_ascii = df[col].astype(str).str.contains(r'[^\x00-\x7F]', regex=True)
            n_records = int(has_non_ascii.sum())
            print(f"      Records with non-ASCII: {n_records:,} ({100*n_records/len(df):.2f}%)")
            char_info[col] = {
                "distinct_non_ascii": n_non_ascii,
                "records_with_non_ascii": n_records,
                "sample_chars": [c for c in sample[:15]],
            }
        else:
            char_info[col] = {"distinct_non_ascii": 0, "records_with_non_ascii": 0}
    quality["characters"] = char_info

    results[f"quality_{label}"] = quality


# ═══════════════════════════════════════════════════════════════════════
# TASK F — Relationship Analysis
# ═══════════════════════════════════════════════════════════════════════

def task_f_relationship_analysis(gt: pd.DataFrame, s1: pd.DataFrame,
                                   s2: pd.DataFrame, s3: pd.DataFrame,
                                   results: dict) -> None:
    """Structural relationship analysis — critical for validation design."""
    section("TASK F: RELATIONSHIP ANALYSIS")

    gt = gt.copy()
    gt["match_list"] = gt[COL_MATCHED_IDS].apply(
        lambda x: [m.strip() for m in str(x).split(",") if m.strip()]
                  if pd.notna(x) and str(x).strip() else []
    )

    all_matched = [mid for lst in gt["match_list"] for mid in lst]

    # ── F.1: Are S2/S3 entities reused across multiple S1 relationships? ──
    subsection("F.1: S2/S3 Entity Reuse Across S1 Relationships")
    matched_id_counts = Counter(all_matched)
    n_unique_matched = len(matched_id_counts)
    reused = {k: v for k, v in matched_id_counts.items() if v > 1}
    n_reused = len(reused)

    print(f"  Total unique matched S2/S3 IDs: {n_unique_matched:,}")
    print(f"  S2/S3 IDs appearing in >1 S1 relationship: {n_reused:,}")

    if n_reused > 0:
        print(f"\n  ⚠ CRITICAL: {n_reused:,} S2/S3 entities are linked to multiple S1 entities!")
        print(f"  This has MAJOR implications for validation:")
        print(f"    - If we split by S1, shared S2/S3 entities could leak information")
        print(f"    - The model could 'see' a S2/S3 entity in training and recognize it in validation")
        print()

        # Break down by max reuse
        reuse_dist = Counter(matched_id_counts.values())
        print(f"  Reuse distribution:")
        for n_uses, count in sorted(reuse_dist.items()):
            print(f"    Appears in {n_uses} S1 relationships: {count:,} IDs")

        # Show top reused
        top_reused = sorted(reused.items(), key=lambda x: -x[1])[:10]
        print(f"\n  Top 10 most reused S2/S3 IDs:")
        for mid, cnt in top_reused:
            print(f"    {mid}: linked to {cnt} S1 entities")

        # Which S1 entities share S2/S3 links?
        s2s3_to_s1 = {}
        for s1_id, mlist in zip(gt[COL_SOURCE1_ID], gt["match_list"]):
            for mid in mlist:
                if mid not in s2s3_to_s1:
                    s2s3_to_s1[mid] = []
                s2s3_to_s1[mid].append(s1_id)

        shared_groups = {k: v for k, v in s2s3_to_s1.items() if len(v) > 1}
        n_s1_involved = len(set(s1_id for group in shared_groups.values() for s1_id in group))
        print(f"\n  S1 entities involved in shared relationships: {n_s1_involved:,}")
    else:
        print(f"  ✓ Every S2/S3 entity maps to exactly one S1 entity")
        print(f"  → This simplifies validation: a simple S1-level split is safe")

    # ── F.2: Cross-source analysis ───────────────────────────────────
    subsection("F.2: Cross-Source Size Comparison")
    print(f"  Source 1: {len(s1):,} entities (deduplicated reference)")
    print(f"  Source 2: {len(s2):,} entities")
    print(f"  Source 3: {len(s3):,} entities")
    print(f"  S2 + S3:  {len(s2) + len(s3):,} total candidates")
    print(f"  Ratio (S2+S3)/S1: {(len(s2) + len(s3)) / len(s1):.2f}")

    # ── F.3: Country overlap ─────────────────────────────────────────
    subsection("F.3: Country Distribution by Source")
    for src, label in [(s1, "S1"), (s2, "S2"), (s3, "S3")]:
        counts = src[COL_COUNTRY].value_counts()
        print(f"\n  {label}:")
        for country, n in counts.items():
            print(f"    {country}: {n:,}")

    c1 = set(s1[COL_COUNTRY].unique())
    c2 = set(s2[COL_COUNTRY].unique())
    c3 = set(s3[COL_COUNTRY].unique())
    print(f"\n  S1 countries: {sorted(c1)}")
    print(f"  S2 countries: {sorted(c2)}")
    print(f"  S3 countries: {sorted(c3)}")

    # ── F.4: Match patterns by country ───────────────────────────────
    subsection("F.4: Match Patterns by Country")
    gt["match_count"] = gt["match_list"].apply(len)
    gt_with_country = gt.merge(
        s1[[COL_ENTITY_ID, COL_COUNTRY]],
        left_on=COL_SOURCE1_ID, right_on=COL_ENTITY_ID, how="left"
    )

    country_patterns = {}
    for country, grp in gt_with_country.groupby(COL_COUNTRY):
        total_c = len(grp)
        zero_c = int((grp["match_count"] == 0).sum())
        one_c = int((grp["match_count"] == 1).sum())
        many_c = int((grp["match_count"] > 1).sum())
        avg_m = float(grp["match_count"].mean())
        max_m = int(grp["match_count"].max())

        print(f"\n  Country: {country}")
        print(f"    Total S1 entities:  {total_c:,}")
        print(f"    Zero matches:       {zero_c:,} ({100*zero_c/total_c:.2f}%)")
        print(f"    One match:          {one_c:,} ({100*one_c/total_c:.2f}%)")
        print(f"    Multiple matches:   {many_c:,} ({100*many_c/total_c:.2f}%)")
        print(f"    Avg match count:    {avg_m:.3f}")
        print(f"    Max match count:    {max_m}")

        country_patterns[country] = {
            "total": total_c, "zero": zero_c, "one": one_c,
            "many": many_c, "avg": round(avg_m, 4), "max": max_m,
        }

    results["relationship_analysis"] = {
        "n_unique_matched_ids": n_unique_matched,
        "n_reused_ids": n_reused,
        "country_patterns": country_patterns,
    }


# ═══════════════════════════════════════════════════════════════════════
# TASK G — Validation Design
# ═══════════════════════════════════════════════════════════════════════

def task_g_validation_design(gt: pd.DataFrame, s1: pd.DataFrame,
                               s2: pd.DataFrame, s3: pd.DataFrame,
                               results: dict) -> None:
    """Investigate leakage risks and propose validation strategy."""
    section("TASK G: VALIDATION STRATEGY ANALYSIS")

    gt = gt.copy()
    gt["match_list"] = gt[COL_MATCHED_IDS].apply(
        lambda x: [m.strip() for m in str(x).split(",") if m.strip()]
                  if pd.notna(x) and str(x).strip() else []
    )
    gt["match_count"] = gt["match_list"].apply(len)

    # ── G.1: Check S2/S3 entity sharing (leakage risk) ──────────────
    subsection("G.1: Leakage Risk Assessment")

    all_matched = [mid for lst in gt["match_list"] for mid in lst]
    matched_id_counts = Counter(all_matched)
    reused = {k: v for k, v in matched_id_counts.items() if v > 1}

    if reused:
        # Build connected components through shared S2/S3 IDs
        from collections import defaultdict

        s2s3_to_s1 = defaultdict(set)
        s1_to_s2s3 = defaultdict(set)
        for s1_id, mlist in zip(gt[COL_SOURCE1_ID], gt["match_list"]):
            for mid in mlist:
                s2s3_to_s1[mid].add(s1_id)
                s1_to_s2s3[s1_id].add(mid)

        # Find connected components using BFS
        visited_s1 = set()
        components = []
        for s1_id in gt[COL_SOURCE1_ID]:
            if s1_id in visited_s1:
                continue
            component_s1 = set()
            component_s2s3 = set()
            queue = [s1_id]
            while queue:
                curr = queue.pop()
                if curr in visited_s1:
                    continue
                visited_s1.add(curr)
                component_s1.add(curr)
                for mid in s1_to_s2s3.get(curr, []):
                    component_s2s3.add(mid)
                    for linked_s1 in s2s3_to_s1.get(mid, []):
                        if linked_s1 not in visited_s1:
                            queue.append(linked_s1)
            components.append((component_s1, component_s2s3))

        comp_sizes = [len(c[0]) for c in components]
        comp_sizes_counter = Counter(comp_sizes)

        print(f"  Connected components (S1 entities linked by shared S2/S3 IDs):")
        print(f"    Total components: {len(components):,}")
        print(f"    Size distribution:")
        for size, count in sorted(comp_sizes_counter.items()):
            if count <= 20 or size > 1:
                print(f"      Size {size}: {count:,} components")

        largest = max(components, key=lambda c: len(c[0]))
        print(f"\n    Largest component: {len(largest[0]):,} S1 entities, "
              f"{len(largest[1]):,} S2/S3 entities")

        n_singleton_components = sum(1 for s in comp_sizes if s == 1)
        n_multi_components = len(components) - n_singleton_components
        print(f"    Singleton components (1 S1): {n_singleton_components:,}")
        print(f"    Multi-entity components:     {n_multi_components:,}")

        results["validation_analysis"] = {
            "has_shared_s2s3": True,
            "n_reused_ids": len(reused),
            "n_components": len(components),
            "n_singleton_components": n_singleton_components,
            "n_multi_components": n_multi_components,
            "largest_component_s1": len(largest[0]),
            "largest_component_s2s3": len(largest[1]),
        }

        print(f"\n  LEAKAGE RISK ASSESSMENT:")
        if n_multi_components > 0:
            print(f"    ⚠ {n_multi_components:,} components contain >1 S1 entity linked")
            print(f"      through shared S2/S3 IDs.")
            print(f"    → A naive S1-level random split COULD leak information if")
            print(f"      two S1 entities in the same component end up in different folds.")
            print(f"    → The model could learn S2/S3 entity features from train and")
            print(f"      recognize the same S2/S3 entity in validation.")
        else:
            print(f"    ✓ No S1 entities share S2/S3 links.")
            print(f"    → A simple S1-level split is safe.")

    else:
        print(f"  ✓ No S2/S3 entities are shared across S1 relationships.")
        print(f"  → No leakage risk from shared entities. S1-level split is safe.")
        results["validation_analysis"] = {
            "has_shared_s2s3": False,
            "n_reused_ids": 0,
        }

    # ── G.2: Country stratification ──────────────────────────────────
    subsection("G.2: Country Stratification Considerations")
    gt_with_country = gt.merge(
        s1[[COL_ENTITY_ID, COL_COUNTRY]],
        left_on=COL_SOURCE1_ID, right_on=COL_ENTITY_ID, how="left"
    )

    print(f"  Country distribution in training S1:")
    for country, n in gt_with_country[COL_COUNTRY].value_counts().items():
        pct = 100 * n / len(gt_with_country)
        print(f"    {country}: {n:,} ({pct:.1f}%)")

    # Match-count bucket distribution per country
    print(f"\n  Match-count bucket × country:")
    gt_with_country["bucket"] = gt_with_country["match_count"].apply(
        lambda x: "0" if x == 0 else ("1" if x == 1 else "2+")
    )
    ct = pd.crosstab(gt_with_country[COL_COUNTRY], gt_with_country["bucket"])
    print(ct.to_string())

    # ── G.3: Proposed strategy ───────────────────────────────────────
    subsection("G.3: Proposed Validation Strategy")
    print("""
  PROPOSED STRATEGY (for approval — NOT implemented yet):

  1. SPLIT UNIT: Source 1 entities (NOT pairs, NOT rows)
     - Each S1 entity and ALL its matched S2/S3 entities go entirely
       into train or validation, never split across both.
     - This mirrors test-time: the model will see entirely new S1 entities.

  2. LEAKAGE HANDLING:""")

    if reused:
        print("""     - Some S2/S3 entities are shared across S1 relationships.
     - Option A (STRICT): Split at the connected-component level.
       Entire components go to train or validation.
       This is the safest but may create imbalanced splits if components
       are large.
     - Option B (PRAGMATIC): Split at S1 level, accepting minor leakage.
       If shared S2/S3 entities are rare and the reuse is low,
       the leakage impact is negligible.
     - RECOMMENDATION: Inspect the severity. If most components are
       size 1, Option B is acceptable. If large components exist,
       Option A is necessary.""")
    else:
        print("""     - No S2/S3 entity reuse detected → simple S1-level split is safe.
     - No connected-component splitting needed.""")

    print("""
  3. STRATIFICATION:
     - Stratify by country to ensure both countries appear in train and validation.
     - Stratify by match-count bucket (0, 1, 2+) to preserve distribution.
     - Use 80/20 split (or 5-fold CV for more robust estimates).

  4. PIPELINE REQUIREMENT:
     - The entire pipeline (blocking → features → model → threshold)
       must be re-run on each fold independently.
     - Blocking must be applied fresh to the validation fold.
     - The model must be trained ONLY on training-fold data.

  5. TEST-TIME RESEMBLANCE:
     - At test time, the model sees entirely new S1 entities (test_source1)
       and must match against test_source2 and test_source3.
     - The validation setup mirrors this: validation S1 entities are new
       to the model, and it must match them against the S2/S3 pool.
     - Note: France appears only in test. Our validation won't have France,
       so we must design features that generalize across countries
       (not hard-code country-specific rules).

  AWAITING APPROVAL before implementing this strategy.
""")


# ═══════════════════════════════════════════════════════════════════════
# Train vs Test Comparison
# ═══════════════════════════════════════════════════════════════════════

def train_vs_test_comparison(train_sources: dict, test_sources: dict,
                               results: dict) -> None:
    """Compare train and test distributions to identify domain shift."""
    section("TRAIN vs TEST COMPARISON")

    comparison = {}
    for src_name in ["S1", "S2", "S3"]:
        tr = train_sources[src_name]
        te = test_sources[src_name]
        subsection(f"Source {src_name}")

        info = {
            "train_rows": len(tr),
            "test_rows": len(te),
        }

        print(f"  Train rows: {len(tr):,}")
        print(f"  Test rows:  {len(te):,}")

        # Country comparison
        tr_countries = sorted(tr[COL_COUNTRY].unique().tolist())
        te_countries = sorted(te[COL_COUNTRY].unique().tolist())
        new_countries = sorted(set(te_countries) - set(tr_countries))
        print(f"  Train countries: {tr_countries}")
        print(f"  Test countries:  {te_countries}")
        if new_countries:
            print(f"  ⚠ NEW countries in test (not in train): {new_countries}")
            # How many test entities belong to new countries
            for nc in new_countries:
                n = int((te[COL_COUNTRY] == nc).sum())
                print(f"    {nc}: {n:,} entities ({100*n/len(te):.2f}%)")

        info["train_countries"] = tr_countries
        info["test_countries"] = te_countries
        info["new_countries"] = new_countries

        # Name length comparison
        tr_nlen = tr[COL_BUSINESS_NAME].str.len()
        te_nlen = te[COL_BUSINESS_NAME].str.len()
        print(f"  Name length — Train: mean={tr_nlen.mean():.1f} med={tr_nlen.median():.0f} | "
              f"Test: mean={te_nlen.mean():.1f} med={te_nlen.median():.0f}")

        # Address length comparison
        tr_alen = tr[COL_BUSINESS_ADDRESS].str.len()
        te_alen = te[COL_BUSINESS_ADDRESS].str.len()
        print(f"  Addr length — Train: mean={tr_alen.mean():.1f} med={tr_alen.median():.0f} | "
              f"Test: mean={te_alen.mean():.1f} med={te_alen.median():.0f}")

        # ID overlap (should be zero)
        overlap = set(tr[COL_ENTITY_ID]) & set(te[COL_ENTITY_ID])
        print(f"  ID overlap train∩test: {len(overlap):,}")
        if overlap:
            print(f"    ⚠ OVERLAPPING IDs: {list(overlap)[:5]}")
        info["id_overlap"] = len(overlap)

        comparison[src_name] = info

    results["train_vs_test"] = comparison


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    section("PART 1 — DATA INGESTION & UNDERSTANDING")
    print("Business Entity Resolution Challenge 2026")
    print("All numbers from actual data. No assumptions.")

    results = {}

    # ── Task A ───────────────────────────────────────────────────────
    if not task_a_dataset_inventory(results):
        print("\n⚠ Cannot proceed — data files missing.")
        sys.exit(1)

    # ── Load all data ────────────────────────────────────────────────
    logger.info("Loading all 7 datasets...")
    train_s1 = load_tsv(TRAIN_SOURCE1)
    train_s2 = load_tsv(TRAIN_SOURCE2)
    train_s3 = load_tsv(TRAIN_SOURCE3)
    train_gt = load_tsv(TRAIN_GROUND_TRUTH)
    test_s1 = load_tsv(TEST_SOURCE1)
    test_s2 = load_tsv(TEST_SOURCE2)
    test_s3 = load_tsv(TEST_SOURCE3)
    logger.info("All datasets loaded.")

    # ── Task B: Schema ───────────────────────────────────────────────
    section("TASK B: SCHEMA INSPECTION")
    for df, label in [
        (train_s1, "train_s1"), (train_s2, "train_s2"), (train_s3, "train_s3"),
        (train_gt, "train_gt"),
        (test_s1, "test_s1"), (test_s2, "test_s2"), (test_s3, "test_s3"),
    ]:
        task_b_schema_inspection(df, label, results)

    # ── Task C: Source Verification ──────────────────────────────────
    section("TASK C: SOURCE VERIFICATION")
    for df, prefix, label in [
        (train_s1, "S1", "train_s1"), (train_s2, "S2", "train_s2"),
        (train_s3, "S3", "train_s3"),
        (test_s1, "S1", "test_s1"), (test_s2, "S2", "test_s2"),
        (test_s3, "S3", "test_s3"),
    ]:
        task_c_source_verification(df, prefix, label, results)

    # ── Task D: Ground Truth ─────────────────────────────────────────
    task_d_ground_truth(train_gt, train_s1, train_s2, train_s3, results)

    # ── Task E: Data Quality ─────────────────────────────────────────
    section("TASK E: DATA QUALITY ANALYSIS")
    for df, label in [
        (train_s1, "train_s1"), (train_s2, "train_s2"), (train_s3, "train_s3"),
        (test_s1, "test_s1"), (test_s2, "test_s2"), (test_s3, "test_s3"),
    ]:
        task_e_data_quality(df, label, results)

    # ── Task F: Relationships ────────────────────────────────────────
    task_f_relationship_analysis(train_gt, train_s1, train_s2, train_s3, results)

    # ── Train vs Test ────────────────────────────────────────────────
    train_sources = {"S1": train_s1, "S2": train_s2, "S3": train_s3}
    test_sources = {"S1": test_s1, "S2": test_s2, "S3": test_s3}
    train_vs_test_comparison(train_sources, test_sources, results)

    # ── Task G: Validation Design ────────────────────────────────────
    task_g_validation_design(train_gt, train_s1, train_s2, train_s3, results)

    # ── Save structured results ──────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EDA_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Structured results saved to: {EDA_RESULTS_FILE}")

    # ── Final summary ────────────────────────────────────────────────
    section("PART 1 — EXECUTION COMPLETE")
    print(f"  Train S1: {len(train_s1):,} rows")
    print(f"  Train S2: {len(train_s2):,} rows")
    print(f"  Train S3: {len(train_s3):,} rows")
    print(f"  Train GT: {len(train_gt):,} rows")
    print(f"  Test S1:  {len(test_s1):,} rows")
    print(f"  Test S2:  {len(test_s2):,} rows")
    print(f"  Test S3:  {len(test_s3):,} rows")
    print(f"\n  Review the output above and the saved JSON for the full Part 1 report.")
    print(f"  STOP. Awaiting review before Part 2.")


if __name__ == "__main__":
    main()
