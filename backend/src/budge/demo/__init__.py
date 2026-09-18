"""The demo: invented people, invented bills, and an invented bank feed.

Nothing here reaches Akahu. A persona has no credentials to reach it with, and
previews cannot use credentials at all, which is the whole reason the demo
exists: something to look at on a deployment that is walled off from real banks.
"""

from collections.abc import Sequence

from budge.demo.feed import (
    FixtureClient,
    Settlement,
    accounts_for,
    settlement_credits,
    transactions_for,
)
from budge.demo.people import ROSTER, Persona, enabled, is_persona, seed


def client_for(
    email: str, settlements: Sequence[Settlement] = ()
) -> FixtureClient | None:
    """A stand-in bank for a persona, and nothing for anybody else.

    `settlements` are the requests other personas have said they paid. Passing
    them in puts a matching credit in this persona's feed, which is what gives
    the demo something real to reconcile rather than a staged result.
    """
    if not enabled() or not is_persona(email):
        return None
    return FixtureClient(email.lower(), settlements)


__all__ = [
    "ROSTER",
    "FixtureClient",
    "Persona",
    "Settlement",
    "accounts_for",
    "client_for",
    "enabled",
    "is_persona",
    "seed",
    "settlement_credits",
    "transactions_for",
]
