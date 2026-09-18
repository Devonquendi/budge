"""Where money goes, and whether the bank still says the account is yours."""

import pytest
from httpx import AsyncClient

from budge import payout
from budge.db.models import User

from .conftest import INVITE_CODE, Sessions

INVITE = {"invite_code": INVITE_CODE}
# Ara's everyday account in the fixture feed, as the browser would send it.
ARA_ACCOUNT = "12-3400-4339250-00"


async def sign_up(client: AsyncClient, email: str = "someone@example.com") -> None:
    response = await client.post(
        "/api/auth/signup", json={"email": email, "password": "hunter2hunter2"} | INVITE
    )
    assert response.status_code == 201, response.text


async def test_an_account_number_is_normalised_before_it_is_stored(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    response = await client.put(
        "/api/auth/me/payout",
        json={"account": "12 3400 4339250 00", "name": "A Someone"},
    )

    assert response.status_code == 200, response.text
    # Stored bank-branch-account-suffix however it was typed.
    assert response.json()["payout"]["account"] == "12-3400-4339250-00"
    assert response.json()["payout"]["name"] == "A Someone"


async def test_something_that_is_not_an_account_number_is_refused(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    response = await client.put("/api/auth/me/payout", json={"account": "my bank"})

    assert response.status_code == 400
    assert "New Zealand account number" in response.json()["detail"]


async def test_an_account_can_be_saved_without_a_bank_to_check_it(
    client: AsyncClient,
) -> None:
    """Plenty of people want paying into an account they have not connected."""
    await sign_up(client)
    response = await client.put("/api/auth/me/payout", json={"account": ARA_ACCOUNT})

    assert response.status_code == 200
    assert response.json()["payout"]["account"] == ARA_ACCOUNT
    # Saved, but nobody has confirmed it is theirs.
    assert response.json()["payout"]["verified"] is False


async def test_clearing_it_leaves_nowhere_to_pay(client: AsyncClient) -> None:
    await sign_up(client)
    await client.put("/api/auth/me/payout", json={"account": ARA_ACCOUNT})

    response = await client.put("/api/auth/me/payout", json={"account": ""})
    assert response.json()["payout"]["account"] is None
    assert response.json()["payout"]["verified"] is False


async def test_a_demo_persona_is_verified_against_their_own_feed(
    client: AsyncClient,
) -> None:
    """The fixture feed is the bank, and it returns this account number."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    me = (await client.get("/api/auth/me")).json()
    assert me["payout"]["account"] == ARA_ACCOUNT
    assert me["payout"]["verified"] is True
    assert me["payout"]["revoked"] is False


async def test_a_request_carries_the_details_a_payer_needs(
    client: AsyncClient,
) -> None:
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )

    pay_to = created.json()[0]["pay_to"]
    assert pay_to["account"] == ARA_ACCOUNT
    assert pay_to["name"] == "Ara Whitcombe"
    # Twelve characters, because bank reference fields truncate silently.
    assert pay_to["reference"] == "Power August"
    assert pay_to["reference"] == pay_to["reference"].strip()
    assert pay_to["verified"] is True


async def test_the_payer_sees_them_without_signing_in(client: AsyncClient) -> None:
    """The whole point: the link has to be enough to pay from."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "stranger@example.com"}],
        },
    )
    token = created.json()[0]["token"]
    await client.post("/api/auth/logout")

    seen = await client.get(f"/api/requests/r/{token}")
    assert seen.json()["pay_to"]["account"] == ARA_ACCOUNT


async def test_a_request_from_someone_with_no_account_says_so(
    client: AsyncClient,
) -> None:
    """Still a valid request: people settle up in cash, and that is fine."""
    await sign_up(client)
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )

    assert created.json()[0]["pay_to"] is None


async def test_a_disconnected_account_is_flagged(
    client: AsyncClient, db: Sessions
) -> None:
    """The case worth catching: requests pointing at an account that went away."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    assert (await client.get("/api/auth/me")).json()["payout"]["revoked"] is False

    async with db() as session:
        user = await session.get(User, 1)
        assert user is not None
        user.payout_account = "12-3400-9999999-00"
        session.add(user)
        await session.commit()

    me = (await client.get("/api/auth/me")).json()
    assert me["payout"]["revoked"] is True


async def test_a_bank_going_quiet_is_not_evidence_of_anything(
    client: AsyncClient, db: Sessions, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No connection to check against must not cry wolf on every request."""
    await sign_up(client)
    await client.put("/api/auth/me/payout", json={"account": ARA_ACCOUNT})

    async with db() as session:
        user = await session.get(User, 1)
        assert user is not None
        from datetime import UTC, datetime

        user.payout_verified_at = datetime.now(UTC)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # No Akahu connection, so connected_accounts is empty.
        assert await payout.still_verified(session, user) is True
