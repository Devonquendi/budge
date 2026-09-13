"""Session handling and the dependencies that identify the current user."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.db.models import User
from budge.db.session import get_session

password_hash = PasswordHash.recommended()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def require_auth(request: Request, call_next) -> Response:
    """Rejects unauthenticated requests. Signing in is the browser app's job.

    Sign-in endpoints have to be exempted here once they land, or nobody can
    reach them to get a session in the first place.
    """
    if request.session.get("user_id"):
        return await call_next(request)
    return Response(status_code=401)


async def get_current_user(request: Request, session: SessionDep) -> User:
    """The logged-in user, or 401 if the session doesn't map to one."""
    user = await session.get(User, request.session.get("user_id"))
    if user is None:
        raise HTTPException(status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_id(user: CurrentUser) -> int:
    """Narrows the optional primary key — a row loaded from the DB always has one."""
    if user.id is None:
        raise HTTPException(status_code=401)
    return user.id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
