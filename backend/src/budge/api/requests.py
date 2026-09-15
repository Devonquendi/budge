"""Charge requests: asking someone for their share, and following it through.

Nothing here stores a request's state. Every route that needs one folds the
event log with `charges.ledger.derive_state`, so what the app shows and what
actually happened cannot drift apart.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import col, select

from budge.auth import CurrentUserId, SessionDep
from budge.charges.ledger import derive_state, make_token, tally_bill
from budge.charges.money import parse_amount, split_evenly
from budge.db.models import (
    NAME_MAX,
    NOTE_MAX,
    TITLE_MAX,
    Bill,
    ChargeRequest,
    RequestEvent,
    User,
)

router = APIRouter(prefix="/requests", tags=["requests"])

NOT_FOUND = 404
MAX_PAYEES = 20

# What a payer may do to their own request, and what its creator may do. Split
# rather than checked inline so an unauthorised action is a lookup failure
# rather than a forgotten branch.
PAYEE_ACTIONS = {"mark-paid": "marked_paid", "decline": "declined"}
CREATOR_ACTIONS = {"confirm": "confirmed", "cancel": "cancelled", "reopen": "reopened"}


class Payee(BaseModel):
    email: EmailStr
    name: str = Field(default="", max_length=NAME_MAX)


class NewBill(BaseModel):
    """One bill, split into a request each. Amount as typed: "42", "$42.50"."""

    title: str = Field(max_length=TITLE_MAX)
    amount: str
    payees: list[Payee] = Field(min_length=1, max_length=MAX_PAYEES)
    # Splitting a $60 dinner three ways means three shares of $20, one of which
    # is the payer's own and is never requested.
    include_me: bool = True
    source_transaction_id: str | None = None


class Note(BaseModel):
    note: str = Field(default="", max_length=NOTE_MAX)


class Event(BaseModel):
    type: str
    actor: str
    note: str | None
    created_at: datetime


class RequestView(BaseModel):
    """One request, from either end of it."""

    id: int
    token: str
    title: str
    amount_cents: int
    bill_total_cents: int
    payee_email: str
    payee_name: str | None
    from_name: str
    from_email: str
    state: str
    created_at: datetime
    events: list[Event]


class Totals(BaseModel):
    owed: int
    claimed: int
    settled: int
    outstanding: int


class Inbox(BaseModel):
    """Both directions at once: the app shows them side by side."""

    sent: list[RequestView]
    received: list[RequestView]
    to_collect: Totals
    to_pay: Totals


async def _events(
    session: SessionDep, request_ids: list[int]
) -> dict[int, list[Event]]:
    if not request_ids:
        return {}
    rows = await session.exec(
        select(RequestEvent)
        .where(col(RequestEvent.request_id).in_(request_ids))
        .order_by(col(RequestEvent.id))
    )
    by_request: dict[int, list[Event]] = {id: [] for id in request_ids}
    for row in rows:
        by_request[row.request_id].append(
            Event.model_validate(row, from_attributes=True)
        )
    return by_request


def _view(
    request: ChargeRequest, bill: Bill, creator: User, events: list[Event]
) -> RequestView:
    return RequestView(
        id=request.id or 0,
        token=request.token,
        title=bill.title,
        amount_cents=request.amount_cents,
        bill_total_cents=bill.total_cents,
        payee_email=request.payee_email,
        payee_name=request.payee_name,
        from_name=creator.name or creator.email,
        from_email=creator.email,
        # The whole reason the event log exists: state is a function of it.
        state=derive_state([e.model_dump() for e in events]),
        created_at=request.created_at,
        events=events,
    )


def _totals(views: list[RequestView]) -> Totals:
    tally = tally_bill(
        [{"state": v.state, "amount_cents": v.amount_cents} for v in views]
    )
    return Totals(**tally._asdict())


@router.post("", status_code=201)
async def create_bill(
    body: NewBill, user_id: CurrentUserId, session: SessionDep
) -> list[RequestView]:
    """Splits one amount into a request per payee and returns them all."""
    total = parse_amount(body.amount)
    if total is None:
        raise HTTPException(status_code=400, detail="That isn't an amount")

    creator = await session.get(User, user_id)
    if creator is None:
        raise HTTPException(status_code=401)

    shares = split_evenly(total, len(body.payees) + (1 if body.include_me else 0))
    # The creator takes the first share, so any leftover cent lands on the
    # person doing the asking rather than on someone being asked.
    if body.include_me:
        shares = shares[1:]

    bill = Bill(
        creator_id=user_id,
        title=body.title.strip() or "Shared cost",
        total_cents=total,
        source_transaction_id=body.source_transaction_id,
    )
    session.add(bill)
    await session.commit()
    await session.refresh(bill)

    requests = [
        ChargeRequest(
            bill_id=bill.id or 0,
            token=make_token(),
            payee_email=str(payee.email).lower(),
            payee_name=payee.name.strip() or None,
            amount_cents=share,
        )
        for payee, share in zip(body.payees, shares, strict=True)
    ]
    session.add_all(requests)
    await session.commit()

    return [_view(r, bill, creator, []) for r in requests]


@router.get("")
async def get_inbox(user_id: CurrentUserId, session: SessionDep) -> Inbox:
    """Everything this user is owed, and everything they have been asked for."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401)

    bills = list(await session.exec(select(Bill).where(Bill.creator_id == user_id)))
    by_bill = {bill.id: bill for bill in bills}
    sent_rows = (
        list(
            await session.exec(
                select(ChargeRequest).where(
                    col(ChargeRequest.bill_id).in_(list(by_bill))
                )
            )
        )
        if by_bill
        else []
    )

    # Matched on email so a request can be sent to someone before they sign up,
    # and be waiting for them when they do.
    received_rows = list(
        await session.exec(
            select(ChargeRequest, Bill, User)
            .join(Bill, col(ChargeRequest.bill_id) == col(Bill.id))
            .join(User, col(Bill.creator_id) == col(User.id))
            .where(ChargeRequest.payee_email == user.email.lower())
        )
    )

    events = await _events(
        session,
        [r.id or 0 for r in sent_rows] + [r.id or 0 for r, _, _ in received_rows],
    )

    sent = [
        _view(r, by_bill[r.bill_id], user, events.get(r.id or 0, [])) for r in sent_rows
    ]
    received = [
        _view(r, bill, creator, events.get(r.id or 0, []))
        for r, bill, creator in received_rows
    ]
    sent.sort(key=lambda v: v.created_at, reverse=True)
    received.sort(key=lambda v: v.created_at, reverse=True)

    return Inbox(
        sent=sent,
        received=received,
        to_collect=_totals(sent),
        to_pay=_totals(received),
    )


