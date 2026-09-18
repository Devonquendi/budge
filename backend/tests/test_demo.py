"""The demo personas, and the ways into them that must not exist."""

import pytest
from httpx import AsyncClient
from sqlmodel import select

from budge import environment
from budge.db.models import Contact, Group, GroupMember

from .conftest import Sessions


async def test_signing_in_as_a_persona_seeds_their_flat(client: AsyncClient) -> None:
    response = await client.post("/api/demo/session", json={"email": "ara@example.com"})

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Ara Whitcombe"
    # The fixture feed stands in for a bank, so the dashboard works too.
    assert response.json()["onboarded"] is True

    inbox = (await client.get("/api/requests")).json()
    assert inbox["sent"], "Ara is owed for the power and the internet"
    assert inbox["received"], "and owes for the car and the groceries"


async def test_seeding_twice_changes_nothing(client: AsyncClient) -> None:
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    first = (await client.get("/api/requests")).json()

    await client.post("/api/demo/session", json={"email": "neve@example.com"})
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    again = (await client.get("/api/requests")).json()

    assert len(again["sent"]) == len(first["sent"])
    assert len(again["received"]) == len(first["received"])


async def test_a_persona_has_no_password_that_works(client: AsyncClient) -> None:
    """The row outlives the endpoint, so it must not be a way in on its own."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    await client.post("/api/auth/logout")

    for guess in ("demo", "", "ara@example.com", "password"):
        response = await client.post(
            "/api/auth/login", json={"email": "ara@example.com", "password": guess}
        )
        assert response.status_code == 401


async def test_a_deployment_without_the_switch_has_no_demo(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off by default, wherever it is running."""
    monkeypatch.delenv(environment.DEMO_SWITCH, raising=False)

    assert (await client.get("/api/demo/personas")).json() == []
    response = await client.post("/api/demo/session", json={"email": "ara@example.com"})
    assert response.status_code == 404


async def test_the_demo_and_a_real_bank_are_never_both_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invented people and live bank tokens do not share a deployment."""
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv(environment.DEMO_SWITCH, "1")
    assert not environment.akahu_enabled()

    # Even the preview escape hatch does not lift it.
    monkeypatch.setenv(environment.ESCAPE_HATCH, "1")
    assert not environment.akahu_enabled()


async def test_an_invented_persona_is_refused(client: AsyncClient) -> None:
    response = await client.post("/api/demo/session", json={"email": "me@example.com"})
    assert response.status_code == 404


def test_the_switch_is_what_turns_the_demo_on() -> None:
    assert environment.demo_enabled()


async def test_a_demo_seeded_before_a_feature_existed_catches_up(
    client: AsyncClient, db: Sessions
) -> None:
    """The bug this guards: one "already seeded" flag for several things.

    A demo database outlives the deploy that made it. Contacts arrived after
    bills did, and a single flag meant they never appeared on any demo that had
    already been used.
    """
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    # Wind it back to what an older deploy would have left: bills, no contacts.
    async with db() as session:
        for contact in await session.exec(select(Contact)):
            await session.delete(contact)
        for member in await session.exec(select(GroupMember)):
            await session.delete(member)
        for group in await session.exec(select(Group)):
            await session.delete(group)
        await session.commit()

    assert (await client.get("/api/people")).json()["contacts"] == []

    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    people = (await client.get("/api/people")).json()
    assert len(people["contacts"]) == 4, "signing in again should fill them in"
    assert len(people["groups"]) == 1
    # And it must not have duplicated the bills while it was at it.
    assert len((await client.get("/api/requests")).json()["sent"]) == 7
