"""Session handling and the dependencies that identify the current user."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.db.models import User
from budge.db.session import get_session

password_hash = PasswordHash.recommended()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def user_id(user: User) -> int:
    """Narrows the optional primary key — a row in the DB always has one."""
    if user.id is None:
        raise HTTPException(status_code=401)
    return user.id


async def get_current_user(request: Request, session: SessionDep) -> User:
    """The logged-in user, or 401 if the session doesn't map to one.

    Routes opt into auth by depending on this (or CurrentUserId). There is no
    blanket middleware: a route without the dependency is public on purpose.
    """
    user = await session.get(User, request.session.get("user_id"))
    if user is None:
        raise HTTPException(status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_id(user: CurrentUser) -> int:
    return user_id(user)


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
