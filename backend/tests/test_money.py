"""Ported from the JavaScript implementation's scripts/test-logic.mjs.

The cases are deliberately identical so the two implementations can be checked
against each other while both exist.
"""

from typing import Any

import pytest

from budge.charges.money import (
    REFERENCE_FALLBACK,
    format_cents,
    make_reference,
    normalise_account,
    parse_amount,
    split_evenly,
)

# --- splitting: the cents must always add back up ---------------------------


def test_even_split_divides_exactly():
    assert split_evenly(1000, 4) == [250, 250, 250, 250]


def test_remainder_goes_to_the_earliest_shares():
    assert split_evenly(1000, 3) == [334, 333, 333]


def test_every_split_sums_to_the_original_total():
    for total in range(1, 2001, 7):
        for n in range(1, 10):
            shares = split_evenly(total, n)
            assert sum(shares) == total, f"{total}/{n}"
            assert max(shares) - min(shares) <= 1, f"{total}/{n} uneven"


def test_a_refund_splits_the_same_way_in_reverse():
    # Truncation toward zero, so a negative total mirrors the positive case
    # instead of drifting a cent the other way.
    assert split_evenly(-1000, 3) == [-334, -333, -333]
    for total in range(-1, -2001, -7):
        for n in range(1, 10):
            assert sum(split_evenly(total, n)) == total, f"{total}/{n}"


def test_split_rejects_fractional_cents():
    # The bug this module exists to prevent, so it fails loudly. Typed as Any
    # because the point is the runtime guard, which the checker would otherwise
    # stop us from reaching.
    fractional: Any = 10.5
    with pytest.raises(TypeError):
        split_evenly(fractional, 2)


def test_split_rejects_a_boolean_masquerading_as_a_number():
    # bool subclasses int in Python, so this would otherwise sail through.
    truthy: Any = True
    with pytest.raises(TypeError):
        split_evenly(truthy, 2)
    with pytest.raises(TypeError):
        split_evenly(1000, truthy)


def test_split_needs_at_least_one_share():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            split_evenly(1000, bad)


# --- parsing -----------------------------------------------------------------


def test_parses_plain_and_decorated_amounts():
    assert parse_amount("45") == 4500
    assert parse_amount("45.2") == 4520
    assert parse_amount("$45.20") == 4520
    assert parse_amount("1,234.56") == 123456


def test_rejects_junk_and_non_positive_amounts():
    for bad in ("", "abc", "45.999", "-5", "0", None):
        assert parse_amount(bad) is None, repr(bad)


def test_formats_cents_as_nz_money():
    assert format_cents(4520) == "$45.20"
    assert format_cents(123456) == "$1,234.56"
    assert format_cents(5) == "$0.05"
    assert format_cents(-4520) == "-$45.20"


# --- account numbers ---------------------------------------------------------


def test_normalises_15_and_16_digit_accounts():
    assert normalise_account("0212340123456000") == "02-1234-0123456-000"
    assert normalise_account("02-1234-0123456-00") == "02-1234-0123456-00"


def test_rejects_wrong_length_accounts():
    for bad in ("", "123", "021234012345600012", None):
        assert normalise_account(bad) is None, repr(bad)


# --- bank references ---------------------------------------------------------


def test_reference_fits_a_bank_field_and_survives_truncation():
    assert make_reference("Power — March") == "Power March"
    assert len(make_reference("A very long description indeed")) <= 12
    # No trailing space when the cut lands mid-word: a payer should not have to
    # notice and delete one.
    assert make_reference("Flat dinner at the Thai place") == "Flat dinner"
    assert make_reference("Groceries Sunday") == "Groceries Su"
    assert make_reference("") == REFERENCE_FALLBACK
    assert make_reference(None) == REFERENCE_FALLBACK
