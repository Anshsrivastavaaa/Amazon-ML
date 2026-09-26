"""Part 3 blocking interfaces and exact-name baseline.

This module intentionally contains only the first blocking family: exact
normalized-name lookups, with country used as an experimental signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Iterable
import json
import os

import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    TRAIN_GROUND_TRUTH,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)
from src.part2_normalization import compact_safe, safe_unicode


@dataclass(frozen=True)
class BlockingConfig:
    """Runtime configuration for the exact-name blocking baseline."""

    chunk_size: int = 100_000
    max_block_size: int | None = None


@dataclass
class CandidateSet:
    """Per-S1 candidate IDs for one target source."""

    source1_to_candidates: dict[str, set[str]] = field(default_factory=dict)

    def add(self, source1_id: str, candidate_ids: Iterable[str]) -> None:
        self.source1_to_candidates.setdefault(source1_id, set()).update(
            candidate_ids
        )

    def counts(self) -> pd.Series:
        return pd.Series(
            {
                source1_id: len(candidate_ids)
                for source1_id, candidate_ids in self.source1_to_candidates.items()
            },
            dtype="int64",
        )


@dataclass
class BlockingRun:
    """Measured output from one blocking strategy."""

    strategy: str
    target_source: str
    candidates: CandidateSet
    elapsed_seconds: float


@dataclass(frozen=True)
class BlockingMetrics:
    """Recall and candidate-size metrics for one evaluated candidate set."""

    strategy: str
    target_source: str
    validation_entities: int
    true_pairs: int
    recovered_pairs: int
    pair_recall: float
    complete_entity_recall: float
    candidate_pairs: int
    average_candidates: float
    median_candidates: float
    p95_candidates: float
    p99_candidates: float
    maximum_candidates: int
    zero_candidate_entities: int
    reduction_ratio: float
    runtime_seconds: float
    process_rss_mb: float

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def prepare_name_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Add Part 2 name representations without changing source columns."""
    prepared = frame.copy()
    prepared["name_clean_unicode"] = prepared["business_name"].map(safe_unicode)
    prepared["name_nopunct"] = prepared["business_name"].map(compact_safe)
    prepared["country_clean"] = prepared["country"].map(safe_unicode)
    return prepared


def _key(row: object, strategy: str) -> str | tuple[str, str]:
    if strategy == "name_only":
        return row.name_clean_unicode
    if strategy == "compact_name":
        return row.name_nopunct
    if strategy == "country_name":
        return (row.country_clean, row.name_clean_unicode)
    raise ValueError(f"Unknown blocking strategy: {strategy}")


def build_exact_index(
    source_path: Path, strategy: str, config: BlockingConfig
) -> dict[str | tuple[str, str], list[str]]:
    """Build an exact-name inverted index from a target source in chunks."""
    index: dict[str | tuple[str, str], list[str]] = {}
    for chunk in pd.read_csv(
        source_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=config.chunk_size,
        usecols=["entity_id", "business_name", "country"],
    ):
        prepared = prepare_name_columns(chunk)
        for row in prepared.itertuples(index=False):
            key = _key(row, strategy)
            if (isinstance(key, str) and not key) or (
                isinstance(key, tuple) and not all(key)
            ):
                continue
            index.setdefault(key, []).append(row.entity_id)
    return index


def generate_exact_candidates(
    source1_path: Path,
    target_path: Path,
    target_source: str,
    strategy: str,
    config: BlockingConfig | None = None,
    source1_ids: set[str] | None = None,
) -> BlockingRun:
    """Generate candidates for one S1-to-target-source exact-key strategy."""
    config = config or BlockingConfig()
    started = perf_counter()
    index = build_exact_index(target_path, strategy, config)
    candidates = CandidateSet()
    for chunk in pd.read_csv(
        source1_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=config.chunk_size,
        usecols=["entity_id", "business_name", "country"],
    ):
        prepared = prepare_name_columns(chunk)
        for row in prepared.itertuples(index=False):
            if source1_ids is not None and row.entity_id not in source1_ids:
                continue
            key = _key(row, strategy)
            if (isinstance(key, str) and not key) or (
                isinstance(key, tuple) and not all(key)
            ):
                candidates.add(row.entity_id, ())
                continue
            candidate_ids = index.get(key, [])
            if config.max_block_size is not None:
                candidate_ids = candidate_ids[: config.max_block_size]
            candidates.add(row.entity_id, candidate_ids)
    return BlockingRun(
        strategy=strategy,
        target_source=target_source,
        candidates=candidates,
        elapsed_seconds=perf_counter() - started,
    )


def union_candidate_sets(*runs: BlockingRun) -> CandidateSet:
    """Union candidates from multiple passes for the same S1/target pair."""
    if not runs:
        return CandidateSet()
    target_sources = {run.target_source for run in runs}
    if len(target_sources) != 1:
        raise ValueError("Cannot union candidate runs from different target sources")
    merged = CandidateSet()
    for run in runs:
        for source1_id, candidate_ids in run.candidates.source1_to_candidates.items():
            merged.add(source1_id, candidate_ids)
    return merged


def load_ground_truth() -> dict[str, set[str]]:
    """Load training truth as S1-to-target ID sets."""
    ground_truth = pd.read_csv(
        TRAIN_GROUND_TRUTH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )
    return {
        row.source1_entity_id: {
            matched_id.strip()
            for matched_id in row.matched_entity_ids.split(",")
            if matched_id.strip()
        }
        for row in ground_truth.itertuples(index=False)
    }


