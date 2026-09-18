"""A preview deployment must not be able to reach a real bank."""

import pytest
from httpx import AsyncClient

from budge import credentials, environment
from budge.db import crypto
from budge.db.models import AkahuCredential

from .conftest import INVITE_CODE, Sessions

INVITE = {"invite_code": INVITE_CODE}


@pytest.fixture
def preview(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", environment.PREVIEW)
    monkeypatch.delenv(environment.ESCAPE_HATCH, raising=False)
    # Otherwise the demo switch would be doing the blocking, not the preview.
    monkeypatch.delenv(environment.DEMO_SWITCH, raising=False)


# Not one of the demo roster: a persona is handed the fixture feed, which
# would hide the thing these tests are checking.
REAL_USER = "someone.real@example.com"


async def sign_up(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/signup",
        json={"email": REAL_USER, "password": "hunter2hunter2"} | INVITE,
    )
    assert response.status_code == 201, response.text


def test_akahu_is_off_on_a_preview(preview: None) -> None:
    assert not environment.akahu_enabled()


def test_the_escape_hatch_turns_it_back_on(
    preview: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(environment.ESCAPE_HATCH, "1")
    assert environment.akahu_enabled()


def test_production_is_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.delenv(environment.DEMO_SWITCH, raising=False)
    assert environment.akahu_enabled()


async def test_a_preview_cannot_store_tokens(
    client: AsyncClient, preview: None
) -> None:
    await sign_up(client)
    response = await client.put(
        "/api/akahu", json={"app_token": "app_token_x", "user_token": "user_token_x"}
    )

    assert response.status_code == 403
    assert "preview" in response.json()["detail"]


async def test_a_preview_cannot_read_tokens_that_are_already_there(
    client: AsyncClient, db: Sessions, preview: None
) -> None:
    """The case that matters: production's rows, visible to a preview build."""
    await sign_up(client)

    async with db() as session:
        # Written as production would have written them, around the guard.
        session.add(
            AkahuCredential(
                user_id=1,
                app_token_encrypted=crypto.encrypt("app_token_real"),
                user_token_encrypted=crypto.encrypt("user_token_real"),
            )
        )
        await session.commit()

        assert await credentials.get(session, 1) is None
        # The one that counts: nothing is decrypted, so nothing calls Akahu.
        assert await credentials.client_for(session, 1) is None

    assert (await client.get("/api/akahu")).json() == {"connected": False}
    assert (await client.get("/api/accounts")).status_code == 409
