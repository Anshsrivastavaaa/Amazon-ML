"""M4 rare-token and multi-token blocking experiments."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from time import perf_counter

import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)
from src.part2_normalization import compact_safe, safe_unicode
from src.part3_blocking import (
    BlockingConfig,
    BlockingRun,
    build_validation_ids,
    evaluate_run,
    load_ground_truth,
)


TOKEN_THRESHOLDS = (10, 25, 50, 100, 250)
TOKEN_REPRESENTATIONS = ("name_clean_unicode", "name_nopunct")


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(sorted(set(compact_safe(value).split())))


def _representation_tokens(value: str, representation: str) -> tuple[str, ...]:
    normalized = (
        safe_unicode(value)
        if representation == "name_clean_unicode"
        else compact_safe(value)
    )
    return tuple(sorted(set(normalized.split())))


def _target_rows(path: Path, chunk_size: int):
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
        usecols=["entity_id", "business_name", "country"],
    ):
        yield from chunk.itertuples(index=False)


def _source1_rows(path: Path, chunk_size: int):
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
        usecols=["entity_id", "business_name", "country"],
    ):
        yield from chunk.itertuples(index=False)


def build_token_frequencies(
    target_path: Path,
    representation: str,
    config: BlockingConfig,
) -> Counter[str]:
    frequencies: Counter[str] = Counter()
    for row in _target_rows(target_path, config.chunk_size):
        frequencies.update(
            _representation_tokens(row.business_name, representation)
        )
    return frequencies


def build_token_index(
    target_path: Path,
    representation: str,
    max_frequency: int,
    config: BlockingConfig,
    country_aware: bool = False,
) -> tuple[dict[str | tuple[str, str], list[str]], Counter[str]]:
    frequencies = build_token_frequencies(target_path, representation, config)
    index: dict[str | tuple[str, str], list[str]] = {}
    for row in _target_rows(target_path, config.chunk_size):
        country = safe_unicode(row.country)
        for token in _representation_tokens(row.business_name, representation):
            if frequencies[token] > max_frequency:
                continue
            key: str | tuple[str, str] = (
                (country, token) if country_aware else token
            )
            if country_aware and not country:
                continue
            index.setdefault(key, []).append(row.entity_id)
    return index, frequencies


def build_token_structures(
    target_path: Path,
    representation: str,
    max_frequency: int,
    config: BlockingConfig,
    frequencies: Counter[str],
) -> tuple[
    dict[str, list[str]],
    dict[tuple[str, str], list[str]],
    dict[tuple[str, str], list[str]],
]:
    token_index: dict[str, list[str]] = {}
    country_index: dict[tuple[str, str], list[str]] = {}
    signature_index: dict[tuple[str, str], list[str]] = {}
    for row in _target_rows(target_path, config.chunk_size):
        tokens = [
            token
            for token in _representation_tokens(row.business_name, representation)
            if frequencies[token] <= max_frequency
        ]
        tokens.sort(key=lambda token: (frequencies[token], token))
        country = safe_unicode(row.country)
        for token in tokens:
            token_index.setdefault(token, []).append(row.entity_id)
            if country:
                country_index.setdefault((country, token), []).append(
                    row.entity_id
                )
        if len(tokens) >= 2:
            signature_index.setdefault(tuple(sorted(tokens[:2])), []).append(
                row.entity_id
            )
    return token_index, country_index, signature_index


def generate_runs_from_structures(
    target_source: str,
    representation: str,
    threshold: int,
    frequencies: Counter[str],
    structures: tuple[
        dict[str, list[str]],
        dict[tuple[str, str], list[str]],
        dict[tuple[str, str], list[str]],
    ],
    source1_ids: set[str],
    config: BlockingConfig,
) -> list[BlockingRun]:
    started = perf_counter()
    token_index, country_index, signature_index = structures
    candidate_maps = [dict[str, set[str]]() for _ in range(4)]
    for row in _source1_rows(TRAIN_SOURCE1, config.chunk_size):
        if row.entity_id not in source1_ids:
            continue
        tokens = [
            token
            for token in _representation_tokens(row.business_name, representation)
            if frequencies[token] <= threshold
        ]
        tokens.sort(key=lambda token: (frequencies[token], token))
        if not tokens:
            for candidates in candidate_maps:
                candidates.setdefault(row.entity_id, set())
            continue
        for token in tokens:
            candidate_maps[0].setdefault(row.entity_id, set()).update(
                token_index.get(token, [])
            )
            candidate_maps[1].setdefault(row.entity_id, set()).update(
                country_index.get((safe_unicode(row.country), token), [])
            )
        if len(tokens) < 2:
            candidate_maps[2].setdefault(row.entity_id, set())
            candidate_maps[3].setdefault(row.entity_id, set())
            continue
        first, second = tokens[:2]
        candidate_maps[2][row.entity_id] = set(
            token_index.get(first, [])
        ) & set(token_index.get(second, []))
        candidate_maps[3][row.entity_id] = set(
            signature_index.get(tuple(sorted((first, second))), [])
        )
    elapsed = perf_counter() - started
    names = (
        f"rare_token_{representation}_freq{threshold}",
        f"country_rare_token_{representation}_freq{threshold}",
        f"multi_token_intersection_{representation}_freq{threshold}",
        f"multi_token_signature_{representation}_freq{threshold}",
    )
    from src.part3_blocking import CandidateSet

    return [
        BlockingRun(
            strategy=name,
            target_source=target_source,
            candidates=CandidateSet(candidate_map),
            elapsed_seconds=elapsed,
        )
        for name, candidate_map in zip(names, candidate_maps)
    ]


def _add_candidates(
    candidates: dict[str, set[str]],
    source1_id: str,
    values: list[str],
) -> None:
    candidates.setdefault(source1_id, set()).update(values)


def generate_rare_token_candidates(
    target_path: Path,
    target_source: str,
    representation: str,
    max_frequency: int,
    config: BlockingConfig,
    source1_ids: set[str],
    country_aware: bool,
) -> BlockingRun:
    started = perf_counter()
    index, frequencies = build_token_index(
        target_path,
        representation,
        max_frequency,
        config,
        country_aware,
    )
    candidates: dict[str, set[str]] = {}
    for row in _source1_rows(TRAIN_SOURCE1, config.chunk_size):
        if row.entity_id not in source1_ids:
            continue
        country = safe_unicode(row.country)
        for token in _representation_tokens(row.business_name, representation):
            if frequencies[token] > max_frequency:
                continue
            key: str | tuple[str, str] = (
                (country, token) if country_aware else token
            )
            _add_candidates(candidates, row.entity_id, index.get(key, []))
    from src.part3_blocking import CandidateSet

    return BlockingRun(
        strategy=(
            f"{'country_' if country_aware else ''}rare_token_"
            f"{representation}_freq{max_frequency}"
        ),
        target_source=target_source,
        candidates=CandidateSet(candidates),
        elapsed_seconds=perf_counter() - started,
    )


def generate_multi_token_candidates(
    target_path: Path,
    target_source: str,
    representation: str,
    max_frequency: int,
    config: BlockingConfig,
    source1_ids: set[str],
    mode: str,
) -> BlockingRun:
    started = perf_counter()
    index, frequencies = build_token_index(
        target_path, representation, max_frequency, config
    )
    signature_index = (
        _build_signature_index(
            target_path, representation, max_frequency, config
        )
        if mode == "signature"
        else {}
    )
    candidates: dict[str, set[str]] = {}
    for row in _source1_rows(TRAIN_SOURCE1, config.chunk_size):
        if row.entity_id not in source1_ids:
            continue
        tokens = [
            token
            for token in _representation_tokens(row.business_name, representation)
            if frequencies[token] <= max_frequency
        ]
        tokens.sort(key=lambda token: (frequencies[token], token))
        if len(tokens) < 2:
            candidates.setdefault(row.entity_id, set())
            continue
        first, second = tokens[:2]
        if mode == "intersection":
            first_ids = set(index.get(first, []))
            second_ids = set(index.get(second, []))
            values = list(first_ids & second_ids)
        elif mode == "signature":
            signature = tuple(sorted((first, second)))
            values = signature_index.get(signature, [])
        else:
            raise ValueError(f"Unknown multi-token mode: {mode}")
        _add_candidates(candidates, row.entity_id, values)
    from src.part3_blocking import CandidateSet

    return BlockingRun(
        strategy=(
            f"multi_token_{mode}_{representation}_freq{max_frequency}"
        ),
        target_source=target_source,
        candidates=CandidateSet(candidates),
        elapsed_seconds=perf_counter() - started,
    )


def _build_signature_index(
    target_path: Path,
    representation: str,
    max_frequency: int,
    config: BlockingConfig,
) -> dict[tuple[str, str], list[str]]:
    frequencies = build_token_frequencies(target_path, representation, config)
    index: dict[tuple[str, str], list[str]] = {}
    for row in _target_rows(target_path, config.chunk_size):
        tokens = [
            token
            for token in _representation_tokens(row.business_name, representation)
            if frequencies[token] <= max_frequency
        ]
        tokens.sort(key=lambda token: (frequencies[token], token))
        if len(tokens) >= 2:
            key = tuple(sorted(tokens[:2]))
            index.setdefault(key, []).append(row.entity_id)
    return index


def run_token_evaluation(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, object]:
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
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
    baseline = json.loads(
        (
            PROCESSED_DATA_DIR / "part3_baseline_results.json"
        ).read_text(encoding="utf-8")
    )
    error_analysis = json.loads(
        (
            PROCESSED_DATA_DIR / "part3_error_analysis_results.json"
        ).read_text(encoding="utf-8")
    )
    baseline_by_source = {
        source: {
            item["strategy"]: item
            for item in baseline["metrics"]
            if item["target_source"] == source
        }
        for source in source_paths
    }
    metrics: list[dict[str, object]] = []
    frequency_summaries: dict[str, object] = {}
    for source, target_path in source_paths.items():
        frequency_summaries[source] = {}
        for representation in TOKEN_REPRESENTATIONS:
            frequencies = build_token_frequencies(
                target_path, representation, config
            )
            frequency_summaries[source][representation] = {}
            for threshold in TOKEN_THRESHOLDS:
                structures = build_token_structures(
                    target_path,
                    representation,
                    threshold,
                    config,
                    frequencies,
                )
                runs = generate_runs_from_structures(
                    source,
                    representation,
                    threshold,
                    frequencies,
                    structures,
                    validation_ids,
                    config,
                )
                for run in runs:
                    measured = evaluate_run(
                        run,
                        truth,
                        source,
                        len(validation_ids),
                        target_counts[source],
                    ).as_dict()
                    baseline_metric = baseline_by_source[source]["compact_name"]
                    measured["baseline_pair_recall"] = baseline_metric["pair_recall"]
                    measured["incremental_pair_recall"] = (
                        measured["pair_recall"] - baseline_metric["pair_recall"]
                    )
                    measured["baseline_candidate_pairs"] = baseline_metric[
                        "candidate_pairs"
                    ]
                    measured["incremental_candidate_pairs"] = (
                        measured["candidate_pairs"]
                        - baseline_metric["candidate_pairs"]
                    )
                    category_totals: Counter[str] = Counter()
                    category_recovered: Counter[str] = Counter()
                    for evidence in error_analysis["sources"][source][
                        "missed_analysis"
                    ]["pair_evidence"]:
                        category = evidence["category"]
                        category_totals[category] += 1
                        candidate_ids = run.candidates.source1_to_candidates.get(
                            evidence["source1_entity_id"], set()
                        )
                        if evidence["matched_id"] in candidate_ids:
                            category_recovered[category] += 1
                    measured["m35_missed_category_recovery"] = {
                        category: {
                            "sampled_missed_pairs": count,
                            "recovered_pairs": category_recovered[category],
                            "recovery_rate": (
                                category_recovered[category] / count
                                if count
                                else 0.0
                            ),
                        }
                        for category, count in category_totals.items()
                    }
                    metrics.append(measured)
                frequency_summaries[source][representation][str(threshold)] = {
                    "tokens_at_or_below_threshold": int(
                        sum(
                            count <= threshold for count in frequencies.values()
                        )
                    ),
                    "total_distinct_tokens": len(frequencies),
                    "top_10_frequent_tokens": frequencies.most_common(10),
                }
    return {
        "method": {
            "validation_fraction": validation_fraction,
            "seed": seed,
            "strategies": [
                "rare_token",
                "country_rare_token",
                "multi_token_intersection",
                "multi_token_signature",
            ],
            "token_representations": list(TOKEN_REPRESENTATIONS),
            "frequency_thresholds": list(TOKEN_THRESHOLDS),
            "candidate_caps": False,
            "address_blocking_implemented": False,
            "parts_1_and_2_modified": False,
        },
        "validation": {"entities": len(validation_ids)},
        "frequency_summaries": frequency_summaries,
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "part3_token_results.json",
    )
    args = parser.parse_args()
    results = run_token_evaluation(
        BlockingConfig(chunk_size=args.chunk_size),
        args.validation_fraction,
        args.seed,
    )
    args.output.write_text(
        json.dumps(results, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "metrics": len(results["metrics"]),
                "sources": sorted(
                    {item["target_source"] for item in results["metrics"]}
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
