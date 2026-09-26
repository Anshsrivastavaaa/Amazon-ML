"""Diagnostic analysis of recall gaps from the Part 3 compact-name baseline."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd
from rapidfuzz.distance import Levenshtein

from src.config import (
    PROCESSED_DATA_DIR,
    TRAIN_SOURCE1,
    TRAIN_SOURCE2,
    TRAIN_SOURCE3,
)
from src.part2_normalization import (
    compact_safe,
    experimental_suffix_stripped,
    safe_unicode,
)
from src.part3_blocking import (
    BlockingConfig,
    build_validation_ids,
    generate_exact_candidates,
    load_ground_truth,
)


SAMPLE_SIZE = 10_000
DIAGNOSTIC_SEED = 20260927
CATEGORY_NAMES = (
    "exact_normalized_name_mismatch",
    "word_order_change",
    "additional_or_missing_tokens",
    "legal_suffix_variation",
    "abbreviation_variation",
    "typo_or_spelling_variation",
    "partial_or_truncated_name",
    "transliteration_or_unicode_variation",
    "very_short_name",
    "weak_name_address_informative",
    "missing_or_empty_address",
    "other_or_unknown",
)

TOKEN_RE = re.compile(r"\S+")


def _tokens(value: str) -> list[str]:
    return TOKEN_RE.findall(compact_safe(value))


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set, right_set = set(left), set(right)
    if not left_set and not right_set:
        return 1.0
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _initials(tokens: list[str]) -> str:
    return "".join(token[0] for token in tokens if token)


def _abbreviation_signal(left: list[str], right: list[str]) -> bool:
    if not left or not right:
        return False
    if _initials(left) == _initials(right) and len(left) == len(right):
        return True
    return any(
        len(short) <= 4 and long.startswith(short)
        for short in left
        for long in right
    ) or any(
        len(short) <= 4 and long.startswith(short)
        for short in right
        for long in left
    )


def _name_features(value: str) -> dict[str, object]:
    unicode_value = safe_unicode(value)
    compact_value = compact_safe(value)
    tokens = _tokens(value)
    return {
        "name_clean_unicode": unicode_value,
        "name_nopunct": compact_value,
        "name_core": experimental_suffix_stripped(value),
        "name_length": len(compact_value),
        "token_count": len(tokens),
        "tokens": tokens,
        "has_non_ascii": any(ord(char) > 127 for char in value),
    }


def _address_features(value: str) -> dict[str, object]:
    clean = safe_unicode(value)
    return {
        "address_clean": clean,
        "address_available": bool(clean),
        "address_tokens": _tokens(clean),
        "address_length": len(clean),
    }


def _classify_pair(row: pd.Series) -> tuple[str, dict[str, bool]]:
    left_name = _name_features(row["business_name_s1"])
    right_name = _name_features(row["business_name_target"])
    left_address = _address_features(row["business_address_s1"])
    right_address = _address_features(row["business_address_target"])
    left_tokens = left_name["tokens"]
    right_tokens = right_name["tokens"]
    token_jaccard = _jaccard(left_tokens, right_tokens)
    address_jaccard = _jaccard(
        left_address["address_tokens"], right_address["address_tokens"]
    )
    name_similarity = Levenshtein.normalized_similarity(
        left_name["name_nopunct"], right_name["name_nopunct"]
    )
    same_multiset = sorted(left_tokens) == sorted(right_tokens)
    subset = bool(left_tokens and right_tokens) and (
        set(left_tokens).issubset(right_tokens)
        or set(right_tokens).issubset(left_tokens)
    )
    address_shared_number = bool(
        set(re.findall(r"\d+", left_address["address_clean"]))
        & set(re.findall(r"\d+", right_address["address_clean"]))
    )
    signals = {
        "token_recoverable": bool(token_jaccard >= 0.5 or subset),
        "address_recoverable": bool(
            left_address["address_available"]
            and right_address["address_available"]
            and (address_jaccard >= 0.5 or address_shared_number)
        ),
        "approximate_recoverable": bool(
            name_similarity >= 0.75
            and token_jaccard < 0.5
            and not subset
        ),
        "difficult": bool(
            name_similarity < 0.75
            and token_jaccard < 0.5
            and not (
                left_address["address_available"]
                and right_address["address_available"]
                and (address_jaccard >= 0.5 or address_shared_number)
            )
        ),
    }

    if same_multiset and left_name["name_nopunct"] != right_name["name_nopunct"]:
        category = "word_order_change"
    elif left_name["name_core"] and (
        left_name["name_core"] == right_name["name_core"]
        and left_name["name_nopunct"] != right_name["name_nopunct"]
    ):
        category = "legal_suffix_variation"
    elif subset and set(left_tokens) != set(right_tokens):
        category = "additional_or_missing_tokens"
    elif _abbreviation_signal(left_tokens, right_tokens):
        category = "abbreviation_variation"
    elif name_similarity >= 0.75 and left_name["name_nopunct"] != right_name["name_nopunct"]:
        category = "typo_or_spelling_variation"
    elif (
        left_name["name_nopunct"] in right_name["name_nopunct"]
        or right_name["name_nopunct"] in left_name["name_nopunct"]
    ) and left_name["name_nopunct"] != right_name["name_nopunct"]:
        category = "partial_or_truncated_name"
    elif left_name["has_non_ascii"] != right_name["has_non_ascii"]:
        category = "transliteration_or_unicode_variation"
    elif max(left_name["token_count"], right_name["token_count"]) <= 1 and max(
        left_name["name_length"], right_name["name_length"]
    ) <= 4:
        category = "very_short_name"
    elif signals["address_recoverable"] and name_similarity < 0.75:
        category = "weak_name_address_informative"
    elif not left_address["address_available"] or not right_address["address_available"]:
        category = "missing_or_empty_address"
    else:
        category = "exact_normalized_name_mismatch"
    return category, signals


def _read_records(path: Path, ids: set[str], chunk_size: int) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
    ):
        selected = chunk[chunk["entity_id"].isin(ids)]
        if not selected.empty:
            frames.append(selected)
    if not frames:
        return pd.DataFrame(
            columns=["entity_id", "business_name", "business_address", "country"]
        )
    return pd.concat(frames, ignore_index=True)


def _sample_pairs(
    pairs: list[tuple[str, str]], sample_size: int, seed: int
) -> list[tuple[str, str]]:
    frame = pd.DataFrame(pairs, columns=["source1_entity_id", "matched_id"])
    if frame.empty:
        return []
    return list(
        frame.sample(n=min(sample_size, len(frame)), random_state=seed).itertuples(
            index=False, name=None
        )
    )


def _pair_frame(
    pairs: list[tuple[str, str]],
    target_path: Path,
    chunk_size: int,
) -> pd.DataFrame:
    pair_frame = pd.DataFrame(
        pairs, columns=["source1_entity_id", "matched_id"]
    )
    source1 = _read_records(
        TRAIN_SOURCE1,
        set(pair_frame["source1_entity_id"]),
        chunk_size,
    ).rename(
        columns={
            "entity_id": "source1_entity_id",
            "business_name": "business_name_s1",
            "business_address": "business_address_s1",
            "country": "country_s1",
        }
    )
    target = _read_records(
        target_path,
        set(pair_frame["matched_id"]),
        chunk_size,
    ).rename(
        columns={
            "entity_id": "matched_id",
            "business_name": "business_name_target",
            "business_address": "business_address_target",
            "country": "country_target",
        }
    )
    return pair_frame.merge(source1, on="source1_entity_id").merge(
        target, on="matched_id"
    )


def _distribution(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty:
        return {
            "pairs": 0,
            "name_length": {},
            "token_count": {},
            "address_available": {},
            "country": {},
        }
    features = frame["business_name_s1"].map(_name_features)
    return {
        "pairs": int(len(frame)),
        "name_length": features.map(lambda item: item["name_length"])
        .describe(percentiles=[0.5, 0.95, 0.99])
        .round(3)
        .to_dict(),
        "token_count": features.map(lambda item: item["token_count"])
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict(),
        "address_available": frame["business_address_s1"]
        .map(lambda value: bool(safe_unicode(value)))
        .value_counts()
        .to_dict(),
        "country": frame["country_s1"].map(safe_unicode).value_counts().to_dict(),
    }


def _analyze_pairs(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty:
        return {
            "category_counts": {},
            "category_percentages": {},
            "recoverability_counts": {},
            "recoverability_percentages": {},
            "examples": [],
            "pair_evidence": [],
        }
    categories: list[str] = []
    recoverability: Counter[str] = Counter()
    evidence: list[dict[str, object]] = []
    for row in frame.itertuples(index=False):
        row_series = pd.Series(row._asdict())
        category, signals = _classify_pair(row_series)
        categories.append(category)
        for signal, enabled in signals.items():
            if enabled:
                recoverability[signal] += 1
        evidence.append(
            {
                "source1_entity_id": row.source1_entity_id,
                "matched_id": row.matched_id,
                "business_name_s1": row.business_name_s1,
                "business_name_target": row.business_name_target,
                "business_address_s1": row.business_address_s1,
                "business_address_target": row.business_address_target,
                "country_s1": row.country_s1,
                "country_target": row.country_target,
                "category": category,
                "signals": signals,
                "name_clean_unicode_s1": safe_unicode(row.business_name_s1),
                "name_clean_unicode_target": safe_unicode(row.business_name_target),
                "name_nopunct_s1": compact_safe(row.business_name_s1),
                "name_nopunct_target": compact_safe(row.business_name_target),
                "name_core_s1": experimental_suffix_stripped(row.business_name_s1),
                "name_core_target": experimental_suffix_stripped(
                    row.business_name_target
                ),
                "address_clean_s1": safe_unicode(row.business_address_s1),
                "address_clean_target": safe_unicode(row.business_address_target),
            }
        )
    counts = Counter(categories)
    total = len(categories)
    examples = []
    for category in CATEGORY_NAMES:
        examples.extend(
            item for item in evidence if item["category"] == category
        )
        category_examples = [
            item for item in examples if item["category"] == category
        ][:3]
        examples = [
            item for item in examples if item["category"] != category
        ] + category_examples
    return {
        "category_counts": dict(counts),
        "category_percentages": {
            category: round(count / total * 100, 4)
            for category, count in counts.items()
        },
        "recoverability_counts": dict(recoverability),
        "recoverability_percentages": {
            category: round(count / total * 100, 4)
            for category, count in recoverability.items()
        },
        "examples": examples,
        "pair_evidence": evidence,
    }


def run_error_analysis(
    config: BlockingConfig | None = None,
    validation_fraction: float = 0.2,
    seed: int = 42,
    sample_size: int = SAMPLE_SIZE,
) -> dict[str, object]:
    """Analyze compact-name baseline misses independently for S2 and S3."""
    config = config or BlockingConfig()
    validation_ids = build_validation_ids(validation_fraction, seed)
    truth = load_ground_truth()
    target_paths = {"S2": TRAIN_SOURCE2, "S3": TRAIN_SOURCE3}
    results: dict[str, object] = {
        "method": {
            "validation_fraction": validation_fraction,
            "validation_seed": seed,
            "diagnostic_seed": DIAGNOSTIC_SEED,
            "sample_size_per_source": sample_size,
            "baseline_strategy": "compact_name",
            "parts_1_and_2_modified": False,
            "new_blocking_strategy_implemented": False,
        },
        "sources": {},
    }
    for source, target_path in target_paths.items():
        run = generate_exact_candidates(
            TRAIN_SOURCE1,
            target_path,
            source,
            "compact_name",
            config,
            validation_ids,
        )
        missed: list[tuple[str, str]] = []
        recovered: list[tuple[str, str]] = []
        for source1_id in sorted(validation_ids):
            candidate_ids = run.candidates.source1_to_candidates.get(
                source1_id, set()
            )
            for matched_id in sorted(truth.get(source1_id, set())):
                if not matched_id.startswith(source):
                    continue
                pair = (source1_id, matched_id)
                (recovered if matched_id in candidate_ids else missed).append(pair)
        missed_sample = _sample_pairs(
            missed, sample_size, DIAGNOSTIC_SEED + (2 if source == "S2" else 3)
        )
        recovered_sample = _sample_pairs(
            recovered,
            sample_size,
            DIAGNOSTIC_SEED + (20 if source == "S2" else 30),
        )
        missed_frame = _pair_frame(missed_sample, target_path, config.chunk_size)
        recovered_frame = _pair_frame(
            recovered_sample, target_path, config.chunk_size
        )
        missed_analysis = _analyze_pairs(missed_frame)
        results["sources"][source] = {
            "validation_entities": len(validation_ids),
            "total_true_pairs": len(missed) + len(recovered),
            "missed_true_pairs": len(missed),
            "recovered_true_pairs": len(recovered),
            "missed_pairs_sampled": len(missed_frame),
            "recovered_pairs_sampled": len(recovered_frame),
            "missed_analysis": missed_analysis,
            "missed_distribution": _distribution(missed_frame),
            "recovered_distribution": _distribution(recovered_frame),
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "part3_error_analysis_results.json",
    )
    args = parser.parse_args()
    results = run_error_analysis(
        BlockingConfig(chunk_size=args.chunk_size),
        args.validation_fraction,
        args.seed,
        args.sample_size,
    )
    args.output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
