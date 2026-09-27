from pathlib import Path

from src.part3_blocking import BlockingConfig
from src.part3_signal_blocking import (
    build_signal_index,
    extract_signal_values,
    lookup_signals,
)


def _target_fixture(path: Path) -> None:
    path.write_text(
        "entity_id\tbusiness_address\tcountry\n"
        "S2-1\t123 Main Street, Austin, TX 78701\tUS\n"
        "S2-2\tUnit 4B, 123 Main Street, Austin, TX 78701\tUS\n"
        "S2-3\t123 Main Street, Austin, TX 78701\t\n"
        "S2-4\t45 Market Road, Pune 422010\tIndia\n",
        encoding="utf-8",
    )


def test_signal_extraction_is_deduplicated_and_signal_specific() -> None:
    address = "Unit 4B, 123 Main Street, Austin, TX 78701"
    assert extract_signal_values(address, "postal") == ("78701",)
    assert extract_signal_values(address, "number") == ("4b", "123", "78701")


def test_country_aware_index_excludes_empty_country_and_deduplicates_ids(
    tmp_path: Path,
) -> None:
    path = tmp_path / "target.tsv"
    _target_fixture(path)
    index = build_signal_index(
        path, "postal", BlockingConfig(chunk_size=2), country_aware=True
    )
    assert index.lookup("78701", "us") == ("S2-1", "S2-2")
    assert index.lookup("78701", "") == ()
    assert index.stats.rows == 4
    assert index.stats.rows_with_signal == 4
    assert index.stats.rows_with_multiple_signals == 0


def test_number_index_reports_multi_signal_rows_and_unconstrained_lookup(
    tmp_path: Path,
) -> None:
    path = tmp_path / "target.tsv"
    _target_fixture(path)
    index = build_signal_index(
        path, "number", BlockingConfig(chunk_size=2), country_aware=False
    )
    assert index.stats.rows_with_multiple_signals == 4
    assert "S2-1" in lookup_signals(index, ("123",), "US")
    assert "S2-2" in lookup_signals(index, ("4b",), "US")
    assert index.frequencies["123"] == 3


def test_unknown_signal_is_rejected() -> None:
    try:
        build_signal_index(Path("unused.tsv"), "unknown")
    except ValueError as error:
        assert "Unknown address signal" in str(error)
    else:
        raise AssertionError("unknown signal should fail explicitly")
