"""Noticing money has arrived, and asking rather than asserting."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient

from budge import reconcile
from budge.akahu.models import Merchant, Transaction

from .conftest import INVITE_CODE, Sessions

INVITE = {"invite_code": INVITE_CODE}


def credit(
    amount: str, description: str, *, days_ago: int = 1, merchant: str | None = None
) -> Transaction:
    return Transaction(
        id=f"txn_{description}_{amount}_{days_ago}".replace(" ", "_"),
        account_id="acc_1",
        account_name="Everyday",
        currency="NZD",
        connection_id="conn_1",
        date=datetime.now(UTC) - timedelta(days=days_ago),
        description=description,
        amount=Decimal(amount),
        type="CREDIT",
        merchant=Merchant(name=merchant) if merchant else None,
    )


async def sign_up(client: AsyncClient, email: str = "ara@example.com") -> None:
    response = await client.post(
        "/api/auth/signup", json={"email": email, "password": "hunter2hunter2"} | INVITE
    )
    assert response.status_code == 201, response.text


async def ask(client: AsyncClient, amount: str, *payees: str) -> list[dict]:
    response = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": amount,
            "payees": [
                {"email": email, "name": email.split("@")[0]} for email in payees
            ],
            "include_me": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_a_credit_matching_one_request_is_offered(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com")

    async with db() as session:
        found = await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])
    assert found == 1

    suggestions = (await client.get("/api/requests/suggestions")).json()
    assert len(suggestions) == 1
    assert suggestions[0]["amount_cents"] == 6000
    assert suggestions[0]["request"]["payee_email"] == "neve@example.com"
    # Offered, not applied. The request has not moved.
    assert suggestions[0]["request"]["state"] == "open"


async def test_accepting_one_settles_the_request(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com")
    async with db() as session:
        await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])

    suggestion = (await client.get("/api/requests/suggestions")).json()[0]
    answered = await client.post(f"/api/requests/suggestions/{suggestion['id']}/accept")

    assert answered.status_code == 200, answered.text
    assert answered.json()["state"] == "confirmed"
    # And it stops being asked about.
    assert (await client.get("/api/requests/suggestions")).json() == []


async def test_dismissing_one_leaves_the_request_alone(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com")
    async with db() as session:
        await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])

    suggestion = (await client.get("/api/requests/suggestions")).json()[0]
    answered = await client.post(
        f"/api/requests/suggestions/{suggestion['id']}/dismiss"
    )

    assert answered.json()["state"] == "open"
    assert (await client.get("/api/requests/suggestions")).json() == []


async def test_a_dismissed_credit_is_not_offered_again(
    client: AsyncClient, db: Sessions
) -> None:
    """Reading the feed twice must not pester anybody twice."""
    await sign_up(client)
    await ask(client, "60", "neve@example.com")
    async with db() as session:
        await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])

    suggestion = (await client.get("/api/requests/suggestions")).json()[0]
    await client.post(f"/api/requests/suggestions/{suggestion['id']}/dismiss")

    async with db() as session:
        again = await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])
    assert again == 0
    assert (await client.get("/api/requests/suggestions")).json() == []


async def test_an_ambiguous_amount_is_left_to_a_human(
    client: AsyncClient, db: Sessions
) -> None:
    """Two people owing the same amount, and nothing in the credit to separate them."""
    await sign_up(client)
    await ask(client, "60", "neve@example.com", "tipene@example.com")

    async with db() as session:
        found = await reconcile.scan(session, 1, [credit("30.00", "ONLINE PAYMENT")])

    assert found == 0, "guessing here would tell someone they had paid when they hadn't"


async def test_a_name_in_the_description_breaks_the_tie(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com", "tipene@example.com")

    async with db() as session:
        found = await reconcile.scan(session, 1, [credit("30.00", "FROM NEVE")])

    assert found == 1
    assert (await client.get("/api/requests/suggestions")).json()[0]["request"][
        "payee_email"
    ] == "neve@example.com"


async def test_money_going_out_is_never_a_payment_to_you(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com")

    async with db() as session:
        found = await reconcile.scan(session, 1, [credit("-60.00", "NEVE C")])

    assert found == 0


async def test_a_settled_request_is_not_matched_again(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    requests = await ask(client, "60", "neve@example.com")
    await client.post(f"/api/requests/{requests[0]['id']}/confirm", json={})

    async with db() as session:
        found = await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])

    assert found == 0


async def test_a_transfer_between_your_own_accounts_is_not_a_payment(
    client: AsyncClient, db: Sessions
) -> None:
    """The same amount, moved between your own accounts, on different banks."""
    await sign_up(client)
    await ask(client, "60", "neve@example.com")

    out = credit("-60.00", "TO SAVINGS")
    incoming = credit("60.00", "FROM EVERYDAY")
    incoming.connection_id = "conn_2"
    incoming.account_id = "acc_2"

    async with db() as session:
        found = await reconcile.scan(session, 1, [out, incoming])

    assert found == 0


async def test_both_legs_of_a_transfer_are_flagged() -> None:
    out = credit("-150.00", "TO SAVINGS")
    incoming = credit("150.00", "FROM EVERYDAY")
    incoming.connection_id = "conn_2"

    internal = reconcile.internal_ids([out, incoming])
    assert internal == {out.id, incoming.id}


async def test_scanning_without_a_bank_is_not_an_error(client: AsyncClient) -> None:
    await sign_up(client)
    response = await client.post("/api/requests/suggestions/scan")

    assert response.status_code == 200, response.text
    assert response.json() == {"found": 0}


async def test_nobody_answers_someone_elses_suggestion(
    client: AsyncClient, db: Sessions
) -> None:
    await sign_up(client)
    await ask(client, "60", "neve@example.com")
    async with db() as session:
        await reconcile.scan(session, 1, [credit("60.00", "NEVE C")])
    suggestion = (await client.get("/api/requests/suggestions")).json()[0]

    await client.post("/api/auth/logout")
    await sign_up(client, "someone.else@example.com")

    response = await client.post(f"/api/requests/suggestions/{suggestion['id']}/accept")
    assert response.status_code == 404


async def test_the_demo_has_something_real_to_reconcile(client: AsyncClient) -> None:
    """Neve says she paid Ara for the power, so the money is in Ara's feed.

    Not staged: the credit exists because of the claim, and the matcher finds
    it the same way it would find a real one.
    """
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    scanned = await client.post("/api/requests/suggestions/scan")
    assert scanned.status_code == 200, scanned.text
    assert scanned.json()["found"] >= 1

    suggestions = (await client.get("/api/requests/suggestions")).json()
    match = next(
        s for s in suggestions if s["request"]["payee_email"] == "neve@example.com"
    )
    assert match["request"]["state"] == "marked_paid"
    assert match["amount_cents"] == match["request"]["amount_cents"]

    settled = await client.post(f"/api/requests/suggestions/{match['id']}/accept")
    assert settled.json()["state"] == "confirmed"


async def test_scanning_the_demo_twice_offers_nothing_new(
    client: AsyncClient,
) -> None:
    await client.post("/api/demo/session", json={"email": "ara@example.com"})
    first = (await client.post("/api/requests/suggestions/scan")).json()["found"]
    second = (await client.post("/api/requests/suggestions/scan")).json()["found"]

    assert first >= 1
    assert second == 0


async def test_a_personas_own_transfer_to_savings_is_not_spending(
    client: AsyncClient,
) -> None:
    """The dashboard counted it, which made it the biggest category of the month."""
    await client.post("/api/demo/session", json={"email": "ara@example.com"})

    history = (await client.get("/api/transactions?days=90")).json()
    transfers = [
        t for t in history["transactions"] if "SAVINGS" in t["description"].upper()
    ]

    assert transfers, "the fixture feed carries a standing transfer to savings"
    assert all(t["internal"] for t in transfers)

    # And a credit from a flatmate is emphatically not internal.
    paid = [t for t in history["transactions"] if t["description"] == "NEVE CALLAGHAN"]
    assert paid and not any(t["internal"] for t in paid)
