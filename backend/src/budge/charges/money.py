"""Amounts, splitting, account numbers and bank references.

Money is handled as whole cents in `int` throughout. Floats never appear: a
split that is a cent out is a bug somebody will notice and never trust again.
"""

import re
from decimal import Decimal

MAX_SAFE_CENTS = 2**53 - 1

_AMOUNT = re.compile(r"^\d+(\.\d{1,2})?$")
_NOT_MONEY = re.compile(r"[$,\s]")
_NOT_REFERENCE = re.compile(r"[^A-Za-z0-9 ]")
_RUNS_OF_SPACE = re.compile(r"\s+")
_NOT_DIGIT = re.compile(r"\D")

# Bank reference fields are twelve characters and truncate silently, so the
# fallback has to be shorter than that too.
REFERENCE_LENGTH = 12
REFERENCE_FALLBACK = "Budge"


def from_cents(cents: int) -> Decimal:
    """For the wire, where money travels as a decimal string."""
    return Decimal(cents).scaleb(-2)


def to_cents(amount: Decimal) -> int:
    return int(amount.scaleb(2))


def split_evenly(total_cents: int, n: int) -> list[int]:
    """Split a total into `n` whole-cent shares that sum back to exactly it.

    The remainder goes one cent at a time to the earliest shares, so four people
    splitting $10.00 get 250/250/250/250 and three get 334/333/333. Dividing
    money and rounding is what produces totals that do not add up.
    """
    # A float total is the bug this whole module exists to prevent, so it fails
    # loudly rather than silently producing shares that do not add up. bool is
    # an int subclass in Python and is never a sensible amount.
    if not isinstance(total_cents, int) or isinstance(total_cents, bool):
        raise TypeError("total must be whole cents")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("share count must be a whole number")
    if n < 1:
        raise ValueError("need at least one share")

    # Truncate toward zero, not toward negative infinity: a refund split three
    # ways should mirror the positive case rather than drift a cent the other
    # way. Python's // floors, so it cannot be used here.
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
    """Normalise an NZ account number, or return None.

    The format is bank-branch-account-suffix: 2-4-7 digits then a 2 or 3 digit
    suffix. No checksum is attempted — the bank does that, and Confirmation of
    Payee has checked the name as well since November 2024.
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
