"""The invented bank feed: no Akahu, no network, and the same past every time."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from budge import demo
from budge.charges.feed import find_internal_transfers

ARA = "ara@example.com"
WINDOW = timedelta(days=90)


def _window() -> tuple[datetime, datetime]:
    end = datetime.now(UTC)
    return end - WINDOW, end


def test_a_persona_has_two_accounts_at_two_banks() -> None:
    accounts = demo.accounts_for(ARA)

    assert len(accounts) == 2
    assert len({account.connection_name for account in accounts}) == 2
    assert all(account.currency == "NZD" for account in accounts)


def test_the_same_person_has_the_same_history_twice() -> None:
    start, end = _window()
    first = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)
    again = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)

    assert [t.id for t in first] == [t.id for t in again]
    assert [t.amount for t in first] == [t.amount for t in again]


def test_two_people_do_not_share_a_history() -> None:
    start, end = _window()
    ara = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)
    neve = demo.transactions_for(
        "neve@example.com", demo.accounts_for("neve@example.com"), start, end
    )

    assert [t.amount for t in ara] != [t.amount for t in neve]


def test_the_feed_is_newest_first_and_inside_the_window() -> None:
    start, end = _window()
    transactions = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)

    assert transactions, "a persona should have a few months of spending"
    assert all(start <= t.date <= end for t in transactions)
    assert [t.date for t in transactions] == sorted(
        (t.date for t in transactions), reverse=True
    )


def test_money_goes_both_ways() -> None:
    start, end = _window()
    transactions = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)

    assert any(t.amount < 0 for t in transactions), "spending"
    assert any(t.amount > 0 for t in transactions), "pay going in"


def test_the_transfers_between_their_own_accounts_are_detectable() -> None:
    """What charges.feed.find_internal_transfers is for, on real fixture data."""
    start, end = _window()
    transactions = demo.transactions_for(ARA, demo.accounts_for(ARA), start, end)

    rows = [
        {
            "id": t.id,
            "account_id": t.account_id,
            "connection_id": t.connection_id,
            "amount_cents": int(t.amount * 100),
            "date": t.date.isoformat(),
        }
        for t in transactions
    ]
    assert find_internal_transfers(rows), "the standing transfer to savings"


def test_only_the_roster_gets_a_feed() -> None:
    assert demo.client_for(ARA) is not None
    assert demo.client_for("someone.real@example.com") is None


def test_production_has_no_fixture_feed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Belt and braces: a persona row in production still reaches no bank."""
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert demo.client_for(ARA) is None


async def test_a_signed_in_persona_sees_accounts_and_transactions(
    client: AsyncClient,
) -> None:
    await client.post("/api/demo/session", json={"email": ARA})

    accounts = await client.get("/api/accounts")
    assert accounts.status_code == 200, accounts.text
    assert len(accounts.json()) == 2

    history = await client.get("/api/transactions?days=90")
    assert history.status_code == 200, history.text
    assert history.json()["transactions"], "a persona should have spending to show"
