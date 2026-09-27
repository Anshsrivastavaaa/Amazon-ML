"""M5.4 cumulative candidate-union evaluation."""

from __future__ import annotations

import gc
import json
import os
import threading
from pathlib import Path
from time import perf_counter

import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)
from src.part3_address_blocking import (
    build_address_token_frequencies,
    build_country_address_index,
    generate_candidates_from_validation_rows,
    load_validation_address_rows,
)
from src.part3_blocking import (
    BlockingConfig,
    BlockingRun,
    CandidateSet,
    build_validation_ids,
    evaluate_run,
    load_ground_truth,
)
from src.part3_candidate_union import (
    measure_marginal_recovery,
    union_named_candidate_sets,
)
from src.part3_candidate_persistence import persist_candidate_run
from src.part3_signal_blocking import build_signal_index
from src.part3_signal_evaluation import (
    generate_signal_combination_run,
    generate_signal_run,
    load_validation_signal_rows,
)
from src.part3_token_blocking import (
    build_token_frequencies,
    build_token_structures,
    generate_runs_from_structures,
)


BASE_THRESHOLD = 250
THRESHOLD = int(os.environ.get("M553_THRESHOLD", "250"))
VALIDATION_FRACTION = 0.2
SEED = 42
PERSIST_ROOT = os.environ.get("M56_PERSIST_ROOT")
PERSIST_ONLY = os.environ.get("M56_PERSIST_ONLY") == "1"
PERSIST_TARGET = os.environ.get("M56_TARGET_SOURCE")


class PeakRSSMonitor:
    def __init__(self) -> None:
        self.peak_mb = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        try:
            import psutil

            process = psutil.Process(os.getpid())
            while not self._stop.is_set():
                self.peak_mb = max(
                    self.peak_mb,
                    process.memory_info().rss / (1024 * 1024),
                )
                self._stop.wait(0.25)
        except ImportError:
            return

    def __enter__(self) -> "PeakRSSMonitor":
        self._thread.start()
        return self

    def __exit__(
        self,
        _exc_type: object,
        _exc_value: object,
        _traceback: object,
    ) -> None:
        del _exc_type, _exc_value, _traceback
        self._stop.set()
        self._thread.join()


def _target_count(path: Path, config: BlockingConfig) -> int:
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


def _cpu_seconds() -> float:
    import psutil

    times = psutil.Process(os.getpid()).cpu_times()
    return times.user + times.system


def _metric(
    run: BlockingRun,
    truth: dict[str, set[str]],
    source: str,
    validation_ids: set[str],
    target_count: int,
    runtime: float,
) -> dict[str, object]:
    measured = evaluate_run(
        BlockingRun(
            strategy=run.strategy,
            target_source=run.target_source,
            candidates=run.candidates,
            elapsed_seconds=runtime,
        ),
        truth,
        source,
        len(validation_ids),
        target_count,
    ).as_dict()
    measured["runtime_seconds"] = runtime
    return measured


