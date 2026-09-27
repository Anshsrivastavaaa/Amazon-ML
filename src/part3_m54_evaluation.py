"""M5.4.2 explicit M4 plus M5.2 candidate-union evaluation."""

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
    build_validation_ids,
    evaluate_run,
    load_ground_truth,
)
from src.part3_candidate_union import (
    measure_marginal_recovery,
    union_named_candidate_sets,
)
from src.part3_token_blocking import (
    build_token_frequencies,
    build_token_structures,
    generate_runs_from_structures,
)


THRESHOLD = 250
VALIDATION_FRACTION = 0.2
SEED = 42


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
        THRESHOLD,
        config,
        frequencies,
    )
    m4_runs = generate_runs_from_structures(
        source,
        "name_clean_unicode",
        THRESHOLD,
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

    stage_start = perf_counter()
    stage_cpu = _cpu_seconds()
    address_frequencies = build_address_token_frequencies(
        target_path, config
    )
    address_index = build_country_address_index(
        target_path,
        address_frequencies,
        THRESHOLD,
        config,
    )
    m52_run, availability = generate_candidates_from_validation_rows(
        source,
        address_index,
        address_frequencies,
        THRESHOLD,
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
    marginal = measure_marginal_recovery(
        m4_run,
        m52_run,
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
        ],
        "marginal_m4_to_union": marginal,
    }
    del m4_run, m52_run, union_run
    gc.collect()
    return results


def run() -> dict[str, object]:
    config = BlockingConfig()
    validation_ids = build_validation_ids(VALIDATION_FRACTION, SEED)
    truth = load_ground_truth()
    with PeakRSSMonitor() as monitor:
        sources = {
            source: _evaluate_source(source, path, config, validation_ids, truth)
            for source, path in (
                ("S2", TRAIN_SOURCE2),
                ("S3", TRAIN_SOURCE3),
            )
        }
    return {
        "checkpoint": "M5.4.2",
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
        },
        "sources": sources,
        "peak_rss_mb": monitor.peak_mb,
    }


def main() -> None:
    output = PROCESSED_DATA_DIR / "part3_m54_m4_m52_union_results.json"
    output.write_text(json.dumps(run(), indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
