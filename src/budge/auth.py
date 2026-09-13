"""Session handling and the dependencies that identify the current user."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.db.models import User
from budge.db.session import get_session

LOGIN_PATH = "/login"
SIGNUP_PATH = "/signup"
ONBOARDING_PATH = "/onboarding"
STATIC_PREFIX = "/static"
PUBLIC_PATHS = (LOGIN_PATH, SIGNUP_PATH)

password_hash = PasswordHash.recommended()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _is_public(path: str) -> bool:
    # Signed-out pages still need the stylesheet and theme script.
    return path in PUBLIC_PATHS or path.startswith(STATIC_PREFIX)


async def require_auth(request: Request, call_next) -> Response:
    """Sends unauthenticated requests to the login page instead of onward."""
    if _is_public(request.url.path) or request.session.get("user_id"):
        return await call_next(request)
    if request.url.path.startswith("/api"):
        return Response(status_code=401)
    return RedirectResponse(LOGIN_PATH)


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
