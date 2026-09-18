"""The request loop, driven end to end through the API."""

from httpx import AsyncClient

from .conftest import INVITE_CODE

INVITE = {"invite_code": INVITE_CODE}


async def sign_up(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/signup", json={"email": email, "password": "hunter2hunter2"} | INVITE
    )
    assert response.status_code == 201, response.text


async def sign_in(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "hunter2hunter2"}
    )
    assert response.status_code == 200, response.text


async def test_splitting_a_bill_sends_one_request_each(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    response = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "$100.00",
            "payees": [{"email": "neve@example.com"}, {"email": "tipene@example.com"}],
        },
    )

    assert response.status_code == 201, response.text
    requests = response.json()
    assert [r["amount_cents"] for r in requests] == [3333, 3333]
    assert {r["state"] for r in requests} == {"open"}
    # Distinct, so one payer's link never opens another's request.
    assert len({r["token"] for r in requests}) == 2


async def test_the_asker_absorbs_the_odd_cent(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    response = await client.post(
        "/api/requests",
        json={
            "title": "Coffee",
            "amount": "10.00",
            "payees": [{"email": "neve@example.com"}, {"email": "tipene@example.com"}],
        },
    )

    # 1000 over three is 334/333/333, and the 334 stays with the person asking.
    assert [r["amount_cents"] for r in response.json()] == [333, 333]


async def test_excluding_yourself_splits_only_between_payees(
    client: AsyncClient,
) -> None:
    await sign_up(client, "ara@example.com")
    response = await client.post(
        "/api/requests",
        json={
            "title": "Their share of the taxi",
            "amount": "30",
            "payees": [{"email": "neve@example.com"}, {"email": "tipene@example.com"}],
            "include_me": False,
        },
    )

    assert [r["amount_cents"] for r in response.json()] == [1500, 1500]


async def test_a_payer_needs_no_account(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
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

    # Signed out, and still able to see it and act on it. This is the whole
    # point of the link.
    seen = await client.get(f"/api/requests/r/{token}")
    assert seen.status_code == 200, seen.text
    assert seen.json()["amount_cents"] == 3000
    assert seen.json()["from_email"] == "ara@example.com"

    paid = await client.post(f"/api/requests/r/{token}/mark-paid", json={})
    assert paid.json()["state"] == "marked_paid"


async def test_the_creator_has_the_final_say(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )
    request = created.json()[0]
    await client.post(f"/api/requests/r/{request['token']}/mark-paid", json={})

    confirmed = await client.post(f"/api/requests/{request['id']}/confirm", json={})
    assert confirmed.json()["state"] == "confirmed"

    # A payer cannot walk back money the person owed says arrived.
    declined = await client.post(f"/api/requests/r/{request['token']}/decline", json={})
    assert declined.json()["state"] == "confirmed"


async def test_nobody_can_act_on_someone_elses_request(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )
    request_id = created.json()[0]["id"]
    await client.post("/api/auth/logout")
    await sign_up(client, "someone.else@example.com")

    response = await client.post(f"/api/requests/{request_id}/confirm", json={})
    assert response.status_code == 404


async def test_the_inbox_shows_both_directions(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )
    await client.post("/api/auth/logout")

    await sign_up(client, "neve@example.com")
    inbox = (await client.get("/api/requests")).json()

    assert inbox["sent"] == []
    assert len(inbox["received"]) == 1
    # Matched on email, so it was waiting before the account existed.
    assert inbox["received"][0]["title"] == "Power, August"
    assert inbox["to_pay"]["outstanding"] == 3000
    assert inbox["to_collect"]["outstanding"] == 0


async def test_a_cancelled_request_leaves_the_tally(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}, {"email": "dev@example.com"}],
        },
    )
    await client.post(f"/api/requests/{created.json()[0]['id']}/cancel", json={})

    inbox = (await client.get("/api/requests")).json()
    assert inbox["to_collect"]["outstanding"] == 2000


async def test_a_bad_amount_is_refused(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    response = await client.post(
        "/api/requests",
        json={
            "title": "Power",
            "amount": "sixty dollars",
            "payees": [{"email": "neve@example.com"}],
        },
    )
    assert response.status_code == 400


async def test_an_unknown_token_is_not_found(client: AsyncClient) -> None:
    assert (await client.get("/api/requests/r/nosuchtoken")).status_code == 404


async def test_a_bill_remembers_the_spend_it_came_from(client: AsyncClient) -> None:
    """Splitting from the ledger, rather than typing an amount in."""
    await sign_up(client, "ara@example.com")
    created = await client.post(
        "/api/requests",
        json={
            "title": "Fern & Fig Grocers",
            "amount": "93.02",
            "payees": [{"email": "neve@example.com"}],
            "source_transaction_id": "txn_demo_acc_ara_everyday_4",
        },
    )

    assert created.status_code == 201, created.text
    request = created.json()[0]
    assert request["source_transaction_id"] == "txn_demo_acc_ara_everyday_4"

    # It survives to both ends of the request, not just the reply to creating it.
    inbox = (await client.get("/api/requests")).json()
    assert inbox["sent"][0]["source_transaction_id"] == request["source_transaction_id"]

    seen = await client.get(f"/api/requests/r/{request['token']}")
    assert seen.json()["source_transaction_id"] == request["source_transaction_id"]


async def test_a_typed_in_bill_has_no_spend_behind_it(client: AsyncClient) -> None:
    await sign_up(client, "ara@example.com")
    created = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": "neve@example.com"}],
        },
    )

    assert created.json()[0]["source_transaction_id"] is None
