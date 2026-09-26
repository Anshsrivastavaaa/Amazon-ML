"""Conservative address representations for Part 3 blocking experiments."""

from __future__ import annotations

from dataclasses import dataclass
import re

from src.part2_normalization import compact_safe, safe_unicode


_ADDRESS_NUMBER_PATTERN = re.compile(
    r"(?<![a-z0-9])\d+[a-z]?(?![a-z0-9])",
    flags=re.IGNORECASE,
)
_POSTAL_PATTERN = re.compile(r"(?<!\w)\d{4,6}(?:-\d{4})?(?!\w)")
_GENERIC_ADDRESS_TOKENS = {
    "apt",
    "apartment",
    "blvd",
    "city",
    "county",
    "dist",
    "district",
    "dr",
    "drive",
    "hwy",
    "lane",
    "ln",
    "road",
    "rd",
    "route",
    "st",
    "street",
    "suite",
    "tal",
    "unit",
}


@dataclass(frozen=True)
class AddressRepresentation:
    """Derived address signals; none are treated as ground-truth fields."""

    address_clean: str
    tokens: tuple[str, ...]
    informative_tokens: tuple[str, ...]
    numbers: tuple[str, ...]
    postal_candidates: tuple[str, ...]


def address_clean(value: object) -> str:
    """Return conservative Unicode-normalized address text."""
    return safe_unicode(value)


def address_tokens(value: object) -> tuple[str, ...]:
    """Return stable unique punctuation-insensitive address tokens."""
    tokens = compact_safe(value).split()
    return tuple(dict.fromkeys(tokens))


def informative_address_tokens(value: object) -> tuple[str, ...]:
    """Remove generic address labels and standalone numeric tokens."""
    return tuple(
        token
        for token in address_tokens(value)
        if token not in _GENERIC_ADDRESS_TOKENS
        and not token.isdigit()
        and len(token) >= 2
    )


def extract_address_numbers(value: object) -> tuple[str, ...]:
    """Extract numeric/address-number candidates without asserting semantics."""
    text = compact_safe(value)
    return tuple(dict.fromkeys(_ADDRESS_NUMBER_PATTERN.findall(text)))


def extract_postal_candidates(value: object) -> tuple[str, ...]:
    """Extract postal-like digit runs as candidate signals.

    A numeric run may be a street number, unit, postal code, or another
    address component, so this function does not assign ground-truth meaning.
    """
    text = address_clean(value)
    candidates = []
    for match in _POSTAL_PATTERN.finditer(text):
        normalized = match.group().replace("-", "")
        if normalized not in candidates:
            candidates.append(normalized)
    return tuple(candidates)


def parse_address(value: object) -> AddressRepresentation:
    """Build all conservative address signals for one raw value."""
    return AddressRepresentation(
        address_clean=address_clean(value),
        tokens=address_tokens(value),
        informative_tokens=informative_address_tokens(value),
        numbers=extract_address_numbers(value),
        postal_candidates=extract_postal_candidates(value),
    )
