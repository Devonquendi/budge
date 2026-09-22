"""Request state, bill tallies, and the tokens that address them."""

import secrets
from collections.abc import Iterable, Mapping
from typing import Any, NamedTuple

Row = Mapping[str, Any]

# The person owed has the final say, so their actions always apply.
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

# No i, l or o, so nothing is misread as 1 or 0 when somebody types it in.
TOKEN_ALPHABET = "0123456789abcdefghjkmnpqrstuvwxy"


class Tally(NamedTuple):
    """What a bill's creator is still owed, and what has actually landed."""

    owed: int
    claimed: int
    settled: int
    outstanding: int


def derive_state(events: Iterable[Row]) -> str:
    """Fold a request's event log into its current state."""
    state = OPEN
    for event in events:
        kind = event["type"]
        if kind in CREATOR_ACTIONS:
            state = CREATOR_ACTIONS[kind]
        elif kind == MARKED_PAID and state in (OPEN, DECLINED):
            state = MARKED_PAID
        # The payer can take back their own claim, but not a confirmation.
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
