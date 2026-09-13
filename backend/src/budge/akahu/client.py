"""Client for Akahu's personal-app REST API."""

from datetime import UTC, datetime
from decimal import Decimal

import httpx2

from budge.akahu import transform
from budge.akahu.models import Account, Transaction

BASE_URL = "https://api.akahu.io/v1"

# Akahu pages transactions with a cursor and no total. A year of a busy account
# is a few thousand rows, so this is headroom rather than a real limit — but an
# unbounded loop against someone else's API is not something to ship.
MAX_PAGES = 50


class AkahuClient:
    """Talks to Akahu on behalf of a single personal app."""

    def __init__(self, app_token: str, user_token: str) -> None:
        self._headers = {
            "X-Akahu-Id": app_token,
            "Authorization": f"Bearer {user_token}",
        }

    def _session(self) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(base_url=BASE_URL, headers=self._headers)

    async def get_accounts(self) -> list[Account]:
        """Every connected account, balances included."""
        async with self._session() as client:
            response = await client.get("/accounts")
            response.raise_for_status()
            # parse_float keeps balances exact: by the time json() has built a
            # float the cents are already gone, so Decimal has to happen here.
            payload = response.json(parse_float=Decimal)
            return [transform.to_account(item) for item in payload["items"]]

    async def get_transactions(
        self, accounts: list[Account], start: datetime, end: datetime
    ) -> list[Transaction]:
        """Settled transactions over a date range, newest first.

        The accounts come in rather than being fetched again because they carry
        the name and currency Akahu leaves off each transaction, and the caller
        has already loaded them to decide which ones to keep.
        """
        by_id = {account.id: account for account in accounts}
        params = {"start": _stamp(start), "end": _stamp(end)}
        items: list[dict] = []

        async with self._session() as client:
            for _ in range(MAX_PAGES):
                response = await client.get("/transactions", params=params)
                response.raise_for_status()
                payload = response.json(parse_float=Decimal)
                items.extend(payload["items"])
                cursor = (payload.get("cursor") or {}).get("next")
                if not cursor:
                    break
                params["cursor"] = cursor

        transactions = [
            transform.to_transaction(
                item,
                account_name=by_id[item["_account"]].name,
                currency=by_id[item["_account"]].currency,
            )
            for item in items
            # An account the user has switched off, or one Akahu stopped
            # returning, has no name to show — drop it rather than guess.
            if item["_account"] in by_id
        ]
        transactions.sort(key=lambda transaction: transaction.date, reverse=True)
        return transactions


def _stamp(moment: datetime) -> str:
    """Akahu wants ISO 8601 in UTC, and is picky about the trailing Z."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
