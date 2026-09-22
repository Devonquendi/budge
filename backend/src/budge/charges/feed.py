"""Matching credits to requests, and spotting transfers between your own accounts.

Transactions are plain mappings here, so this doesn't care where they came from.
"""

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

Txn = Mapping[str, Any]


def match_credit(credit: Txn, open_requests: Sequence[Txn]) -> Txn | None:
    """The one open request this credit pays, or None if it could be several.

    Matched on amount, with the payer's first name breaking a tie. Not on the
    reference: banks truncate it, drop it, or move it to another field.
    """
    if credit["amount_cents"] <= 0:
        return None

    same_amount = [
        r for r in open_requests if r["amount_cents"] == credit["amount_cents"]
    ]
    if not same_amount:
        return None
    if len(same_amount) == 1:
        return same_amount[0]

    # Not the counterparty's account number: digits can only false-match a name.
    haystack = " ".join(
        str(credit.get(field) or "")
        for field in ("description", "particulars", "reference", "counterparty")
    ).lower()

    def named(request: Txn) -> bool:
        first = str(request["debtor_name"]).strip().split()[0].lower()
        return len(first) >= 3 and first in haystack

    by_name = [r for r in same_amount if named(r)]
    return by_name[0] if len(by_name) == 1 else None


def _day_number(value: object) -> int:
    """Whole days since the epoch, from a date or an ISO-ish string."""
    if isinstance(value, datetime):
        return value.date().toordinal()
    if isinstance(value, date):
        return value.toordinal()
    return date.fromisoformat(str(value)[:10]).toordinal()


def find_internal_transfers(
    transactions: Sequence[Txn], window_days: int = 3
) -> set[Any]:
    """Ids of both legs of each transfer between the user's own accounts.

    A debit and a credit of the same amount within a few days, on different
    connections so a payment to somebody else is never mistaken for one.
    """
    credits = [t for t in transactions if t["amount_cents"] > 0]
    claimed: set[Any] = set()
    internal: set[Any] = set()

    for debit in (t for t in transactions if t["amount_cents"] < 0):
        for credit in credits:
            if (
                credit["id"] not in claimed
                and credit["amount_cents"] == -debit["amount_cents"]
                and credit.get("connection_id") != debit.get("connection_id")
                and abs(_day_number(credit["date"]) - _day_number(debit["date"]))
                <= window_days
            ):
                claimed.add(credit["id"])
                internal.add(debit["id"])
                internal.add(credit["id"])
                break

    return internal
