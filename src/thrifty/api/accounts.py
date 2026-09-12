"""FastAPI routes for account data."""

from fastapi import APIRouter, HTTPException

from thrifty import credentials
from thrifty.akahu.models import Account
from thrifty.auth import CurrentUserId, SessionDep

router = APIRouter(prefix="/accounts", tags=["accounts"])

NOT_ONBOARDED = 409


@router.get("")
async def get_accounts(user_id: CurrentUserId, session: SessionDep) -> list[Account]:
    """The user's dashboard accounts and their balances."""
    client = await credentials.client_for(session, user_id)
    if client is None:
        raise HTTPException(status_code=NOT_ONBOARDED, detail="Akahu not connected")

    accounts = await client.get_accounts()
    included = await credentials.included_account_ids(session, user_id)
    if included is None:
        return accounts
    return [account for account in accounts if account.id in included]
