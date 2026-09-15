"""The demo personas, and the ways into them that must not exist."""

import pytest
from httpx import AsyncClient

from budge import environment


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


async def test_production_has_no_demo_at_all(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERCEL_ENV", "production")

    assert (await client.get("/api/demo/personas")).json() == []
    response = await client.post("/api/demo/session", json={"email": "ara@example.com"})
    assert response.status_code == 404


async def test_an_invented_persona_is_refused(client: AsyncClient) -> None:
    response = await client.post("/api/demo/session", json={"email": "me@example.com"})
    assert response.status_code == 404


def test_demo_is_on_outside_production() -> None:
    assert environment.vercel_env() == "development"