def build_validation_ids(
    validation_fraction: float = 0.2, seed: int = 42
) -> set[str]:
    """Build a deterministic S1-level validation split by country and match bucket."""
    source1 = pd.read_csv(
        TRAIN_SOURCE1,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        usecols=["entity_id", "country"],
    )
    ground_truth = pd.read_csv(
        TRAIN_GROUND_TRUTH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )
    ground_truth["match_count"] = ground_truth["matched_entity_ids"].map(
        lambda value: 0 if not value else len(value.split(","))
    )
    ground_truth["match_bucket"] = ground_truth["match_count"].map(
        lambda value: "0" if value == 0 else ("1" if value == 1 else "2+")
    )
    rows = ground_truth.merge(
        source1, left_on="source1_entity_id", right_on="entity_id"
    )
    validation = (
        rows.groupby(["country", "match_bucket"], group_keys=False)
        .sample(frac=validation_fraction, random_state=seed)
    )
    return set(validation["source1_entity_id"])


def _process_rss_mb() -> float:
    """Return current process RSS when psutil is available."""
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        return float("nan")


def evaluate_run(
    run: BlockingRun,
    truth: dict[str, set[str]],
    target_prefix: str,
    source1_count: int,
    full_target_count: int,
    runtime_seconds: float | None = None,
) -> BlockingMetrics:
    """Measure candidate recall, distribution, reduction, and process memory."""
    validation_ids = set(run.candidates.source1_to_candidates)
    counts = run.candidates.counts().reindex(sorted(validation_ids), fill_value=0)
    target_truth = {
        source1_id: {
            matched_id for matched_id in truth.get(source1_id, set())
            if matched_id.startswith(target_prefix)
        }
        for source1_id in validation_ids
    }
    true_pairs = sum(len(ids) for ids in target_truth.values())
    recovered_pairs = sum(
        len(ids & run.candidates.source1_to_candidates[source1_id])
        for source1_id, ids in target_truth.items()
    )
    complete = sum(
        bool(ids) and ids.issubset(run.candidates.source1_to_candidates[source1_id])
        or not ids
        for source1_id, ids in target_truth.items()
    )
    candidate_pairs = int(counts.sum())
    full_pairs = source1_count * full_target_count
    return BlockingMetrics(
        strategy=run.strategy,
        target_source=run.target_source,
        validation_entities=len(validation_ids),
        true_pairs=true_pairs,
        recovered_pairs=recovered_pairs,
        pair_recall=recovered_pairs / true_pairs if true_pairs else 1.0,
        complete_entity_recall=complete / len(validation_ids)
        if validation_ids
        else 1.0,
        candidate_pairs=candidate_pairs,
        average_candidates=float(counts.mean()) if len(counts) else 0.0,
        median_candidates=float(counts.median()) if len(counts) else 0.0,
        p95_candidates=float(counts.quantile(0.95)) if len(counts) else 0.0,
        p99_candidates=float(counts.quantile(0.99)) if len(counts) else 0.0,
        maximum_candidates=int(counts.max()) if len(counts) else 0,
        zero_candidate_entities=int((counts == 0).sum()),
        reduction_ratio=1 - candidate_pairs / full_pairs if full_pairs else 0.0,
        runtime_seconds=(
            run.elapsed_seconds if runtime_seconds is None else runtime_seconds
        ),
        process_rss_mb=_process_rss_mb(),
    )


def run_baseline_evaluation(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, object]:
    """Evaluate name-only, country+name, and their union on one S1 split."""
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
    source1_count = len(validation_ids)
    source_paths = {"S2": TRAIN_SOURCE2, "S3": TRAIN_SOURCE3}
    target_counts = {
        source: sum(
            len(chunk)
            for chunk in pd.read_csv(
                path,
                sep="\t",
                dtype=str,
                keep_default_na=False,
                usecols=["entity_id"],
                chunksize=config.chunk_size,
            )
        )
        for source, path in source_paths.items()
    }
    metrics: list[dict[str, object]] = []
    for source, target_path in source_paths.items():
        runs = {
            strategy: generate_exact_candidates(
                TRAIN_SOURCE1,
                target_path,
                source,
                strategy,
                config,
                validation_ids,
            )
            for strategy in ("name_only", "compact_name", "country_name")
        }
        runs["name_country_union"] = BlockingRun(
            strategy="name_country_union",
            target_source=source,
            candidates=union_candidate_sets(runs["name_only"], runs["country_name"]),
            elapsed_seconds=(
                runs["name_only"].elapsed_seconds
                + runs["country_name"].elapsed_seconds
            ),
        )
        for strategy, run in runs.items():
            metrics.append(
                evaluate_run(
                    run,
                    truth,
                    source,
                    source1_count,
                    target_counts[source],
                ).as_dict()
            )
    return {
        "validation": {
            "fraction": validation_fraction,
            "seed": seed,
            "entities": source1_count,
            "split_unit": "source1_entity",
            "target_indexes_use_labels": False,
        },
        "config": config.__dict__,
        "metrics": metrics,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "part3_baseline_results.json",
    )
    args = parser.parse_args()
    results = run_baseline_evaluation(
        BlockingConfig(chunk_size=args.chunk_size),
        args.validation_fraction,
        args.seed,
    )
    args.output.write_text(
        json.dumps(results, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
