"""Genie, Akahu's transaction enrichment API.

Genie is a separate service from the main Akahu API with its own key, handed
out by emailing hello@akahu.nz. Set GENIE_API_TOKEN and the transactions page
starts filling in the categories Akahu didn't send; leave it unset and
everything below is inert, which is the state a fresh clone is in.
"""

import os
from decimal import Decimal

import httpx2

from budge.akahu import transform
from budge.akahu.models import Transaction

BASE_URL = "https://api.genie.akahu.io/v1"

# Genie takes up to 1000 queries per request.
BATCH_SIZE = 1000

# Genie scores 0 to 0.99 and returns its guesses regardless. Below this the
# match is a coin flip, and a wrong category is worse than a blank one because
# it silently skews every total built on top of it.
MIN_CONFIDENCE = 0.6


class GenieClient:
    """Looks up merchants and categories for transaction descriptions."""

    def __init__(self, api_token: str) -> None:
        self._headers = {"Authorization": f"Bearer {api_token}"}

    async def search(self, queries: list[dict]) -> dict[str, dict]:
        """Best match per query, keyed by the correlation id we sent."""
        matches: dict[str, dict] = {}
        async with httpx2.AsyncClient(
            base_url=BASE_URL, headers=self._headers, timeout=30
        ) as client:
            for start in range(0, len(queries), BATCH_SIZE):
                batch = queries[start : start + BATCH_SIZE]
                response = await client.post("/search", json=batch)
                response.raise_for_status()
                payload = response.json(parse_float=Decimal)
                for item in payload.get("items", []):
                    best = _best(item.get("results") or [])
                    if best is not None:
                        matches[item["id"]] = best
        return matches


def _best(results: list[dict]) -> dict | None:
    """The most confident result, if any of them clear the bar."""
    confident = [r for r in results if float(r.get("confidence", 0)) >= MIN_CONFIDENCE]
    if not confident:
        return None
    return max(confident, key=lambda result: float(result["confidence"]))


# Genie only accepts these four, while Akahu sends a dozen. Anything not
# mapped here is sent without a type rather than rejected outright.
GENIE_TYPES = {
    "CARD": "CARD",
    "EFTPOS": "CARD",
    "DEBIT": "CARD",
    "DIRECT DEBIT": "DIRECT DEBIT",
    "PAYMENT": "PAYMENT",
    "STANDING ORDER": "STANDING ORDER",
}

# Loan repayments, interest, bank fees and incoming pay have no merchant behind
# them, so Genie has nothing to match on. Skipping them keeps the bill and the
# latency down, and stops a confident-looking wrong answer landing on rows the
# user can already read at a glance.
UNMATCHABLE_TYPES = frozenset(
    {"LOAN", "INTEREST", "FEE", "CREDIT", "DIRECT CREDIT", "TRANSFER"}
)


def _query(transaction: Transaction) -> dict:
    """One Genie query. More context means a better match, so send what we have."""
    query = {
        "id": transaction.id,
        "description": transaction.description,
        "_connection": transaction.connection_id,
        # Genie's sign convention matches Akahu's, so the amount goes as-is.
        "amount": float(transaction.amount),
        "direction": "CREDIT" if transaction.amount > 0 else "DEBIT",
    }
    kind = GENIE_TYPES.get(transaction.type)
    if kind is not None:
        query["type"] = kind
    return query


async def classify(transactions: list[Transaction]) -> list[Transaction]:
    """Fill in the categories and merchants Akahu left blank.

    Anything Akahu already classified is left alone — it knows the user's own
    connection, which Genie is only guessing at from the description. Returns
    the list unchanged if Genie isn't configured or doesn't answer, because a
    missing category should degrade the page, not break it.
    """
    token = os.environ.get("GENIE_API_TOKEN")
    if not token:
        return transactions

    unknown = [
        t
        for t in transactions
        if t.category is None and t.type not in UNMATCHABLE_TYPES
    ]
    if not unknown:
        return transactions

    try:
        matches = await GenieClient(token).search([_query(t) for t in unknown])
    except httpx2.HTTPError:
        return transactions

    for transaction in unknown:
        match = matches.get(transaction.id)
        if match is None:
            continue
        transaction.category = transform.to_category(
            match.get("category"),
            source="genie",
            confidence=float(match["confidence"]),
        )
        if transaction.merchant is None:
            transaction.merchant = transform.to_merchant(match.get("merchant"))

    return transactions
