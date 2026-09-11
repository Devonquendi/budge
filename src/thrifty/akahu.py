"""Client for Akahu's personal-app REST API."""

import os

import httpx2

BASE_URL = "https://api.akahu.io/v1"


class AkahuClient:
    """Talks to Akahu on behalf of a single personal app."""

    def __init__(self, app_token: str, user_token: str) -> None:
        self._headers = {
            "X-Akahu-Id": app_token,
            "Authorization": f"Bearer {user_token}",
        }

    @classmethod
    def from_env(cls) -> AkahuClient:
        """Build a client from AKAHU_APP_TOKEN / AKAHU_USER_TOKEN."""
        return cls(
            app_token=os.environ["AKAHU_APP_TOKEN"],
            user_token=os.environ["AKAHU_USER_TOKEN"],
        )

    async def get_accounts(self) -> list[dict]:
        """Every connected account, balances included."""
        async with httpx2.AsyncClient(
            base_url=BASE_URL, headers=self._headers
        ) as client:
            response = await client.get("/accounts")
            response.raise_for_status()
            return response.json()["items"]
