"""FastAPI routes for account data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from budge import credentials, demo
from budge.akahu import AkahuClient
from budge.akahu.models import Account
from budge.auth import CurrentUserId, SessionDep
from budge.db.models import NICKNAME_MAX

router = APIRouter(prefix="/accounts", tags=["accounts"])

NOT_ONBOARDED = 409
NOT_FOUND = 404


class Selection(BaseModel):
    """Every account Akahu knows about, and the ones the dashboard totals."""

    accounts: list[Account]
    included: list[str]


class SelectionUpdate(BaseModel):
    included: list[str]


class NicknameUpdate(BaseModel):
    """Blank clears the rename, which puts Akahu's own name back."""

    nickname: str = Field(default="", max_length=NICKNAME_MAX)


async def _client(
    session: SessionDep, user_id: int
) -> AkahuClient | demo.FixtureClient:
    client = await credentials.client_for(session, user_id)
    if client is None:
        raise HTTPException(status_code=NOT_ONBOARDED, detail="Akahu not connected")
    return client


async def _accounts(session: SessionDep, user_id: int) -> list[Account]:
    """Every account Akahu returns, under whatever the user calls it."""
    client = await _client(session, user_id)
    return await credentials.name_accounts(
        session, user_id, await client.get_accounts()
    )


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
    accounts = await _accounts(session, user_id)
    included = await credentials.included_account_ids(session, user_id)
    if included is None:
        return accounts
    return [account for account in accounts if account.id in included]


@router.get("/selection")
async def get_selection(user_id: CurrentUserId, session: SessionDep) -> Selection:
    """Every account plus the current ticks, for the account picker."""
    return await _selection(session, user_id, await _accounts(session, user_id))


@router.put("/selection")
async def set_selection(
    body: SelectionUpdate, user_id: CurrentUserId, session: SessionDep
) -> Selection:
    """Replaces the tick list. Accounts Akahu no longer returns are dropped."""
    accounts = await _accounts(session, user_id)
    await credentials.set_included_account_ids(
        session, user_id, [a.id for a in accounts], set(body.included)
    )
    return await _selection(session, user_id, accounts)


@router.put("/{account_id}/nickname")
async def set_nickname(
    account_id: str,
    body: NicknameUpdate,
    user_id: CurrentUserId,
    session: SessionDep,
) -> Selection:
    """Renames one account for this user only. Akahu never hears about it."""
    accounts = await _accounts(session, user_id)
    account = next((a for a in accounts if a.id == account_id), None)
    if account is None:
        raise HTTPException(status_code=NOT_FOUND, detail="No such account")

    nickname = body.nickname.strip() or None
    await credentials.set_nickname(
        session, user_id, [a.id for a in accounts], account_id, nickname
    )
    # Applied here rather than re-reading: the accounts above are already the
    # answer, bar the one name that just changed.
    account.nickname = nickname
    return await _selection(session, user_id, accounts)
