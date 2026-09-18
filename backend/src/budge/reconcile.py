"""Noticing that money has arrived, and asking whether it settles a request.

Nothing here closes a request on its own. `charges.feed.match_credit` returns
nothing rather than guess when a credit could belong to more than one person,
and even a confident match is put to the person owed as a question. Telling
somebody they have been paid when they have not is the worst thing this
application could do, and no amount of matching makes that acceptable.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.akahu.models import Transaction
from budge.charges.feed import find_internal_transfers, match_credit
from budge.charges.ledger import derive_state
from budge.db.models import Bill, ChargeRequest, MatchSuggestion, RequestEvent

# Credits older than this are not worth offering: a request open that long is
# being chased by other means, and an ancient match reads as noise.
CONSIDER_DAYS = 45


def _rows(transactions: Sequence[Transaction]) -> list[dict]:
    """Akahu transactions as the plain mappings charges.feed works in."""
    return [
        {
            "id": t.id,
            "account_id": t.account_id,
            "connection_id": t.connection_id,
            "amount_cents": int(t.amount * 100),
            "date": t.date,
            "description": t.description,
        }
        for t in transactions
    ]


def internal_ids(transactions: Sequence[Transaction]) -> set[str]:
    """Transactions that are this user moving their own money between accounts.

    Both legs, so neither the debit nor the credit counts as spending or income.
    """
    return {str(one) for one in find_internal_transfers(_rows(transactions))}


async def _open_requests(
    session: AsyncSession, user_id: int
) -> list[tuple[ChargeRequest, dict]]:
    """Requests this user is owed that nobody has confirmed arriving."""
    rows = list(
        await session.exec(
            select(ChargeRequest, Bill)
            .join(Bill, col(ChargeRequest.bill_id) == col(Bill.id))
            .where(Bill.creator_id == user_id)
        )
    )
    if not rows:
        return []

    events = await session.exec(
        select(RequestEvent).where(
            col(RequestEvent.request_id).in_([r.id or 0 for r, _ in rows])
        )
    )
    by_request: dict[int, list[dict]] = {}
    for event in sorted(events, key=lambda e: e.id or 0):
        by_request.setdefault(event.request_id, []).append({"type": event.type})

    out = []
    for request, _bill in rows:
        state = derive_state(by_request.get(request.id or 0, []))
        # A confirmed or cancelled request is finished; a declined one is still
        # open as far as the money is concerned, and a credit may yet settle it.
        if state in ("confirmed", "cancelled"):
            continue
        out.append(
            (
                request,
                {
                    "amount_cents": request.amount_cents,
                    "debtor_name": request.payee_name or request.payee_email,
                    "id": request.id,
                },
            )
        )
    return out


async def scan(
    session: AsyncSession, user_id: int, transactions: Sequence[Transaction]
) -> int:
    """Looks for credits that settle open requests. Returns how many are new.

    Idempotent: a suggestion already raised for a credit, accepted or dismissed,
    is never raised again. Reading the feed twice must not pester anybody twice.
    """
    open_requests = await _open_requests(session, user_id)
    if not open_requests:
        return 0

    by_id = {row["id"]: request for request, row in open_requests}
    candidates = [row for _, row in open_requests]

    internal = internal_ids(transactions)
    seen = {
        (s.request_id, s.transaction_id)
        for s in await session.exec(
            select(MatchSuggestion).where(MatchSuggestion.user_id == user_id)
        )
    }

    cutoff = _days_ago(transactions, CONSIDER_DAYS)
    made = 0
    for transaction in transactions:
        cents = int(transaction.amount * 100)
        # Money out is not somebody paying you, and a transfer between your own
        # accounts is not either, however neatly the amount lines up.
        if cents <= 0 or transaction.id in internal:
            continue
        if cutoff is not None and transaction.date < cutoff:
            continue

        credit = {
            "amount_cents": cents,
            "description": transaction.description,
            "counterparty": transaction.merchant.name if transaction.merchant else "",
        }
        hit = match_credit(credit, candidates)
        if hit is None:
            continue

        key = (hit["id"], transaction.id)
        if key in seen:
            continue
        seen.add(key)

        request = by_id[hit["id"]]
        session.add(
            MatchSuggestion(
                user_id=user_id,
                request_id=request.id or 0,
                transaction_id=transaction.id,
                amount_cents=cents,
                description=transaction.description,
                occurred_at=transaction.date.replace(tzinfo=None),
            )
        )
        made += 1

    if made:
        await session.commit()
    return made


def _days_ago(transactions: Sequence[Transaction], days: int) -> datetime | None:
    """Measured from the newest transaction, not from now.

    The fixture feed and a real one can both sit slightly in the past, and a
    cutoff anchored to the wall clock would quietly consider nothing.
    """
    if not transactions:
        return None
    newest = max(t.date for t in transactions)
    return newest - timedelta(days=days)
