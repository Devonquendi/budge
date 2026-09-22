"""Matching credits to requests, and spotting transfers between your own accounts.

Pure functions over transaction mappings, so both are testable without a bank, a
network or a database. Transactions are dicts here rather than models on purpose:
this layer should not care where the rows came from.
"""

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

Txn = Mapping[str, Any]


def match_credit(credit: Txn, open_requests: Sequence[Txn]) -> Txn | None:
    """Match an incoming credit to exactly one open request, or nothing.

    Amount is the strong signal. The reference deliberately is NOT required —
    paying banks truncate it to twelve characters, drop it, or put it in a
    different field, so a matcher that depends on it fails quietly and often.
    Where the amount is ambiguous the payer's name breaks the tie; where it is
    still ambiguous this returns None and a human decides.

    Guessing wrong here means telling somebody they have paid when they have not,
    which is the worst thing this application could do.
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

    # Deliberately excludes the counterparty account number: a digit string can
    # only ever produce a false match against a person's name.
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
    """Ids of transactions that are you moving your own money about.

    With a joint and a personal account connected these can dominate a report —
    the same mistake as counting a flatmate's repayment as income, just bigger. A
    transfer shows up twice: a debit on one account and a matching credit on
    another, within a day or two.

    The pair must sit on DIFFERENT connections, so a genuine payment to somebody
    else can never be mistaken for one.
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
