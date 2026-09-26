"""Focused tests for M5.2 address-token blocking helpers."""

from collections import Counter
from pathlib import Path

from src.part3_address_blocking import (
    address_block_distribution,
    build_country_address_index,
)
from src.part3_blocking import BlockingConfig


def test_country_address_index_ignores_empty_country_and_filters_frequency(
    tmp_path: Path,
) -> None:
    path = tmp_path / "target.tsv"
    path.write_text(
        "entity_id\tbusiness_address\tcountry\n"
        "S2-1\t123 Main Road, Austin\tUS\n"
        "S2-2\t123 Main Road, Dallas\tUS\n"
        "S2-3\t45 Market Street, Pune\tIndia\n"
        "S2-4\t45 Market Street, Pune\t\n",
        encoding="utf-8",
    )
    frequencies = Counter({"main": 1, "austin": 1, "market": 2, "pune": 2})
    index = build_country_address_index(
        path, frequencies, 1, BlockingConfig(chunk_size=2)
    )
    assert index[("us", "main")] == ["S2-1", "S2-2"]
    assert ("india", "pune") not in index
    assert ("", "pune") not in index


def test_block_distribution_exposes_oversized_blocks() -> None:
    summary = address_block_distribution(
        {
            ("us", "main"): ["S2-1"] * 101,
            ("us", "market"): ["S2-2"],
        },
        Counter({"main": 1, "market": 1}),
        10,
    )
    assert summary["indexed_country_token_blocks"] == 2
    assert summary["blocks_over_100"] == 1
    assert summary["max_block_size"] == 101
