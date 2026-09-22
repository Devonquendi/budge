"""The demo: invented people, invented bills, and an invented bank feed.

Nothing here reaches Akahu.
"""

from budge.demo.feed import FixtureClient, accounts_for, transactions_for
from budge.demo.people import ROSTER, Persona, enabled, is_persona, seed


def client_for(email: str) -> FixtureClient | None:
    """A stand-in bank for a persona, and nothing for anybody else."""
    if not enabled() or not is_persona(email):
        return None
    return FixtureClient(email.lower())


__all__ = [
    "ROSTER",
    "FixtureClient",
    "Persona",
    "accounts_for",
    "client_for",
    "enabled",
    "is_persona",
    "seed",
    "transactions_for",
]
