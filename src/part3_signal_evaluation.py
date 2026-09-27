"""Evaluation helpers for postal and address-number blocking signals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd

from src.part2_normalization import safe_unicode
from src.part3_address import parse_address
from src.part3_blocking import (
    BlockingConfig,
    BlockingRun,
    CandidateSet,
    build_validation_ids,
    evaluate_run,
    load_ground_truth,
)
from src.part3_signal_blocking import (
    SignalIndex,
    build_signal_index,
    lookup_signals,
    without_country,
)
from src.config import TRAIN_SOURCE1, TRAIN_SOURCE2, TRAIN_SOURCE3


@dataclass(frozen=True)
class ValidationSignalRow:
    source1_id: str
    country: str
    address: str
    postal: tuple[str, ...]
    number: tuple[str, ...]
    has_address: bool


def load_validation_signal_rows(
    source1_path: Path,
    validation_ids: set[str],
    config: BlockingConfig,
) -> list[ValidationSignalRow]:
    rows: list[ValidationSignalRow] = []
    for chunk in pd.read_csv(
        source1_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=config.chunk_size,
        usecols=["entity_id", "business_address", "country"],
    ):
        for row in chunk.itertuples(index=False):
            if row.entity_id not in validation_ids:
                continue
            parsed = parse_address(row.business_address)
            rows.append(
                ValidationSignalRow(
                    source1_id=row.entity_id,
                    country=safe_unicode(row.country),
                    address=parsed.address_clean,
                    postal=parsed.postal_candidates,
                    number=parsed.numbers,
                    has_address=bool(parsed.address_clean),
                )
            )
    return rows


def generate_signal_run(
    target_source: str,
    strategy: str,
    index: SignalIndex,
    rows: list[ValidationSignalRow],
    signal_name: str,
    country_aware: bool,
    max_frequency: int | None = None,
) -> tuple[BlockingRun, dict[str, int]]:
    started = perf_counter()
    candidates: dict[str, set[str]] = {}
    missing = 0
    with_signal = 0
    for row in rows:
        if not row.has_address:
            missing += 1
        signals = tuple(
            signal
            for signal in getattr(row, signal_name)
            if max_frequency is None
            or index.frequencies.get(signal, 0) <= max_frequency
        )
        if signals:
            with_signal += 1
        country = row.country if country_aware else ""
        candidates[row.source1_id] = lookup_signals(index, signals, country)
    return (
        BlockingRun(
            strategy=strategy,
            target_source=target_source,
            candidates=CandidateSet(candidates),
            elapsed_seconds=perf_counter() - started,
        ),
        {
            "validation_entities_without_address": missing,
            f"validation_entities_with_{signal_name}": with_signal,
        },
    )


def generate_signal_combination_run(
    target_source: str,
    strategy: str,
    indexes: dict[str, SignalIndex],
    rows: list[ValidationSignalRow],
    signal_names: tuple[str, ...],
    country_aware: bool,
    max_frequencies: dict[str, int | None] | None = None,
    combine: str = "intersection",
) -> tuple[BlockingRun, dict[str, int]]:
    """Generate candidates by combining reusable signal-family indexes."""
    if not signal_names:
        raise ValueError("At least one signal family is required")
    if combine not in {"intersection", "union"}:
        raise ValueError(f"Unknown signal combination: {combine}")
    if any(name not in indexes for name in signal_names):
        raise ValueError("Missing signal index for combination")

    started = perf_counter()
    candidates: dict[str, set[str]] = {}
    availability: dict[str, int] = {
        "validation_entities_without_address": sum(
            not row.has_address for row in rows
        )
    }
    for name in signal_names:
        availability[f"validation_entities_with_{name}"] = 0

    for row in rows:
        country = row.country if country_aware else ""
        per_signal: list[set[str]] = []
        for name in signal_names:
            index = indexes[name]
            max_frequency = (
                max_frequencies.get(name)
                if max_frequencies is not None
                else None
            )
            signals = tuple(
                signal
                for signal in getattr(row, name)
                if max_frequency is None
                or index.frequencies.get(signal, 0) <= max_frequency
            )
            if signals:
                availability[f"validation_entities_with_{name}"] += 1
            per_signal.append(lookup_signals(index, signals, country))

        if combine == "intersection":
            candidate_ids = set.intersection(*per_signal)
        else:
            candidate_ids = set.union(*per_signal)
        candidates[row.source1_id] = candidate_ids

    return (
        BlockingRun(
            strategy=strategy,
            target_source=target_source,
            candidates=CandidateSet(candidates),
            elapsed_seconds=perf_counter() - started,
        ),
        availability,
    )


def _row_count(path: Path, config: BlockingConfig) -> int:
    return sum(
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


def run_postal_evaluation(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, object]:
    """Evaluate postal-only and country+postal blocking on both targets."""
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
    rows = load_validation_signal_rows(TRAIN_SOURCE1, validation_ids, config)
    metrics: list[dict[str, object]] = []
    extraction: dict[str, object] = {
        "S1": {
            "rows": len(rows),
            "rows_with_address": sum(row.has_address for row in rows),
            "rows_with_postal": sum(bool(row.postal) for row in rows),
            "rows_with_multiple_postal": sum(len(row.postal) > 1 for row in rows),
        }
    }
    for source, target_path in {"S2": TRAIN_SOURCE2, "S3": TRAIN_SOURCE3}.items():
        country_index = build_signal_index(
            target_path, "postal", config, country_aware=True
        )
        unconstrained = without_country(country_index)
        extraction[source] = country_index.stats.as_dict()
        for strategy, index, country_aware in (
            ("postal", unconstrained, False),
            ("country_postal", country_index, True),
        ):
            run, availability = generate_signal_run(
                source,
                strategy,
                index,
                rows,
                "postal",
                country_aware,
            )
            metric = evaluate_run(
                run,
                truth,
                source,
                len(validation_ids),
                _row_count(target_path, config),
            ).as_dict()
            metric["availability"] = availability
            metric["block_statistics"] = {
                "indexed_blocks": len(index.blocks),
                "max_block_size": max(index.block_sizes(), default=0),
                "blocks_over_100": sum(size > 100 for size in index.block_sizes()),
                "blocks_over_1000": sum(
                    size > 1000 for size in index.block_sizes()
                ),
                "blocks_over_10000": sum(
                    size > 10000 for size in index.block_sizes()
                ),
            }
            metrics.append(metric)
    return {
        "validation": {
            "fraction": validation_fraction,
            "seed": seed,
            "entities": len(validation_ids),
            "split_unit": "source1_entity",
            "target_indexes_use_labels": False,
        },
        "config": config.__dict__,
        "strategies": ["postal", "country_postal"],
        "extraction": extraction,
        "metrics": metrics,
    }


def run_number_evaluation(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, object]:
    """Evaluate number-only and country+number blocking on both targets."""
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
    rows = load_validation_signal_rows(TRAIN_SOURCE1, validation_ids, config)
    metrics: list[dict[str, object]] = []
    thresholds = (5, 10, 25, 50, 100, 250)
    extraction: dict[str, object] = {
        "S1": {
            "rows": len(rows),
            "rows_with_address": sum(row.has_address for row in rows),
            "rows_with_number": sum(bool(row.number) for row in rows),
            "rows_with_multiple_number": sum(len(row.number) > 1 for row in rows),
        }
    }
    for source, target_path in {"S2": TRAIN_SOURCE2, "S3": TRAIN_SOURCE3}.items():
        country_index = build_signal_index(
            target_path, "number", config, country_aware=True
        )
        unconstrained = without_country(country_index)
        extraction[source] = country_index.stats.as_dict()
        for threshold in thresholds:
            for strategy, index, country_aware in (
                ("number", unconstrained, False),
                ("country_number", country_index, True),
            ):
                run, availability = generate_signal_run(
                    source,
                    f"{strategy}_freq{threshold}",
                    index,
                    rows,
                    "number",
                    country_aware,
                    max_frequency=threshold,
                )
                metric = evaluate_run(
                    run,
                    truth,
                    source,
                    len(validation_ids),
                    _row_count(target_path, config),
                ).as_dict()
                metric["frequency_threshold"] = threshold
                metric["availability"] = availability
                sizes = [
                    size
                    for key, size in (
                        (key, len(values)) for key, values in index.blocks.items()
                    )
                    if index.frequencies[
                        key[1] if isinstance(key, tuple) else key
                    ] <= threshold
                ]
                metric["block_statistics"] = {
                    "indexed_blocks": len(sizes),
                    "max_block_size": max(sizes, default=0),
                    "blocks_over_100": sum(size > 100 for size in sizes),
                    "blocks_over_1000": sum(size > 1000 for size in sizes),
                    "blocks_over_10000": sum(size > 10000 for size in sizes),
                }
                metrics.append(metric)
    return {
        "validation": {
            "fraction": validation_fraction,
            "seed": seed,
            "entities": len(validation_ids),
            "split_unit": "source1_entity",
            "target_indexes_use_labels": False,
        },
        "config": config.__dict__,
        "strategies": ["number", "country_number"],
        "frequency_thresholds": list(thresholds),
        "extraction": extraction,
        "metrics": metrics,
    }
