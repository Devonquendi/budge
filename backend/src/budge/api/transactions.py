"""FastAPI routes for transaction history and its classification."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from budge import credentials, demo, reconcile
from budge.akahu import AkahuClient, genie
from budge.akahu.models import Transaction
from budge.auth import CurrentUserId, SessionDep

router = APIRouter(prefix="/transactions", tags=["transactions"])

NOT_ONBOARDED = 409

DEFAULT_DAYS = 90
MAX_DAYS = 365


class History(BaseModel):
    """A window of transactions, classified as far as we can manage."""

    transactions: list[Transaction]
    days: int


async def _client(
    session: SessionDep, user_id: int
) -> AkahuClient | demo.FixtureClient:
    client = await credentials.client_for(session, user_id)
    if client is None:
        raise HTTPException(status_code=NOT_ONBOARDED, detail="Akahu not connected")
    return client


@router.get("")
async def get_transactions(
    user_id: CurrentUserId,
    session: SessionDep,
    days: int = Query(default=DEFAULT_DAYS, ge=1, le=MAX_DAYS),
) -> History:
    """Recent transactions for the accounts on the dashboard, newest first."""
    client = await _client(session, user_id)
    accounts = await credentials.name_accounts(
        session, user_id, await client.get_accounts()
    )

    included = await credentials.included_account_ids(session, user_id)
    if included is not None:
        accounts = [account for account in accounts if account.id in included]

    end = datetime.now(UTC)
    transactions = await client.get_transactions(
        accounts, start=end - timedelta(days=days), end=end
    )

    # Marked over the whole window rather than per row: a transfer is only
    # recognisable as the pair of legs it is, and the pair has to be in view.
    internal = reconcile.internal_ids(transactions)
    for transaction in transactions:
        transaction.internal = transaction.id in internal

    return History(transactions=await genie.classify(transactions), days=days)
