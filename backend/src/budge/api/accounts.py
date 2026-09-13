"""FastAPI routes for account data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from budge import credentials
from budge.akahu import AkahuClient
from budge.akahu.models import Account
from budge.auth import CurrentUserId, SessionDep

router = APIRouter(prefix="/accounts", tags=["accounts"])

NOT_ONBOARDED = 409


class Selection(BaseModel):
    """Every account Akahu knows about, and the ones the dashboard totals."""

    accounts: list[Account]
    included: list[str]


class SelectionUpdate(BaseModel):
    included: list[str]


async def _client(session: SessionDep, user_id: int) -> AkahuClient:
    client = await credentials.client_for(session, user_id)
    if client is None:
        raise HTTPException(status_code=NOT_ONBOARDED, detail="Akahu not connected")
    return client


async def _selection(
    session: SessionDep, user_id: int, accounts: list[Account]
) -> Selection:
    included = await credentials.included_account_ids(session, user_id)
    # Nothing chosen yet means everything counts, which is what onboarding shows.
    ids = [a.id for a in accounts] if included is None else sorted(included)
    return Selection(accounts=accounts, included=ids)


@router.get("")
async def get_accounts(user_id: CurrentUserId, session: SessionDep) -> list[Account]:
    """The user's dashboard accounts and their balances."""
    client = await _client(session, user_id)
    accounts = await client.get_accounts()
    included = await credentials.included_account_ids(session, user_id)
    if included is None:
        return accounts
    return [account for account in accounts if account.id in included]


@router.get("/selection")
async def get_selection(user_id: CurrentUserId, session: SessionDep) -> Selection:
    """Every account plus the current ticks, for the account picker."""
    client = await _client(session, user_id)
    return await _selection(session, user_id, await client.get_accounts())


@router.put("/selection")
async def set_selection(
    body: SelectionUpdate, user_id: CurrentUserId, session: SessionDep
) -> Selection:
    """Replaces the tick list. Accounts Akahu no longer returns are dropped."""
    client = await _client(session, user_id)
    accounts = await client.get_accounts()
    await credentials.set_included_account_ids(
        session, user_id, [a.id for a in accounts], set(body.included)
    )
    return await _selection(session, user_id, accounts)
