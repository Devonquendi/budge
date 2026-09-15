"""Invented people with invented bills, so the request loop can be played with.

Off in production and on everywhere else, decided by VERCEL_ENV. The personas
are a fixed roster on @example.com, which RFC 2606 reserves and no one can ever
receive mail at, and seeding is idempotent: signing in as the same persona twice
adds nothing. None of them has Akahu credentials or a password anyone knows, so
no demo session can reach a real bank and no demo row is a way into the app.
"""

import os
import secrets

from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.auth import password_hash
from budge.charges.ledger import make_token
from budge.charges.money import split_evenly
from budge.db.models import Bill, ChargeRequest, RequestEvent, User


def _unusable_password() -> str:
    """A hash of something nobody knows, including us.

    Demo rows can end up in the same database as real ones, where /auth/login
    still serves them. A password they can be signed in with would be a way
    into those accounts that outlives this endpoint being switched off, so
    there isn't one: the only door is /demo/session, and that is shut in
    production.
    """
    return password_hash.hash(secrets.token_urlsafe(32))


class Persona(BaseModel):
    email: str
    name: str
    blurb: str


ROSTER = [
    Persona(
        email="ara@example.com",
        name="Ara Whitcombe",
        blurb="Pays the power bill and chases everyone for it",
    ),
    Persona(
        email="neve@example.com",
        name="Neve Callaghan",
        blurb="Owes Ara for power, owes Tipene for the car WOF",
    ),
    Persona(
        email="tipene@example.com",
        name="Tipene Rawhiti",
        blurb="Fronted the car costs, split the groceries",
    ),
    Persona(
        email="marguerite@example.com",
        name="Marguerite Sol",
        blurb="Just moved in, has one request waiting",
    ),
    Persona(
        email="dev@example.com",
        name="Dev Ramachandran",
        blurb="Pays on time, which makes him unusual",
    ),
]

BY_EMAIL = {p.email: p for p in ROSTER}

# title, who asked, who owes, total in cents, and how far each has got.
# "" leaves a request open, which is the state most of them should be in.
SCRIPT = [
    (
        "Power, August",
        "ara@example.com",
        18_640,
        [
            ("neve@example.com", "marked_paid"),
            ("tipene@example.com", ""),
            ("marguerite@example.com", ""),
            ("dev@example.com", "confirmed"),
        ],
    ),
    (
        "Internet, August",
        "ara@example.com",
        8_999,
        [
            ("neve@example.com", "confirmed"),
            ("tipene@example.com", "confirmed"),
            ("dev@example.com", "confirmed"),
        ],
    ),
    (
        "Car WOF and service",
        "tipene@example.com",
        34_500,
        [
            ("neve@example.com", ""),
            ("ara@example.com", "declined"),
        ],
    ),
    (
        "Groceries, Sunday",
        "tipene@example.com",
        12_730,
        [
            ("ara@example.com", "marked_paid"),
            ("neve@example.com", ""),
        ],
    ),
    (
        "Flat dinner at the Thai place",
        "dev@example.com",
        9_600,
        [
            ("ara@example.com", ""),
            ("neve@example.com", ""),
            ("tipene@example.com", ""),
            ("marguerite@example.com", ""),
        ],
    ),
]

# Getting to a state takes the events that would really have produced it.
PATHS = {
    "marked_paid": [("marked_paid", "payee")],
    "confirmed": [("marked_paid", "payee"), ("confirmed", "creator")],
    "declined": [("declined", "payee")],
}


def enabled() -> bool:
    """Anywhere but production. Vercel sets VERCEL_ENV on every deployment."""
    return os.environ.get("VERCEL_ENV") != "production"


def is_persona(email: str) -> bool:
    """Whether this account is one of ours, which decides what it can see."""
    return email.lower() in BY_EMAIL


async def seed(session: AsyncSession) -> dict[str, User]:
    """Creates the roster and its bills once, then leaves them alone."""
    existing = {
        user.email: user
        for user in await session.exec(
            select(User).where(col(User.email).in_(list(BY_EMAIL)))
        )
    }
    for persona in ROSTER:
        if persona.email not in existing:
            user = User(
                email=persona.email,
                name=persona.name,
                password_hash=_unusable_password(),
            )
            session.add(user)
            existing[persona.email] = user
    await session.commit()
    for user in existing.values():
        await session.refresh(user)

    # One bill standing in for the lot: if it survived a previous sign-in, so
    # did the rest, and seeding again would just duplicate them.
    creator_ids = [u.id or 0 for u in existing.values()]
    already = (
        await session.exec(
            select(Bill).where(col(Bill.creator_id).in_(creator_ids)).limit(1)
        )
    ).first()
    if already is not None:
        return existing

    for title, creator_email, total, payees in SCRIPT:
        bill = Bill(
            creator_id=existing[creator_email].id or 0, title=title, total_cents=total
        )
        session.add(bill)
        await session.commit()
        await session.refresh(bill)

        # The creator's own share comes off the top, same as a real split.
        shares = split_evenly(total, len(payees) + 1)[1:]
        for (payee_email, outcome), share in zip(payees, shares, strict=True):
            request = ChargeRequest(
                bill_id=bill.id or 0,
                token=make_token(),
                payee_email=payee_email,
                payee_name=BY_EMAIL[payee_email].name,
                amount_cents=share,
            )
            session.add(request)
            await session.commit()
            await session.refresh(request)
            for type, actor in PATHS.get(outcome, []):
                session.add(
                    RequestEvent(request_id=request.id or 0, type=type, actor=actor)
                )
        await session.commit()

    return existing