def _evaluate_source(
    source: str,
    target_path: Path,
    config: BlockingConfig,
    validation_ids: set[str],
    truth: dict[str, set[str]],
) -> dict[str, object]:
    target_count = _target_count(target_path, config)
    validation_rows = load_validation_address_rows(
        config, validation_ids
    )

    stage_start = perf_counter()
    stage_cpu = _cpu_seconds()
    frequencies = build_token_frequencies(
        target_path, "name_clean_unicode", config
    )
    structures = build_token_structures(
        target_path,
        "name_clean_unicode",
        BASE_THRESHOLD,
        config,
        frequencies,
    )
    m4_runs = generate_runs_from_structures(
        source,
        "name_clean_unicode",
        BASE_THRESHOLD,
        frequencies,
        structures,
        validation_ids,
        config,
    )
    m4_run = next(
        run
        for run in m4_runs
        if run.strategy == "country_rare_token_name_clean_unicode_freq250"
    )
    m4_runtime = perf_counter() - stage_start
    m4_cpu = _cpu_seconds() - stage_cpu
    del m4_runs, structures, frequencies
    gc.collect()
    if PERSIST_ROOT:
        persist_candidate_run(
            m4_run, validation_ids, Path(PERSIST_ROOT), "m4", BASE_THRESHOLD
        )

    stage_start = perf_counter()
    stage_cpu = _cpu_seconds()
    address_frequencies = build_address_token_frequencies(
        target_path, config
    )
    address_index = build_country_address_index(
        target_path,
        address_frequencies,
        BASE_THRESHOLD,
        config,
    )
    m52_run, availability = generate_candidates_from_validation_rows(
        source,
        address_index,
        address_frequencies,
        BASE_THRESHOLD,
        validation_rows,
    )
    m52_runtime = perf_counter() - stage_start
    m52_cpu = _cpu_seconds() - stage_cpu
    block_sizes = [len(values) for values in address_index.values()]
    m52_availability = availability
    del address_index, address_frequencies, validation_rows
    gc.collect()

    union_run = union_named_candidate_sets(
        [("m4", m4_run), ("m52", m52_run)],
        "m4_union_m52",
    )
    if PERSIST_ROOT:
        persist_candidate_run(
            union_run,
            validation_ids,
            Path(PERSIST_ROOT),
            "m4_union_m52",
            BASE_THRESHOLD,
        )
    marginal = measure_marginal_recovery(
        m4_run,
        m52_run,
        truth,
        source,
        validation_ids,
    ).as_dict()
    stage_start = perf_counter()
    stage_cpu = _cpu_seconds()
    number_index = build_signal_index(
        target_path,
        "number",
        config,
        country_aware=True,
    )
    number_rows = load_validation_signal_rows(
        TRAIN_SOURCE1,
        validation_ids,
        config,
    )
    m533_run, m533_availability = generate_signal_run(
        source,
        f"country_number_freq{THRESHOLD}",
        number_index,
        number_rows,
        "number",
        True,
        max_frequency=THRESHOLD,
    )
    m533_runtime = perf_counter() - stage_start
    m533_cpu = _cpu_seconds() - stage_cpu
    number_block_sizes = [
        len(values)
        for key, values in number_index.blocks.items()
        if number_index.frequencies[
            key[1] if isinstance(key, tuple) else key
        ] <= THRESHOLD
    ]
    cumulative_run = union_named_candidate_sets(
        [("m4_union_m52", union_run), ("m5.3.3", m533_run)],
        "m4_union_m52_union_m5.3.3",
    )
    if PERSIST_ROOT:
        persist_candidate_run(
            cumulative_run,
            validation_ids,
            Path(PERSIST_ROOT),
            f"m4_union_m52_union_m533_{THRESHOLD}",
            THRESHOLD,
        )
    cumulative_marginal = measure_marginal_recovery(
        union_run,
        m533_run,
        truth,
        source,
        validation_ids,
    ).as_dict()
    if PERSIST_ONLY:
        m534_run = BlockingRun(
            strategy=f"country_postal_number_freq{THRESHOLD}",
            target_source=source,
            candidates=CandidateSet(
                {source1_id: set() for source1_id in validation_ids}
            ),
            elapsed_seconds=0.0,
        )
        m534_availability: dict[str, int] = {}
        m534_runtime = 0.0
        m534_cpu = 0.0
        postal_block_sizes: list[int] = []
        postal_index = None
        cumulative_m534_run = cumulative_run
        m534_marginal = {
            "previous_strategy": cumulative_run.strategy,
            "added_strategy": m534_run.strategy,
            "new_recovered_pairs": 0,
            "new_complete_entities": 0,
            "candidate_pairs_before": 0,
            "candidate_pairs_after": 0,
            "marginal_candidate_pairs": 0,
            "marginal_pair_recall": 0.0,
            "marginal_candidate_cost": None,
            "previously_missed_pairs": 0,
            "percentage_of_previous_misses_recovered": 0.0,
        }
    else:
        stage_start = perf_counter()
        stage_cpu = _cpu_seconds()
        postal_index = build_signal_index(
            target_path,
            "postal",
            config,
            country_aware=True,
        )
        m534_run, m534_availability = generate_signal_combination_run(
            source,
            f"country_postal_number_freq{THRESHOLD}",
            {"postal": postal_index, "number": number_index},
            number_rows,
            ("postal", "number"),
            True,
            max_frequencies={"postal": THRESHOLD, "number": THRESHOLD},
            combine="intersection",
        )
        m534_runtime = perf_counter() - stage_start
        m534_cpu = _cpu_seconds() - stage_cpu
        postal_block_sizes = [
            len(values)
            for key, values in postal_index.blocks.items()
            if postal_index.frequencies[
                key[1] if isinstance(key, tuple) else key
            ] <= THRESHOLD
        ]
        cumulative_m534_run = union_named_candidate_sets(
            [
                ("m4_union_m52_union_m5.3.3", cumulative_run),
                ("m5.3.4", m534_run),
            ],
            "m4_union_m52_union_m5.3.3_union_m5.3.4",
        )
        m534_marginal = measure_marginal_recovery(
            cumulative_run,
            m534_run,
            truth,
            source,
            validation_ids,
        ).as_dict()
    results = {
        "target_source": source,
        "strategies": [
            {
                "strategy": "m4_country_rare_token_name_clean_unicode_freq250",
                "metric": _metric(
                    m4_run,
                    truth,
                    source,
                    validation_ids,
                    target_count,
                    m4_runtime,
                ),
                "cpu_seconds": m4_cpu,
            },
            {
                "strategy": "m5.2_country_address_token_freq250",
                "metric": _metric(
                    m52_run,
                    truth,
                    source,
                    validation_ids,
                    target_count,
                    m52_runtime,
                ),
                "cpu_seconds": m52_cpu,
                "availability": m52_availability,
                "block_statistics": {
                    "indexed_blocks": len(block_sizes),
                    "max_block_size": max(block_sizes, default=0),
                    "blocks_over_100": sum(size > 100 for size in block_sizes),
                    "blocks_over_1000": sum(size > 1000 for size in block_sizes),
                    "blocks_over_10000": sum(
                        size > 10000 for size in block_sizes
                    ),
                },
            },
            {
                "strategy": "m4_union_m52",
                "metric": _metric(
                    union_run,
                    truth,
                    source,
                    validation_ids,
                    target_count,
                    m4_runtime + m52_runtime,
                ),
                "cpu_seconds": m4_cpu + m52_cpu,
            },
            {
                "strategy": "m4_union_m52_union_m5.3.3",
                "metric": _metric(
                    cumulative_run,
                    truth,
                    source,
                    validation_ids,
                    target_count,
                    m4_runtime + m52_runtime + m533_runtime,
                ),
                "cpu_seconds": m4_cpu + m52_cpu + m533_cpu,
            },
            {
                "strategy": "m4_union_m52_union_m5.3.3_union_m5.3.4",
                "metric": _metric(
                    cumulative_m534_run,
                    truth,
                    source,
                    validation_ids,
                    target_count,
                    m4_runtime + m52_runtime + m533_runtime + m534_runtime,
                ),
                "cpu_seconds": m4_cpu + m52_cpu + m533_cpu + m534_cpu,
            },
        ],
        "marginal_m4_to_union": marginal,
        "marginal_union_to_m533": cumulative_marginal,
        "marginal_union_m533_to_m534": m534_marginal,
        "m533": {
            "strategy": f"country_number_freq{THRESHOLD}",
            "availability": m533_availability,
            "block_statistics": {
                "indexed_blocks_at_threshold": len(number_block_sizes),
                "max_block_size": max(number_block_sizes, default=0),
                "blocks_over_100": sum(
                    size > 100 for size in number_block_sizes
                ),
                "blocks_over_1000": sum(
                    size > 1000 for size in number_block_sizes
                ),
                "blocks_over_10000": sum(
                    size > 10000 for size in number_block_sizes
                ),
            },
            "runtime_seconds": m533_runtime,
            "cpu_seconds": m533_cpu,
            "extraction": number_index.stats.as_dict(),
        },
        "m534": {
            "strategy": f"country_postal_number_freq{THRESHOLD}",
            "semantics": "country-aware postal/number intersection",
            "availability": m534_availability,
            "block_statistics": {
                "postal_indexed_blocks_at_threshold": len(
                    postal_block_sizes
                ),
                "postal_max_block_size": max(postal_block_sizes, default=0),
                "postal_blocks_over_100": sum(
                    size > 100 for size in postal_block_sizes
                ),
                "postal_blocks_over_1000": sum(
                    size > 1000 for size in postal_block_sizes
                ),
                "number_indexed_blocks_at_threshold": len(number_block_sizes),
                "number_max_block_size": max(number_block_sizes, default=0),
                "number_blocks_over_100": sum(
                    size > 100 for size in number_block_sizes
                ),
                "number_blocks_over_1000": sum(
                    size > 1000 for size in number_block_sizes
                ),
            },
            "runtime_seconds": m534_runtime,
            "cpu_seconds": m534_cpu,
            "postal_extraction": (
                postal_index.stats.as_dict() if postal_index is not None else {}
            ),
            "number_extraction": number_index.stats.as_dict(),
        },
    }
    del m4_run, m52_run, union_run, m533_run, cumulative_run
    del m534_run, cumulative_m534_run, postal_index, number_index, number_rows
    gc.collect()
    return results


