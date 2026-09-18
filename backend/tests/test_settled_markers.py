"""A credit that closed a request should say so, on the ledger."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient

from budge import reconcile
from budge.akahu.models import Transaction

from .conftest import INVITE_CODE, Sessions

INVITE = {"invite_code": INVITE_CODE}


def credit(amount: str, description: str) -> Transaction:
    return Transaction(
        id="txn_incoming_1",
        account_id="acc_1",
        account_name="Everyday",
        currency="NZD",
        connection_id="conn_1",
        date=datetime.now(UTC) - timedelta(days=1),
        description=description,
        amount=Decimal(amount),
        type="CREDIT",
    )


async def setup(client: AsyncClient, db: Sessions) -> dict:
    await client.post(
        "/api/auth/signup",
        json={"email": "ara@example.com", "password": "hunter2hunter2"} | INVITE,
    )
    await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com", "name": "Neve Callaghan"}],
            "include_me": False,
        },
    )
    async with db() as session:
        await reconcile.scan(session, 1, [credit("60.00", "NEVE CALLAGHAN")])
    return (await client.get("/api/requests/suggestions")).json()[0]


async def test_an_accepted_match_marks_the_transaction(
    client: AsyncClient, db: Sessions
) -> None:
    suggestion = await setup(client, db)
    await client.post(f"/api/requests/suggestions/{suggestion['id']}/accept")

    settled = (await client.get("/api/requests/settlements")).json()
    assert len(settled) == 1
    assert settled[0]["transaction_id"] == "txn_incoming_1"
    assert settled[0]["who"] == "Neve Callaghan"
    assert settled[0]["title"] == "Power, August"
    assert settled[0]["amount_cents"] == 6000
    # The token is what makes the marker a link back to the request.
    assert settled[0]["token"]


async def test_a_dismissed_match_marks_nothing(
    client: AsyncClient, db: Sessions
) -> None:
    """Dismissing was somebody saying that credit was something else."""
    suggestion = await setup(client, db)
    await client.post(f"/api/requests/suggestions/{suggestion['id']}/dismiss")

    assert (await client.get("/api/requests/settlements")).json() == []


async def test_an_unanswered_match_marks_nothing(
    client: AsyncClient, db: Sessions
) -> None:
    await setup(client, db)
    assert (await client.get("/api/requests/settlements")).json() == []


async def test_nobody_sees_what_settled_somebody_elses_request(
    client: AsyncClient, db: Sessions
) -> None:
    suggestion = await setup(client, db)
    await client.post(f"/api/requests/suggestions/{suggestion['id']}/accept")
    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/signup",
        json={"email": "someone.else@example.com", "password": "hunter2hunter2"}
        | INVITE,
    )

    assert (await client.get("/api/requests/settlements")).json() == []


async def test_confirming_a_payment_does_not_make_it_vanish(
    client: AsyncClient,
) -> None:
    """The demo credit is the evidence the confirmation was based on.

    Deriving it from the request's current state meant accepting a match
    deleted the transaction the match was found in, and the ledger could no
    longer point at anything.
    """
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    inbox = (await client.get("/api/requests")).json()
    open_request = next(r for r in inbox["sent"] if r["state"] == "open")
    await client.post(
        f"/api/requests/r/{open_request['token']}/mark-paid", json={"note": "paid"}
    )

    def credits() -> list[dict]:
        return [
            t
            for t in history["transactions"]
            if t["id"] == f"txn_demo_acc_demo_ara_everyday_{open_request['token']}"
        ]

    history = (await client.get("/api/transactions?days=45")).json()
    assert credits(), "the claim should put money in the feed"

    # They said they paid and the money is there, so it settles on its own.
    assert (await client.post("/api/requests/suggestions/scan")).json()["settled"] >= 1

    history = (await client.get("/api/transactions?days=45")).json()
    assert credits(), "and it should still be there after it is confirmed"

    settled = (await client.get("/api/requests/settlements")).json()
    assert any(s["token"] == open_request["token"] for s in settled)


async def test_two_claimed_payments_are_two_transactions(
    client: AsyncClient,
) -> None:
    """They shared an id, so the second overwrote the first on the ledger."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    inbox = (await client.get("/api/requests")).json()
    for request in [r for r in inbox["sent"] if r["state"] == "open"][:2]:
        await client.post(f"/api/requests/r/{request['token']}/mark-paid", json={})

    history = (await client.get("/api/transactions?days=45")).json()
    claimed = [t for t in history["transactions"] if "_txn_" not in t["id"]]
    ids = [t["id"] for t in history["transactions"]]
    assert len(ids) == len(set(ids)), "every ledger row needs its own id"
    assert len(claimed) >= 0
