from collections import Counter

from src.part3_signal_blocking import SignalExtractionStats, SignalIndex
from src.part3_blocking import BlockingRun, CandidateSet
from src.part3_candidate_union import (
    measure_marginal_recovery,
    union_named_candidate_sets,
)
from src.part3_signal_evaluation import (
    ValidationSignalRow,
    generate_signal_combination_run,
    generate_signal_run,
)


def _index() -> SignalIndex:
    return SignalIndex(
        signal_name="number",
        country_aware=True,
        frequencies=Counter({"12": 2, "34": 10, "56": 1}),
        blocks={
            ("us", "12"): ("S2-1", "S2-2"),
            ("us", "34"): ("S2-3",),
            ("us", "56"): ("S2-4",),
        },
        stats=SignalExtractionStats(
            rows=4,
            rows_with_signal=4,
            rows_with_multiple_signals=1,
            distinct_signals=3,
            signal_occurrences=4,
        ),
    )


def test_number_run_unions_multiple_signals_without_a_candidate_cap() -> None:
    rows = [
        ValidationSignalRow(
            source1_id="S1-1",
            country="US",
            address="address",
            postal=(),
            number=("12", "56", "12"),
            has_address=True,
        )
    ]

    run, availability = generate_signal_run(
        "S2",
        "number",
        _index(),
        rows,
        "number",
        True,
    )

    assert run.candidates.source1_to_candidates["S1-1"] == {
        "S2-1",
        "S2-2",
        "S2-4",
    }
    assert availability["validation_entities_with_number"] == 1


def test_number_run_frequency_filter_excludes_only_over_threshold_signals() -> None:
    rows = [
        ValidationSignalRow(
            source1_id="S1-1",
            country="US",
            address="address",
            postal=(),
            number=("12", "34", "56"),
            has_address=True,
        )
    ]

    run, availability = generate_signal_run(
        "S2",
        "number_freq5",
        _index(),
        rows,
        "number",
        True,
        max_frequency=5,
    )

    assert run.candidates.source1_to_candidates["S1-1"] == {
        "S2-1",
        "S2-2",
        "S2-4",
    }
    assert availability["validation_entities_with_number"] == 1


def test_country_aware_number_run_excludes_missing_country_and_empty_signals() -> None:
    rows = [
        ValidationSignalRow(
            source1_id="S1-1",
            country="",
            address="",
            postal=(),
            number=("12",),
            has_address=False,
        ),
        ValidationSignalRow(
            source1_id="S1-2",
            country="US",
            address="address",
            postal=(),
            number=(),
            has_address=True,
        ),
    ]

    run, availability = generate_signal_run(
        "S2",
        "country_number",
        _index(),
        rows,
        "number",
        True,
    )

    assert run.candidates.source1_to_candidates == {"S1-1": set(), "S1-2": set()}
    assert availability == {
        "validation_entities_without_address": 1,
        "validation_entities_with_number": 1,
    }


def test_combination_intersects_signal_families_after_unioning_values() -> None:
    postal_index = _index()
    postal_index = SignalIndex(
        signal_name="postal",
        country_aware=True,
        frequencies=Counter({"p1": 1, "p2": 1}),
        blocks={
            ("us", "p1"): ("S2-1", "S2-2"),
            ("us", "p2"): ("S2-2", "S2-3"),
        },
        stats=postal_index.stats,
    )
    number_index = _index()
    rows = [
        ValidationSignalRow(
            source1_id="S1-1",
            country="US",
            address="address",
            postal=("p1", "p2"),
            number=("12", "34"),
            has_address=True,
        )
    ]

    run, availability = generate_signal_combination_run(
        "S2",
        "country_postal_number",
        {"postal": postal_index, "number": number_index},
        rows,
        ("postal", "number"),
        True,
        max_frequencies={"number": 5},
    )

    assert run.candidates.source1_to_candidates["S1-1"] == {"S2-1", "S2-2"}
    assert availability["validation_entities_with_postal"] == 1
    assert availability["validation_entities_with_number"] == 1


def test_combination_union_is_explicit_and_does_not_form_cartesian_pairs() -> None:
    postal_index = SignalIndex(
        signal_name="postal",
        country_aware=True,
        frequencies=Counter({"p1": 1}),
        blocks={("us", "p1"): ("S2-1",)},
        stats=_index().stats,
    )
    number_index = SignalIndex(
        signal_name="number",
        country_aware=True,
        frequencies=Counter({"12": 1}),
        blocks={("us", "12"): ("S2-2",)},
        stats=_index().stats,
    )
    rows = [
        ValidationSignalRow(
            source1_id="S1-1",
            country="US",
            address="address",
            postal=("p1",),
            number=("12",),
            has_address=True,
        )
    ]

    run, _ = generate_signal_combination_run(
        "S2",
        "postal_union_number",
        {"postal": postal_index, "number": number_index},
        rows,
        ("postal", "number"),
        True,
        combine="union",
    )

    assert run.candidates.source1_to_candidates["S1-1"] == {"S2-1", "S2-2"}