async def _by_token(session: SessionDep, token: str) -> RequestView:
    row = (
        await session.exec(
            select(ChargeRequest, Bill, User)
            .join(Bill, col(ChargeRequest.bill_id) == col(Bill.id))
            .join(User, col(Bill.creator_id) == col(User.id))
            .where(ChargeRequest.token == token)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=NOT_FOUND, detail="No such request")
    request, bill, creator = row
    events = (await _events(session, [request.id or 0])).get(request.id or 0, [])
    return _view(request, bill, creator, events)


async def _record(
    session: SessionDep, request_id: int, type: str, actor: str, note: str
) -> None:
    session.add(
        RequestEvent(
            request_id=request_id, type=type, actor=actor, note=note.strip() or None
        )
    )
    await session.commit()


@router.get("/r/{token}")
async def get_by_token(token: str, session: SessionDep) -> RequestView:
    """The page a payer opens. No account needed: the link is the authority."""
    return await _by_token(session, token)


@router.post("/r/{token}/{action}")
async def act_as_payee(
    token: str, action: str, body: Note, session: SessionDep
) -> RequestView:
    """What the person being asked can do, without signing in."""
    type = PAYEE_ACTIONS.get(action)
    if type is None:
        raise HTTPException(status_code=NOT_FOUND, detail="No such action")
    view = await _by_token(session, token)
    await _record(session, view.id, type, "payee", body.note)
    return await _by_token(session, token)


@router.post("/{request_id}/{action}")
async def act_as_creator(
    request_id: int,
    action: str,
    body: Note,
    user_id: CurrentUserId,
    session: SessionDep,
) -> RequestView:
    """What the person owed can do. Their word is final: see CREATOR_ACTIONS."""
    type = CREATOR_ACTIONS.get(action)
    if type is None:
        raise HTTPException(status_code=NOT_FOUND, detail="No such action")

    row = (
        await session.exec(
            select(ChargeRequest, Bill)
            .join(Bill, col(ChargeRequest.bill_id) == col(Bill.id))
            .where(ChargeRequest.id == request_id, Bill.creator_id == user_id)
        )
    ).first()
    # Someone else's request is indistinguishable from one that doesn't exist.
    if row is None:
        raise HTTPException(status_code=NOT_FOUND, detail="No such request")

    await _record(session, request_id, type, "creator", body.note)
    return await _by_token(session, row[0].token)
