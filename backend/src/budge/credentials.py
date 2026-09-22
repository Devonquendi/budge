"""A user's stored Akahu tokens and their dashboard account selection."""

import httpx2
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge import demo
from budge.akahu import AkahuClient
from budge.akahu.models import Account
from budge.db import crypto
from budge.db.models import AkahuAccountSetting, AkahuCredential, User


async def _row(session: AsyncSession, user_id: int) -> AkahuCredential | None:
    statement = select(AkahuCredential).where(AkahuCredential.user_id == user_id)
    return (await session.exec(statement)).first()


async def get(session: AsyncSession, user_id: int) -> AkahuCredential | None:
    """The user's stored tokens. None on a demo deployment, whether or not a
    row exists: invented people and live tokens don't share a database."""
    if demo.enabled():
        return None
    return await _row(session, user_id)


async def has_bank(session: AsyncSession, user_id: int) -> bool:
    """Whether this user has anything to read transactions from.

    Not the same question as "are there Akahu tokens": a demo persona has a
    fixture feed and no tokens, and the app should treat them as set up.
    """
    user = await session.get(User, user_id)
    if user is not None and demo.client_for(user.email) is not None:
        return True
    return await get(session, user_id) is not None


async def save(
    session: AsyncSession, user_id: int, app_token: str, user_token: str
) -> None:
    """Stores the tokens encrypted, replacing any the user already had."""
    if demo.enabled():
        raise PermissionError("Akahu is disabled on a demo deployment")
    app_encrypted = crypto.encrypt(app_token)
    user_encrypted = crypto.encrypt(user_token)

    credential = await _row(session, user_id)
    if credential is None:
        credential = AkahuCredential(
            user_id=user_id,
            app_token_encrypted=app_encrypted,
            user_token_encrypted=user_encrypted,
        )
    else:
        credential.app_token_encrypted = app_encrypted
        credential.user_token_encrypted = user_encrypted

    session.add(credential)
    await session.commit()


async def verify_and_save(
    session: AsyncSession, user_id: int, app_token: str, user_token: str
) -> bool:
    """Saves the tokens only if Akahu accepts them. False means it didn't."""
    try:
        await AkahuClient(app_token=app_token, user_token=user_token).get_accounts()
    except httpx2.HTTPError:
        return False

    await save(session, user_id, app_token, user_token)
    return True


async def forget(session: AsyncSession, user_id: int) -> None:
    """Drops the tokens and the account picks, putting the user back before setup.

    The picks go too: they are Akahu account ids, and a later reconnection,
    even to the same banks, is a new set of ids that these rows would silently
    exclude from the dashboard.
    """
    credential = await _row(session, user_id)
    if credential is not None:
        await session.delete(credential)
    for setting in await _settings(session, user_id):
        await session.delete(setting)
    await session.commit()


async def client_for(
    session: AsyncSession, user_id: int
) -> AkahuClient | demo.FixtureClient | None:
    """A bank for this user, or None if they haven't connected one.

    A demo persona gets the fixture feed. See demo.FixtureClient.
    """
    user = await session.get(User, user_id)
    if user is not None:
        stand_in = demo.client_for(user.email)
        if stand_in is not None:
            return stand_in

    credential = await get(session, user_id)
    if credential is None:
        return None
    return AkahuClient(
        app_token=crypto.decrypt(credential.app_token_encrypted),
        user_token=crypto.decrypt(credential.user_token_encrypted),
    )


async def _settings(session: AsyncSession, user_id: int) -> list[AkahuAccountSetting]:
    statement = select(AkahuAccountSetting).where(
        AkahuAccountSetting.user_id == user_id
    )
    return list((await session.exec(statement)).all())


async def included_account_ids(session: AsyncSession, user_id: int) -> set[str] | None:
    """Accounts the user picked for the dashboard, or None if they never picked."""
    settings = await _settings(session, user_id)
    if not settings:
        return None
    return {s.akahu_account_id for s in settings if s.included_in_dashboard}


async def set_included_account_ids(
    session: AsyncSession, user_id: int, all_ids: list[str], included: set[str]
) -> None:
    existing = {s.akahu_account_id: s for s in await _settings(session, user_id)}
    for account_id in all_ids:
        setting = existing.get(account_id) or AkahuAccountSetting(
            user_id=user_id, akahu_account_id=account_id
        )
        setting.included_in_dashboard = account_id in included
        session.add(setting)
    await session.commit()


async def name_accounts(
    session: AsyncSession, user_id: int, accounts: list[Account]
) -> list[Account]:
    """Stamp each account with the name the user gave it, if they gave it one.

    Everything downstream reads `display_name`, so this has to run before the
    accounts are handed out or transactions are built from them.
    """
    nicknames = {
        s.akahu_account_id: s.nickname
        for s in await _settings(session, user_id)
        if s.nickname
    }
    for account in accounts:
        account.nickname = nicknames.get(account.id)
    return accounts


async def set_nickname(
    session: AsyncSession,
    user_id: int,
    all_ids: list[str],
    account_id: str,
    nickname: str | None,
) -> None:
    """Renames one account. None puts Akahu's own name back.

    Every account id comes in because an empty table is what means "the
    dashboard shows all of them". Writing one row would quietly reduce that to
    "the dashboard shows the account you just renamed", so it gets filled in
    first.
    """
    settings = {s.akahu_account_id: s for s in await _settings(session, user_id)}
    if not settings:
        settings = {
            other: AkahuAccountSetting(user_id=user_id, akahu_account_id=other)
            for other in all_ids
        }

    setting = settings.get(account_id) or AkahuAccountSetting(
        user_id=user_id,
        akahu_account_id=account_id,
        # Missing from a table that has rows means excluded, and renaming an
        # account is not how it should arrive on the dashboard.
        included_in_dashboard=False,
    )
    setting.nickname = nickname
    settings[account_id] = setting

    session.add_all(settings.values())
    await session.commit()
