"""Part 2 - normalization experiments for business entity resolution.

The module keeps the original text intact and evaluates conservative derived
representations on real training data. It is intentionally independent from
blocking and matching so its findings can be reused by later pipeline stages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (  # noqa: E402
    PROCESSED_DATA_DIR,
    TRAIN_GROUND_TRUTH,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)


LEGAL_SUFFIXES = {
    "ag",
    "agco",
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "llp",
    "ltd",
    "pvt",
    "private",
}
SUFFIX_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(sorted(LEGAL_SUFFIXES, key=len, reverse=True))
    + r")\b",
    flags=re.IGNORECASE,
)
NON_ALNUM_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)
WHITESPACE_PATTERN = re.compile(r"\s+")


def safe_unicode(value: object) -> str:
    """Return a conservative Unicode-normalized, case-folded text value."""
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    return text


def compact_safe(value: object) -> str:
    """Return a punctuation-insensitive form without transliteration."""
    return WHITESPACE_PATTERN.sub(
        " ", NON_ALNUM_PATTERN.sub(" ", safe_unicode(value))
    ).strip()


def experimental_suffix_stripped(value: object) -> str:
    """Return an intentionally aggressive form for collision experiments."""
    text = compact_safe(value)
    text = SUFFIX_PATTERN.sub(" ", text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def _read_ground_truth_sample(sample_size: int, seed: int) -> pd.DataFrame:
    """Read a deterministic sample of matched S1-to-S2/S3 relationships."""
    gt = pd.read_csv(
        TRAIN_GROUND_TRUTH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        usecols=["source1_entity_id", "matched_entity_ids"],
    )
    matched = gt[gt["matched_entity_ids"].str.len() > 0].copy()
    sampled = matched.sample(n=min(sample_size, len(matched)), random_state=seed)
    sampled["matched_id"] = sampled["matched_entity_ids"].str.split(",").str[0]
    return sampled[["source1_entity_id", "matched_id"]]


def _lookup_records(path: Path, ids: set[str], chunk_size: int) -> pd.DataFrame:
    """Look up selected IDs without retaining an entire source in memory."""
    records: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
    ):
        selected = chunk[chunk["entity_id"].isin(ids)]
        if not selected.empty:
            records.append(selected)
    if not records:
        return pd.DataFrame(columns=["entity_id", "business_name", "business_address"])
    return pd.concat(records, ignore_index=True)


def _pair_experiment(
    sample: pd.DataFrame, source1: pd.DataFrame, source2: pd.DataFrame
) -> dict[str, object]:
    """Measure exact agreement and missing-value behavior on true pairs."""
    left = sample.merge(source1, left_on="source1_entity_id", right_on="entity_id")
    right = sample.merge(source2, left_on="matched_id", right_on="entity_id")
    pairs = left[["source1_entity_id", "business_name", "business_address"]].merge(
        right[["source1_entity_id", "business_name", "business_address"]],
        on="source1_entity_id",
        suffixes=("_s1", "_matched"),
    )

    result: dict[str, object] = {"sampled_pairs": int(len(pairs))}
    for field in ("business_name", "business_address"):
        left_values = pairs[f"{field}_s1"]
        right_values = pairs[f"{field}_matched"]
        result[field] = {
            "raw_exact_rate": round(
                float((left_values == right_values).mean()), 6
            ),
            "safe_unicode_exact_rate": round(
                float(
                    (
                        left_values.map(safe_unicode)
                        == right_values.map(safe_unicode)
                    ).mean()
                ),
                6,
            ),
            "compact_exact_rate": round(
                float(
                    (
                        left_values.map(compact_safe)
                        == right_values.map(compact_safe)
                    ).mean()
                ),
                6,
            ),
            "experimental_exact_rate": round(
                float(
                    (
                        left_values.map(experimental_suffix_stripped)
                        == right_values.map(experimental_suffix_stripped)
                    ).mean()
                ),
                6,
            ),
            "left_empty": int((left_values == "").sum()),
            "right_empty": int((right_values == "").sum()),
        }
    return result


def _collision_stats(path: Path, field: str, chunk_size: int) -> dict[str, object]:
    """Measure representation collisions over an entire source column."""
    by_representation = {
        "raw": Counter(),
        "safe_unicode": Counter(),
        "compact": Counter(),
        "experimental": Counter(),
    }
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        usecols=[field],
        chunksize=chunk_size,
    ):
        values = chunk[field]
        if field == "business_name":
            safe_values = values.map(safe_unicode)
            compact_values = values.map(compact_safe)
            experimental_values = values.map(experimental_suffix_stripped)
        else:
            safe_values = values.map(safe_unicode)
            compact_values = values.map(compact_safe)
            experimental_values = compact_values
        for label, series in (
            ("raw", values),
            ("safe_unicode", safe_values),
            ("compact", compact_values),
            ("experimental", experimental_values),
        ):
            by_representation[label].update(series.tolist())

    stats: dict[str, object] = {}
    for label, counter in by_representation.items():
        nonempty = {key: count for key, count in counter.items() if key}
        duplicate_values = sum(count > 1 for count in nonempty.values())
        rows_in_duplicates = sum(
            count for count in nonempty.values() if count > 1
        )
        stats[label] = {
            "unique_nonempty_values": len(nonempty),
            "duplicate_values": duplicate_values,
            "rows_in_duplicate_values": rows_in_duplicates,
            "max_nonempty_bucket": max(nonempty.values(), default=0),
            "empty_rows": int(counter.get("", 0)),
        }
    return stats


def run_experiment(
    sample_size: int = 50_000, chunk_size: int = 100_000, seed: int = 42
) -> dict[str, object]:
    """Run the normalization experiment against the actual training files."""
    sample = _read_ground_truth_sample(sample_size, seed)
    s1_ids = set(sample["source1_entity_id"])
    s2_ids = {value for value in sample["matched_id"] if value.startswith("S2-")}
    s3_ids = {value for value in sample["matched_id"] if value.startswith("S3-")}
    s1 = _lookup_records(TRAIN_SOURCE1, s1_ids, chunk_size)
    s2 = _lookup_records(TRAIN_SOURCE2, s2_ids, chunk_size)
    s3 = _lookup_records(TRAIN_SOURCE3, s3_ids, chunk_size)
    matched = pd.concat([s2, s3], ignore_index=True)

    result = {
        "experiment": {
            "seed": seed,
            "requested_pairs": sample_size,
            "sampled_pairs": len(sample),
            "chunk_size": chunk_size,
            "source": "training data and training ground truth",
        },
        "true_pair_agreement": _pair_experiment(sample, s1, matched),
        "collision_stats": {
            "train_source1": {
                "business_name": _collision_stats(
                    TRAIN_SOURCE1, "business_name", chunk_size
                ),
                "business_address": _collision_stats(
                    TRAIN_SOURCE1, "business_address", chunk_size
                ),
            },
            "train_source2": {
                "business_name": _collision_stats(
                    TRAIN_SOURCE2, "business_name", chunk_size
                ),
                "business_address": _collision_stats(
                    TRAIN_SOURCE2, "business_address", chunk_size
                ),
            },
            "train_source3": {
                "business_name": _collision_stats(
                    TRAIN_SOURCE3, "business_name", chunk_size
                ),
                "business_address": _collision_stats(
                    TRAIN_SOURCE3, "business_address", chunk_size
                ),
            },
        },
        "representation_policy": {
            "raw": "Retain unchanged for auditability and final feature comparison.",
            "safe_unicode": (
                "Primary representation: NFKC, case-folded, whitespace-normalized; "
                "preserves Unicode letters and digits."
            ),
            "compact": (
                "Auxiliary punctuation-insensitive representation; not used alone "
                "when it creates oversized blocks."
            ),
            "experimental": (
                "Diagnostic only: removes common legal suffix tokens. Never use as "
                "the sole blocking or matching representation."
            ),
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-size", type=int, default=50_000)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "part2_normalization_results.json",
    )
    args = parser.parse_args()
    results = run_experiment(args.sample_size, args.chunk_size, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results["experiment"], indent=2))
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
