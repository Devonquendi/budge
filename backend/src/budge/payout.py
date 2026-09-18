"""Where money should actually go, and whether that is still true.

A request without a payout account can only be claimed paid, never paid: the
payer has nowhere to send it. This is the half that turns "I've paid this" from
an assertion into something somebody could act on.
"""

from datetime import UTC, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from budge import credentials
from budge.charges.money import normalise_account
from budge.db.models import User


async def connected_accounts(session: AsyncSession, user_id: int) -> list[str]:
    """Every account number this user's bank connection actually returns.

    Empty when there is no connection, which is not the same as "the account is
    wrong": see `still_verified`, which treats the two differently.
    """
    client = await credentials.client_for(session, user_id)
    if client is None:
        return []
    numbers = []
    for account in await client.get_accounts():
        number = normalise_account(account.formatted_account)
        if number:
            numbers.append(number)
    return numbers


async def verify(session: AsyncSession, user: User, account: str) -> bool:
    """Checks a payout account against the accounts the bank reports.

    Verification is what stops somebody quietly pointing their requests at an
    account that isn't theirs. It is deliberately not a precondition for saving
    one: plenty of people will want to be paid into an account they have not
    connected, and refusing that outright would be worse than saying so.
    """
    normalised = normalise_account(account)
    if normalised is None:
        return False
    return normalised in await connected_accounts(session, user.id or 0)


async def still_verified(session: AsyncSession, user: User) -> bool:
    """Whether a previously verified account is still among the connected ones.

    True when there is nothing to contradict: no account set, or no connection
    to check against. A bank going quiet is not evidence the account is wrong,
    and flagging it would cry wolf every time a token expired.
    """
    if not user.payout_account or user.payout_verified_at is None:
        return True
    connected = await connected_accounts(session, user.id or 0)
    if not connected:
        return True
    return user.payout_account in connected


async def save(
    session: AsyncSession, user: User, account: str | None, name: str
) -> User:
    """Stores a payout account, verifying it against the bank where it can."""
    if account is None:
        user.payout_account = None
        user.payout_name = None
        user.payout_verified_at = None
    else:
        normalised = normalise_account(account)
        if normalised is None:
            raise ValueError("That isn't a New Zealand account number")
        user.payout_account = normalised
        user.payout_name = name.strip() or None
        verified = await verify(session, user, normalised)
        user.payout_verified_at = datetime.now(UTC) if verified else None

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
