"""Reusable postal and address-number signal indexes for Part 3."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

from src.part2_normalization import safe_unicode
from src.part3_address import parse_address
from src.part3_blocking import BlockingConfig


SignalExtractor = Callable[[object], tuple[str, ...]]
SignalKey = str | tuple[str, str]


@dataclass(frozen=True)
class SignalExtractionStats:
    """Observed extraction behavior; values are candidate signals only."""

    rows: int
    rows_with_signal: int
    rows_with_multiple_signals: int
    distinct_signals: int
    signal_occurrences: int

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class SignalIndex:
    """Deduplicated source-specific inverted index for one signal family."""

    signal_name: str
    country_aware: bool
    frequencies: Counter[str]
    blocks: dict[SignalKey, tuple[str, ...]]
    stats: SignalExtractionStats

    def lookup(self, signal: str, country: str = "") -> tuple[str, ...]:
        key: SignalKey = (
            (country, signal) if self.country_aware else signal
        )
        return self.blocks.get(key, ())

    def block_sizes(self) -> list[int]:
        return [len(values) for values in self.blocks.values()]


def _rows(
    path: Path, config: BlockingConfig
) -> Iterable[tuple[str, str, str, tuple[str, ...]]]:
    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=config.chunk_size,
        usecols=["entity_id", "business_address", "country"],
    ):
        for row in chunk.itertuples(index=False):
            yield (
                row.entity_id,
                safe_unicode(row.country),
                row.business_address,
                (),
            )


def _extractor(signal_name: str) -> SignalExtractor:
    if signal_name == "postal":
        return lambda value: parse_address(value).postal_candidates
    if signal_name == "number":
        return lambda value: parse_address(value).numbers
    raise ValueError(f"Unknown address signal: {signal_name}")


def build_signal_index(
    target_path: Path,
    signal_name: str,
    config: BlockingConfig | None = None,
    country_aware: bool = True,
) -> SignalIndex:
    """Build one reusable signal index with no empty universal key."""
    config = config or BlockingConfig()
    extract = _extractor(signal_name)
    frequencies: Counter[str] = Counter()
    rows = 0
    rows_with_signal = 0
    rows_with_multiple_signals = 0
    occurrences: dict[SignalKey, set[str]] = {}

    for entity_id, country, address, _ in _rows(target_path, config):
        rows += 1
        signals = tuple(dict.fromkeys(extract(address)))
        if not signals:
            continue
        rows_with_signal += 1
        if len(signals) > 1:
            rows_with_multiple_signals += 1
        frequencies.update(signals)
        for signal in signals:
            if country_aware and not country:
                continue
            key: SignalKey = (country, signal) if country_aware else signal
            occurrences.setdefault(key, set()).add(entity_id)

    blocks = {
        key: tuple(sorted(entity_ids))
        for key, entity_ids in occurrences.items()
    }
    return SignalIndex(
        signal_name=signal_name,
        country_aware=country_aware,
        frequencies=frequencies,
        blocks=blocks,
        stats=SignalExtractionStats(
            rows=rows,
            rows_with_signal=rows_with_signal,
            rows_with_multiple_signals=rows_with_multiple_signals,
            distinct_signals=len(frequencies),
            signal_occurrences=sum(frequencies.values()),
        ),
    )


def extract_signal_values(value: object, signal_name: str) -> tuple[str, ...]:
    """Return deduplicated candidate values for one raw address."""
    return tuple(dict.fromkeys(_extractor(signal_name)(value)))


def lookup_signals(
    index: SignalIndex,
    signals: Iterable[str],
    country: object = "",
) -> set[str]:
    """Union matching target IDs for one S1 address."""
    country_clean = safe_unicode(country)
    if index.country_aware and not country_clean:
        return set()
    values: set[str] = set()
    for signal in dict.fromkeys(signals):
        if signal:
            values.update(index.lookup(signal, country_clean))
    return values
