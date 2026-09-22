"""Amounts in whole cents, splitting, account numbers and bank references."""

import re
from decimal import Decimal

# The most cents the browser can still add up exactly.
MAX_SAFE_CENTS = 2**53 - 1

_AMOUNT = re.compile(r"^\d+(\.\d{1,2})?$")
_NOT_MONEY = re.compile(r"[$,\s]")
_NOT_REFERENCE = re.compile(r"[^A-Za-z0-9 ]")
_RUNS_OF_SPACE = re.compile(r"\s+")
_NOT_DIGIT = re.compile(r"\D")

# Bank reference fields are twelve characters and truncate silently.
REFERENCE_LENGTH = 12
REFERENCE_FALLBACK = "Budge"


def from_cents(cents: int) -> Decimal:
    """For the wire, where money travels as a decimal string."""
    return Decimal(cents).scaleb(-2)


def to_cents(amount: Decimal) -> int:
    return int(amount.scaleb(2))


def split_evenly(total_cents: int, n: int) -> list[int]:
    """`n` whole-cent shares that add back to the total, odd cents on the first.

    $10.00 three ways is 334/333/333.
    """
    # bool is an int subclass, and never an amount.
    if not isinstance(total_cents, int) or isinstance(total_cents, bool):
        raise TypeError("total must be whole cents")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("share count must be a whole number")
    if n < 1:
        raise ValueError("need at least one share")

    # Toward zero, so a negative total mirrors the positive one. // would floor.
    base = int(total_cents / n)
    remainder = total_cents - base * n
    step = -1 if remainder < 0 else 1
    remainder = abs(remainder)
    return [base + (step if i < remainder else 0) for i in range(n)]


def parse_amount(value: object) -> int | None:
    """Money in, cents out. Accepts "45", "45.5", "$45.20", "1,234.56"."""
    cleaned = _NOT_MONEY.sub("", "" if value is None else str(value))
    if not _AMOUNT.fullmatch(cleaned):
        return None
    whole, _, frac = cleaned.partition(".")
    cents = int(whole) * 100 + int(frac.ljust(2, "0") or 0)
    return cents if 0 < cents <= MAX_SAFE_CENTS else None


def normalise_account(value: object) -> str | None:
    """An NZ account number as bank-branch-account-suffix, or None.

    No checksum: the bank does that, and Confirmation of Payee checks the name.
    """
    digits = _NOT_DIGIT.sub("", "" if value is None else str(value))
    if len(digits) not in (15, 16):
        return None
    return "-".join([digits[:2], digits[2:6], digits[6:13], digits[13:]])


def make_reference(title: object) -> str:
    """Build a bank reference that still means something after truncation."""
    clean = _NOT_REFERENCE.sub(" ", "" if title is None else str(title))
    clean = _RUNS_OF_SPACE.sub(" ", clean).strip()
    return (clean or REFERENCE_FALLBACK)[:REFERENCE_LENGTH]
