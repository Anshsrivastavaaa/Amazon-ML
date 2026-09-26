"""Part 3 blocking interfaces and exact-name baseline.

This module intentionally contains only the first blocking family: exact
normalized-name lookups, with country used as an experimental signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Iterable

import pandas as pd

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


def prepare_name_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Add Part 2 name representations without changing source columns."""
    prepared = frame.copy()
    prepared["name_clean_unicode"] = prepared["business_name"].map(safe_unicode)
    prepared["name_nopunct"] = prepared["business_name"].map(compact_safe)
    prepared["country_clean"] = prepared["country"].map(safe_unicode)
    return prepared


def _key(row: pd.Series, strategy: str) -> str | tuple[str, str]:
    if strategy == "name_only":
        return row["name_clean_unicode"]
    if strategy == "compact_name":
        return row["name_nopunct"]
    if strategy == "country_name":
        return (row["country_clean"], row["name_clean_unicode"])
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
            row_series = pd.Series(row._asdict())
            key = _key(row_series, strategy)
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
            row_series = pd.Series(row._asdict())
            key = _key(row_series, strategy)
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
