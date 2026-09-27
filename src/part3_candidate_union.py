"""Candidate-set unions and marginal recovery metrics for Part 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.part3_blocking import BlockingRun, CandidateSet


@dataclass(frozen=True)
class MarginalRecovery:
    """Recovery and candidate-cost changes from adding one candidate set."""

    previous_strategy: str
    added_strategy: str
    new_recovered_pairs: int
    new_complete_entities: int
    candidate_pairs_before: int
    candidate_pairs_after: int
    marginal_candidate_pairs: int
    marginal_pair_recall: float
    marginal_candidate_cost: float | None
    previously_missed_pairs: int
    percentage_of_previous_misses_recovered: float

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def union_named_candidate_sets(
    runs: list[tuple[str, BlockingRun]],
    strategy: str,
) -> BlockingRun:
    """Union named runs after validating that they target one source."""
    if not runs:
        raise ValueError("At least one candidate run is required")
    target_sources = {run.target_source for _, run in runs}
    if len(target_sources) != 1:
        raise ValueError("Cannot union candidate runs from different target sources")

    merged: dict[str, set[str]] = {}
    for _, run in runs:
        for source1_id, candidate_ids in run.candidates.source1_to_candidates.items():
            merged.setdefault(source1_id, set()).update(candidate_ids)
    ordered = {
        source1_id: merged[source1_id]
        for source1_id in sorted(merged)
    }
    elapsed_seconds = sum(run.elapsed_seconds for _, run in runs)
    return BlockingRun(
        strategy=strategy,
        target_source=runs[0][1].target_source,
        candidates=CandidateSet(ordered),
        elapsed_seconds=elapsed_seconds,
    )


def measure_marginal_recovery(
    previous: BlockingRun,
    added: BlockingRun,
    truth: dict[str, set[str]],
    target_prefix: str,
    validation_s1_ids: Iterable[str],
) -> MarginalRecovery:
    """Measure recovery and candidate cost over an explicit S1 universe.

    Candidate maps are treated as sparse maps over ``validation_s1_ids``;
    missing entries have zero candidates. Ground truth is consulted only for
    these evaluation metrics, never while constructing candidate maps.
    """
    if previous.target_source != added.target_source:
        raise ValueError("Candidate runs must target the same source")

    source1_ids = set(validation_s1_ids)
    previous_pairs = 0
    added_pairs = 0
    new_complete_entities = 0
    previously_missed_pairs = 0
    total_true_pairs = 0

    for source1_id in source1_ids:
        previous_candidates = previous.candidates.source1_to_candidates.get(
            source1_id, set()
        )
        added_candidates = added.candidates.source1_to_candidates.get(
            source1_id, set()
        )
        truth_ids = {
            matched_id
            for matched_id in truth.get(source1_id, set())
            if matched_id.startswith(target_prefix)
        }
        total_true_pairs += len(truth_ids)
        previous_recovered = truth_ids & previous_candidates
        added_recovered = truth_ids & (previous_candidates | added_candidates)
        previous_pairs += len(previous_recovered)
        added_pairs += len(added_recovered)
        previously_missed_pairs += len(truth_ids - previous_recovered)
        if truth_ids - previous_recovered and not truth_ids - added_recovered:
            new_complete_entities += 1

    candidate_pairs_before = sum(
        len(previous.candidates.source1_to_candidates.get(source1_id, set()))
        for source1_id in source1_ids
    )
    candidate_pairs_after = sum(
        len(previous.candidates.source1_to_candidates.get(source1_id, set())
            | added.candidates.source1_to_candidates.get(source1_id, set()))
        for source1_id in source1_ids
    )
    new_recovered_pairs = added_pairs - previous_pairs
    marginal_candidate_pairs = candidate_pairs_after - candidate_pairs_before
    return MarginalRecovery(
        previous_strategy=previous.strategy,
        added_strategy=added.strategy,
        new_recovered_pairs=new_recovered_pairs,
        new_complete_entities=new_complete_entities,
        candidate_pairs_before=candidate_pairs_before,
        candidate_pairs_after=candidate_pairs_after,
        marginal_candidate_pairs=marginal_candidate_pairs,
        marginal_pair_recall=(
            new_recovered_pairs / total_true_pairs
            if total_true_pairs
            else 0.0
        ),
        marginal_candidate_cost=(
            marginal_candidate_pairs / new_recovered_pairs
            if new_recovered_pairs
            else None
        ),
        previously_missed_pairs=previously_missed_pairs,
        percentage_of_previous_misses_recovered=(
            new_recovered_pairs / previously_missed_pairs
            if previously_missed_pairs
            else 0.0
        ),
    )
