"""FastAPI routes for account data."""

from fastapi import APIRouter

from thrifty.akahu import AkahuClient

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def get_accounts() -> list[dict]:
    """Connected accounts and their balances."""
    return await AkahuClient.from_env().get_accounts()
