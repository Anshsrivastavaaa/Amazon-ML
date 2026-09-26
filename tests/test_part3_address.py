"""Focused tests for the M5.1 address representation interface."""

from src.part3_address import (
    address_clean,
    address_tokens,
    extract_address_numbers,
    extract_postal_candidates,
    informative_address_tokens,
    parse_address,
)


def test_missing_address_returns_empty_signals() -> None:
    parsed = parse_address("")
    assert parsed.address_clean == ""
    assert parsed.tokens == ()
    assert parsed.informative_tokens == ()
    assert parsed.numbers == ()
    assert parsed.postal_candidates == ()


def test_us_address_extracts_number_and_postal_candidate() -> None:
    parsed = parse_address("123 Main Street, Austin, TX 78701")
    assert parsed.address_clean == "123 main street, austin, tx 78701"
    assert "123" in parsed.numbers
    assert "78701" in parsed.postal_candidates
    assert "main" in parsed.informative_tokens
    assert "street" not in parsed.informative_tokens


def test_indian_address_extracts_postal_like_candidate() -> None:
    parsed = parse_address("Plot N-14, MIDC, Ambad, Nashik 422010")
    assert "14" in parsed.numbers
    assert "422010" in parsed.postal_candidates
    assert "ambad" in parsed.informative_tokens


def test_punctuation_and_unit_markers_are_signals_not_truth() -> None:
    parsed = parse_address("Unit 4B, 55-57 King St.")
    assert parsed.tokens == ("unit", "4b", "55", "57", "king", "st")
    assert parsed.numbers == ("4b", "55", "57")
    assert parsed.postal_candidates == ()


def test_unicode_and_public_helpers_are_deterministic() -> None:
    value = "  Straße 12, München 80331 "
    assert address_clean(value) == "strasse 12, münchen 80331"
    assert address_tokens(value) == ("strasse", "12", "münchen", "80331")
    assert informative_address_tokens(value) == ("strasse", "münchen")
    assert extract_address_numbers(value) == ("12", "80331")
    assert extract_postal_candidates(value) == ("80331",)
