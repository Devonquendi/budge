"""Request state, bill tallies, and the tokens that address them."""

import secrets
from collections.abc import Iterable, Mapping
from typing import Any, NamedTuple

# Rows as they come back from the database: known keys, values we read by name.
# Mirrors `Txn` in feed.py rather than inventing a second convention.
Row = Mapping[str, Any]

# Creator actions are authoritative and apply in order. The person owed always
# has the final say on whether money actually arrived.
CREATOR_ACTIONS = {
    "confirmed": "confirmed",
    "cancelled": "cancelled",
    "reopened": "open",
}

OPEN = "open"
MARKED_PAID = "marked_paid"
DECLINED = "declined"
CONFIRMED = "confirmed"
CANCELLED = "cancelled"

# Unguessable, URL-safe, and short enough to read down a phone. Crockford-style:
# no i, l or o, so nothing is mistaken for 1 or 0 when somebody types it in.
#
# Exactly 32 characters, which matters. The JavaScript original listed 33 and
# indexed them with `byte % 32`, so its last character could never be produced —
# dropping it here loses nothing and makes the mapping honest. 256 divides by 32
# evenly, so there is no modulo bias either way.
TOKEN_ALPHABET = "0123456789abcdefghjkmnpqrstuvwxy"


class Tally(NamedTuple):
    """What a bill's creator is still owed, and what has actually landed."""

    owed: int
    claimed: int
    settled: int
    outstanding: int


def derive_state(events: Iterable[Row]) -> str:
    """Fold an append-only event log into the request's current state.

    State is derived, never stored, so a balance can always be re-explained from
    what actually happened rather than trusted from a column somebody wrote.
    """
    state = OPEN
    for event in events:
        kind = event["type"]
        if kind in CREATOR_ACTIONS:
            state = CREATOR_ACTIONS[kind]
        elif kind == "marked_paid" and state == OPEN:
            state = MARKED_PAID
        # Declining is the payer pushing back, so it can override their own
        # earlier claim — but never a confirmation, because money that arrived,
        # arrived.
        elif kind == "declined" and state in (OPEN, MARKED_PAID):
            state = DECLINED
    return state


def tally_bill(requests: Iterable[Row]) -> Tally:
    """Sum a bill's requests by what stage each has reached."""
    owed = claimed = settled = 0
    for request in requests:
        state = request["state"]
        amount = request["amount_cents"]
        if state == CANCELLED:
            continue
        if state == CONFIRMED:
            settled += amount
        elif state == MARKED_PAID:
            claimed += amount
        else:
            owed += amount
    return Tally(
        owed=owed, claimed=claimed, settled=settled, outstanding=owed + claimed
    )


def make_token(length: int = 12) -> str:
    """A short, unguessable, unambiguous token for addressing a request."""
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(length))
