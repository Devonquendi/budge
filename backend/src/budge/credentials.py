"""A user's stored Akahu tokens and their dashboard account selection."""

import httpx2
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.akahu import AkahuClient
from budge.db import crypto
from budge.db.models import AkahuAccountSetting, AkahuCredential


async def get(session: AsyncSession, user_id: int) -> AkahuCredential | None:
    statement = select(AkahuCredential).where(AkahuCredential.user_id == user_id)
    return (await session.exec(statement)).first()


async def save(
    session: AsyncSession, user_id: int, app_token: str, user_token: str
) -> None:
    """Stores the tokens encrypted, replacing any the user already had."""
    app_encrypted = crypto.encrypt(app_token)
    user_encrypted = crypto.encrypt(user_token)

    credential = await get(session, user_id)
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

    The picks go too: they are Akahu account ids, and a later reconnection —
    even to the same banks — is a new set of ids that these rows would silently
    exclude from the dashboard.
    """
    credential = await get(session, user_id)
    if credential is not None:
        await session.delete(credential)
    for setting in await _settings(session, user_id):
        await session.delete(setting)
    await session.commit()


async def client_for(session: AsyncSession, user_id: int) -> AkahuClient | None:
    """An Akahu client using the user's tokens, or None if they haven't onboarded."""
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
