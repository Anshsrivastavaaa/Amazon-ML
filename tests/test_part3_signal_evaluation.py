from collections import Counter

from src.part3_signal_blocking import SignalExtractionStats, SignalIndex
from src.part3_signal_evaluation import ValidationSignalRow, generate_signal_run


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