def test_combination_rejects_missing_index_and_unknown_combine() -> None:
    row = ValidationSignalRow(
        source1_id="S1-1",
        country="US",
        address="address",
        postal=("p1",),
        number=("12",),
        has_address=True,
    )
    try:
        generate_signal_combination_run(
            "S2",
            "missing",
            {"postal": _index()},
            [row],
            ("postal", "number"),
            True,
        )
    except ValueError as error:
        assert "Missing signal index" in str(error)
    else:
        raise AssertionError("missing signal index should fail explicitly")

    try:
        generate_signal_combination_run(
            "S2",
            "unknown",
            {"postal": _index(), "number": _index()},
            [row],
            ("postal", "number"),
            True,
            combine="cartesian",
        )
    except ValueError as error:
        assert "Unknown signal combination" in str(error)
    else:
        raise AssertionError("unknown combination should fail explicitly")


def _run(
    strategy: str,
    target_source: str,
    candidates: dict[str, set[str]],
) -> BlockingRun:
    return BlockingRun(
        strategy=strategy,
        target_source=target_source,
        candidates=CandidateSet(candidates),
        elapsed_seconds=1.0,
    )


def test_named_union_is_deterministic_and_validates_target_source() -> None:
    first = _run("m4", "S2", {"S1-1": {"S2-1"}, "S1-2": set()})
    second = _run("m52", "S2", {"S1-1": {"S2-2"}})

    merged = union_named_candidate_sets(
        [("m4", first), ("m52", second)],
        "m4_union_m52",
    )

    assert merged.strategy == "m4_union_m52"
    assert merged.target_source == "S2"
    assert merged.candidates.source1_to_candidates == {
        "S1-1": {"S2-1", "S2-2"},
        "S1-2": set(),
    }

    try:
        union_named_candidate_sets(
            [("m4", first), ("m52", _run("m52", "S3", {}))],
            "invalid",
        )
    except ValueError as error:
        assert "different target sources" in str(error)
    else:
        raise AssertionError("mixed target sources should fail explicitly")


def test_marginal_recovery_uses_candidate_identities_and_costs() -> None:
    previous = _run(
        "m4",
        "S2",
        {"S1-1": {"S2-1"}, "S1-2": set(), "S1-3": set()},
    )
    added = _run(
        "m52",
        "S2",
        {"S1-1": {"S2-2"}, "S1-2": {"S2-3"}, "S1-3": set()},
    )
    truth = {
        "S1-1": {"S2-1", "S2-2"},
        "S1-2": {"S2-3"},
        "S1-3": {"S2-4"},
    }

    result = measure_marginal_recovery(
        previous, added, truth, "S2", {"S1-1", "S1-2", "S1-3", "S1-4"}
    )

    assert result.new_recovered_pairs == 2
    assert result.new_complete_entities == 2
    assert result.candidate_pairs_before == 1
    assert result.candidate_pairs_after == 3
    assert result.marginal_candidate_pairs == 2
    assert result.marginal_pair_recall == 0.5
    assert result.previously_missed_pairs == 3
    assert result.percentage_of_previous_misses_recovered == 2 / 3
    assert result.marginal_candidate_cost == 1.0


def test_marginal_recovery_rejects_target_mismatch() -> None:
    try:
        measure_marginal_recovery(
            _run("m4", "S2", {}),
            _run("m52", "S3", {}),
            {},
            "S2",
            set(),
        )
    except ValueError as error:
        assert "same source" in str(error)
    else:
        raise AssertionError("mixed target sources should fail explicitly")


def test_marginal_cost_is_added_candidates_per_new_pair() -> None:
    previous = _run("m4", "S2", {"S1-1": set()})
    added = _run("m52", "S2", {"S1-1": {"S2-1", "S2-2", "S2-3"}})

    result = measure_marginal_recovery(
        previous,
        added,
        {"S1-1": {"S2-1"}},
        "S2",
        {"S1-1"},
    )

    assert result.new_recovered_pairs == 1
    assert result.candidate_pairs_after == 3
    assert result.marginal_candidate_cost == 3.0


def test_marginal_metrics_include_s1_absent_from_both_maps() -> None:
    previous = _run("m4", "S2", {"S1-1": set()})
    added = _run("m52", "S2", {"S1-1": set()})

    result = measure_marginal_recovery(
        previous,
        added,
        {"S1-1": set(), "S1-2": {"S2-1"}},
        "S2",
        {"S1-1", "S1-2"},
    )

    assert result.previously_missed_pairs == 1
    assert result.new_recovered_pairs == 0
    assert result.candidate_pairs_before == 0
    assert result.candidate_pairs_after == 0
    assert result.marginal_candidate_cost is None


def test_marginal_metrics_handle_overlap_and_zero_recovery() -> None:
    previous = _run("m4", "S2", {"S1-1": {"S2-1"}})
    added = _run("m52", "S2", {"S1-1": {"S2-1", "S2-2"}})

    result = measure_marginal_recovery(
        previous,
        added,
        {"S1-1": {"S2-3"}},
        "S2",
        {"S1-1"},
    )

    assert result.new_recovered_pairs == 0
    assert result.marginal_candidate_pairs == 1
    assert result.marginal_candidate_cost is None


def test_marginal_metrics_count_entity_completed_from_partial_recovery() -> None:
    previous = _run("m4", "S2", {"S1-1": {"S2-1"}})
    added = _run("m52", "S2", {"S1-1": {"S2-2"}})

    result = measure_marginal_recovery(
        previous,
        added,
        {"S1-1": {"S2-1", "S2-2"}},
        "S2",
        {"S1-1"},
    )

    assert result.new_recovered_pairs == 1
    assert result.new_complete_entities == 1