def run() -> dict[str, object]:
    config = BlockingConfig()
    validation_ids = build_validation_ids(VALIDATION_FRACTION, SEED)
    truth = load_ground_truth()
    with PeakRSSMonitor() as monitor:
        source_paths = (("S2", TRAIN_SOURCE2), ("S3", TRAIN_SOURCE3))
        if PERSIST_TARGET:
            source_paths = tuple(
                item for item in source_paths if item[0] == PERSIST_TARGET
            )
            if not source_paths:
                raise ValueError(f"Unknown persistence target: {PERSIST_TARGET}")
        sources = {
            source: _evaluate_source(source, path, config, validation_ids, truth)
            for source, path in source_paths
        }
    return {
        "checkpoint": "M5.5.3-threshold",
        "validation": {
            "fraction": VALIDATION_FRACTION,
            "seed": SEED,
            "entities": len(validation_ids),
            "split_unit": "source1_entity",
            "target_indexes_use_labels": False,
        },
        "config": config.__dict__,
        "threshold": THRESHOLD,
        "semantics": {
            "union": "explicit per-S1 candidate ID set union",
            "ground_truth_used_for_candidate_construction": False,
            "m4_strategy": "country-aware rare-token name_clean_unicode",
            "m52_strategy": "country-aware informative address token",
            "m533_strategy": "country-aware address number",
            "m534_strategy": (
                "country-aware postal and number intersection"
            ),
            "base_threshold": BASE_THRESHOLD,
        },
        "sources": sources,
        "peak_rss_mb": monitor.peak_mb,
    }


def main() -> None:
    output_name = os.environ.get(
        "M553_OUTPUT",
        "part3_m54_m4_m52_m533_m534_union_results.json",
    )
    output = PROCESSED_DATA_DIR / output_name
    output.write_text(json.dumps(run(), indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
