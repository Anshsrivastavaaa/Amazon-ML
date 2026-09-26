"""M5.2 country-aware informative address-token blocking experiments."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from time import perf_counter, process_time

import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)
from src.part2_normalization import safe_unicode
from src.part3_address import informative_address_tokens
from src.part3_blocking import (
    BlockingConfig,
    BlockingRun,
    CandidateSet,
    build_validation_ids,
    evaluate_run,
    load_ground_truth,
)


ADDRESS_TOKEN_THRESHOLDS = (5, 10, 25, 50, 100, 250)


class M52Profiler:
    """Phase timers and scan/recomputation counters for M5.2."""

    def __init__(self) -> None:
        self.started_wall = perf_counter()
        self.started_cpu = process_time()
        self.timings: Counter[str] = Counter()
        self.counts: Counter[str] = Counter()
        self.peak_rss_mb = 0.0

    def phase(self, name: str):
        return _ProfilePhase(self, name)

    def sample_rss(self) -> None:
        try:
            import psutil

            rss = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            self.peak_rss_mb = max(self.peak_rss_mb, rss)
        except ImportError:
            pass

    def as_dict(self) -> dict[str, object]:
        self.sample_rss()
        return {
            "wall_clock_seconds": perf_counter() - self.started_wall,
            "cpu_seconds": process_time() - self.started_cpu,
            "peak_rss_mb": self.peak_rss_mb,
            "phase_seconds": dict(self.timings),
            "operation_counts": dict(self.counts),
        }


class _ProfilePhase:
    def __init__(self, profiler: M52Profiler, name: str) -> None:
        self.profiler = profiler
        self.name = name

    def __enter__(self):
        self.started = perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.profiler.timings[self.name] += perf_counter() - self.started
        self.profiler.sample_rss()


def _rows(path: Path, config: BlockingConfig, profiler: M52Profiler | None = None):
    if profiler is not None:
        profiler.counts[f"full_scans:{path.name}"] += 1
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=config.chunk_size,
        usecols=["entity_id", "business_address", "country"],
    ):
        yield from chunk.itertuples(index=False)


def build_address_token_frequencies(
    target_path: Path,
    config: BlockingConfig,
    profiler: M52Profiler | None = None,
) -> Counter[str]:
    frequencies: Counter[str] = Counter()
    phase = profiler.phase("address_normalization_and_tokenization") if profiler else None
    if phase:
        phase.__enter__()
    try:
        for row in _rows(target_path, config, profiler):
            if profiler:
                profiler.counts["address_token_recomputations"] += 1
            frequencies.update(informative_address_tokens(row.business_address))
    finally:
        if phase:
            phase.__exit__(None, None, None)
    return frequencies


def build_country_address_index(
    target_path: Path,
    frequencies: Counter[str],
    max_frequency: int,
    config: BlockingConfig,
    profiler: M52Profiler | None = None,
) -> dict[tuple[str, str], list[str]]:
    index: dict[tuple[str, str], list[str]] = {}
    if profiler:
        profiler.counts["target_index_rebuilds"] += 1
    phase = profiler.phase("index_construction") if profiler else None
    if phase:
        phase.__enter__()
    try:
      for row in _rows(target_path, config, profiler):
        country = safe_unicode(row.country)
        if not country:
            continue
        if profiler:
            profiler.counts["address_token_recomputations"] += 1
        for token in informative_address_tokens(row.business_address):
            if frequencies[token] <= max_frequency:
                index.setdefault((country, token), []).append(row.entity_id)
    finally:
        if phase:
            phase.__exit__(None, None, None)
    return index


def address_block_distribution(
    index: dict[tuple[str, str], list[str]],
    frequencies: Counter[str],
    max_frequency: int,
) -> dict[str, object]:
    block_sizes = [len(values) for values in index.values()]
    series = pd.Series(block_sizes, dtype="int64")
    return {
        "distinct_tokens": len(frequencies),
        "tokens_at_or_below_threshold": int(
            sum(count <= max_frequency for count in frequencies.values())
        ),
        "indexed_country_token_blocks": len(block_sizes),
        "max_block_size": int(series.max()) if not series.empty else 0,
        "blocks_over_100": int((series > 100).sum()) if not series.empty else 0,
        "blocks_over_1000": int((series > 1000).sum()) if not series.empty else 0,
        "blocks_over_10000": int((series > 10000).sum())
        if not series.empty
        else 0,
        "block_size_p95": float(series.quantile(0.95))
        if not series.empty
        else 0.0,
        "block_size_p99": float(series.quantile(0.99))
        if not series.empty
        else 0.0,
    }


def generate_address_candidates(
    target_path: Path,
    target_source: str,
    frequencies: Counter[str],
    max_frequency: int,
    config: BlockingConfig,
    source1_ids: set[str],
    index: dict[tuple[str, str], list[str]] | None = None,
    profiler: M52Profiler | None = None,
) -> tuple[BlockingRun, dict[str, int]]:
    started = perf_counter()
    if index is None:
        index = build_country_address_index(
            target_path, frequencies, max_frequency, config
        )
    candidates: dict[str, set[str]] = {}
    source1_missing_address = 0
    source1_with_informative_token = 0
    if profiler:
        profiler.counts["source1_query_passes"] += 1
    phase = profiler.phase("candidate_retrieval_and_deduplication") if profiler else None
    if phase:
        phase.__enter__()
    try:
      for row in _rows(TRAIN_SOURCE1, config, profiler):
        if row.entity_id not in source1_ids:
            continue
        country = safe_unicode(row.country)
        if profiler:
            profiler.counts["address_token_recomputations"] += 1
        tokens = [
            token
            for token in informative_address_tokens(row.business_address)
            if frequencies[token] <= max_frequency
        ]
        if not safe_unicode(row.business_address):
            source1_missing_address += 1
        if tokens:
            source1_with_informative_token += 1
        values: set[str] = set()
        if country:
            for token in tokens:
                values.update(index.get((country, token), []))
        candidates[row.entity_id] = values
    finally:
        if phase:
            phase.__exit__(None, None, None)
    return (
        BlockingRun(
            strategy=f"country_address_token_freq{max_frequency}",
            target_source=target_source,
            candidates=CandidateSet(candidates),
            elapsed_seconds=perf_counter() - started,
        ),
        {
            "validation_entities_without_address": source1_missing_address,
            "validation_entities_with_informative_token": (
                source1_with_informative_token
            ),
        },
    )


def _m4_missed_recovery(
    source: str,
    target_path: Path,
    validation_ids: set[str],
    truth: dict[str, set[str]],
    config: BlockingConfig,
    profiler: M52Profiler | None = None,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    from src.part3_token_blocking import (
        build_token_frequencies,
        build_token_structures,
        generate_runs_from_structures,
    )

    if profiler:
        profiler.counts["m4_missed_recovery_runs"] += 1
    frequencies = build_token_frequencies(target_path, "name_clean_unicode", config)
    structures = build_token_structures(
        target_path, "name_clean_unicode", 250, config, frequencies
    )
    m4_run = generate_runs_from_structures(
        source,
        "name_clean_unicode",
        250,
        frequencies,
        structures,
        validation_ids,
        config,
    )[1]
    missed: set[tuple[str, str]] = set()
    for source1_id in validation_ids:
        candidates = m4_run.candidates.source1_to_candidates.get(
            source1_id, set()
        )
        for matched_id in truth.get(source1_id, set()):
            if matched_id.startswith(source) and matched_id not in candidates:
                missed.add((source1_id, matched_id))
    return missed, set()


def run_address_token_evaluation(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
    profiler: M52Profiler | None = None,
) -> dict[str, object]:
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
    target_paths = {"S2": TRAIN_SOURCE2, "S3": TRAIN_SOURCE3}
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
        for source, path in target_paths.items()
    }
    m4_results = json.loads(
        (PROCESSED_DATA_DIR / "part3_token_results.json").read_text(
            encoding="utf-8"
        )
    )
    m4_metrics = {
        source: next(
            item
            for item in m4_results["metrics"]
            if item["target_source"] == source
            and item["strategy"]
            == "country_rare_token_name_clean_unicode_freq250"
        )
        for source in target_paths
    }
    metrics: list[dict[str, object]] = []
    distributions: dict[str, object] = {}
    for source, target_path in target_paths.items():
        frequencies = build_address_token_frequencies(target_path, config, profiler)
        distributions[source] = {}
        m4_missed, _ = _m4_missed_recovery(
            source, target_path, validation_ids, truth, config, profiler
        )
        for threshold in ADDRESS_TOKEN_THRESHOLDS:
            index = build_country_address_index(
                target_path, frequencies, threshold, config, profiler
            )
            run, availability = generate_address_candidates(
                target_path,
                source,
                frequencies,
                threshold,
                config,
                validation_ids,
                index,
                profiler,
            )
            measured = evaluate_run(
                run,
                truth,
                source,
                len(validation_ids),
                target_counts[source],
            ).as_dict()
            m4_metric = m4_metrics[source]
            address_recovered_m4_misses = sum(
                matched_id
                in run.candidates.source1_to_candidates.get(source1_id, set())
                for source1_id, matched_id in m4_missed
            )
            measured.update(
                {
                    "m4_pair_recall": m4_metric["pair_recall"],
                    "incremental_pair_recall_over_m4": (
                        measured["pair_recall"] - m4_metric["pair_recall"]
                    ),
                    "m4_candidate_pairs": m4_metric["candidate_pairs"],
                    "incremental_candidate_pairs_over_m4": (
                        measured["candidate_pairs"]
                        - m4_metric["candidate_pairs"]
                    ),
                    "m4_missed_true_pairs": len(m4_missed),
                    "address_recovered_m4_misses": (
                        address_recovered_m4_misses
                    ),
                    "address_recovery_rate_of_m4_misses": (
                        address_recovered_m4_misses / len(m4_missed)
                        if m4_missed
                        else 0.0
                    ),
                    **availability,
                }
            )
            metrics.append(measured)
            distributions[source][str(threshold)] = (
                address_block_distribution(index, frequencies, threshold)
            )
    return {
        "method": {
            "validation_fraction": validation_fraction,
            "seed": seed,
            "thresholds": list(ADDRESS_TOKEN_THRESHOLDS),
            "strategy": "country-aware informative address token",
            "empty_values_are_universal_keys": False,
            "candidate_caps": False,
            "uses_postal_or_address_numbers": False,
            "uses_name_address_combination": False,
        },
        "validation": {"entities": len(validation_ids)},
        "metrics": metrics,
        "block_distributions": distributions,
        "profiling": profiler.as_dict() if profiler else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "part3_address_token_results.json",
    )
    args = parser.parse_args()
    profiler = M52Profiler()
    results = run_address_token_evaluation(
        BlockingConfig(chunk_size=args.chunk_size),
        args.validation_fraction,
        args.seed,
        profiler,
    )
    args.output.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"metrics": len(results["metrics"]), "sources": ["S2", "S3"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
