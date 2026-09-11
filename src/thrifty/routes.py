"""FastAPI routes for account data."""

from fastapi import APIRouter

from thrifty.akahu import AkahuClient
from thrifty.akahu.models import Account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def get_accounts() -> list[Account]:
    """Connected accounts and their balances."""
    return await AkahuClient.from_env().get_accounts()
