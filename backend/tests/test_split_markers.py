"""A transaction you have split should say so, on every screen that shows it."""

from httpx import AsyncClient

from .conftest import INVITE_CODE

INVITE = {"invite_code": INVITE_CODE}
TXN = "txn_demo_acc_demo_ara_everyday_1"


async def sign_up(client: AsyncClient, email: str = "ara@example.com") -> None:
    response = await client.post(
        "/api/auth/signup", json={"email": email, "password": "hunter2hunter2"} | INVITE
    )
    assert response.status_code == 201, response.text


async def split(
    client: AsyncClient, amount: str, *payees: str, txn: str = TXN
) -> list[dict]:
    response = await client.post(
        "/api/requests",
        json={
            "title": "Fern & Fig Grocers",
            "amount": amount,
            "payees": [{"email": email} for email in payees],
            "include_me": False,
            "source_transaction_id": txn,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_a_split_transaction_reports_what_came_of_it(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    await split(client, "90", "neve@example.com", "tipene@example.com")

    summaries = (await client.get("/api/requests/by-transaction")).json()
    assert len(summaries) == 1
    assert summaries[0]["transaction_id"] == TXN
    assert summaries[0]["people"] == 2
    assert summaries[0]["asked_cents"] == 9000
    assert summaries[0]["outstanding_cents"] == 9000
    assert summaries[0]["settled_cents"] == 0

    # The shares ride along, so asking again can show what was already asked.
    assert {s["who"] for s in summaries[0]["shares"]} == {
        "neve@example.com",
        "tipene@example.com",
    }
    assert all(s["state"] == "open" for s in summaries[0]["shares"])
    assert all(s["token"] for s in summaries[0]["shares"])


async def test_confirming_moves_it_from_outstanding_to_settled(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    requests = await split(client, "90", "neve@example.com", "tipene@example.com")
    await client.post(f"/api/requests/{requests[0]['id']}/confirm", json={})

    summary = (await client.get("/api/requests/by-transaction")).json()[0]
    assert summary["settled_cents"] == 4500
    assert summary["outstanding_cents"] == 4500
    assert summary["people"] == 2
    assert sorted(s["state"] for s in summary["shares"]) == ["confirmed", "open"]


async def test_a_cancelled_request_stops_counting(client: AsyncClient) -> None:
    """Withdrawn, so it should not still hang off the transaction it came from."""
    await sign_up(client)
    requests = await split(client, "90", "neve@example.com", "tipene@example.com")
    await client.post(f"/api/requests/{requests[0]['id']}/cancel", json={})

    summary = (await client.get("/api/requests/by-transaction")).json()[0]
    assert summary["people"] == 1
    assert summary["asked_cents"] == 4500
    assert len(summary["shares"]) == 1, "a withdrawn request is not still listed"


async def test_splitting_the_same_transaction_twice_adds_up(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    await split(client, "90", "neve@example.com")
    await split(client, "30", "tipene@example.com")

    summaries = (await client.get("/api/requests/by-transaction")).json()
    assert len(summaries) == 1, "still one transaction, however many times it was split"
    assert summaries[0]["people"] == 2
    assert summaries[0]["asked_cents"] == 12000


async def test_a_typed_in_bill_is_not_attached_to_any_transaction(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    await client.post(
        "/api/requests",
        json={
            "title": "Power",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )

    assert (await client.get("/api/requests/by-transaction")).json() == []


async def test_nobody_sees_what_somebody_else_split(client: AsyncClient) -> None:
    await sign_up(client)
    await split(client, "90", "neve@example.com")
    await client.post("/api/auth/logout")
    await sign_up(client, "someone.else@example.com")

    assert (await client.get("/api/requests/by-transaction")).json() == []
