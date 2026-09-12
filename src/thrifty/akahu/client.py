"""Client for Akahu's personal-app REST API."""

import httpx2

from thrifty.akahu import transform
from thrifty.akahu.models import Account

BASE_URL = "https://api.akahu.io/v1"


class AkahuClient:
    """Talks to Akahu on behalf of a single personal app."""

    def __init__(self, app_token: str, user_token: str) -> None:
        self._headers = {
            "X-Akahu-Id": app_token,
            "Authorization": f"Bearer {user_token}",
        }

    async def get_accounts(self) -> list[Account]:
        """Every connected account, balances included."""
        async with httpx2.AsyncClient(
            base_url=BASE_URL, headers=self._headers
        ) as client:
            response = await client.get("/accounts")
            response.raise_for_status()
            return [transform.to_account(item) for item in response.json()["items"]]
