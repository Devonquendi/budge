"""Per-user accounts: invite-gated signup, login, and session handling."""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pwdlib import PasswordHash
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from thrifty.db.models import AkahuCredential, User
from thrifty.db.session import get_session
from thrifty.pages import form_page

LOGIN_PATH = "/login"
SIGNUP_PATH = "/signup"
ONBOARDING_PATH = "/onboarding"
PUBLIC_PATHS = (LOGIN_PATH, SIGNUP_PATH)

router = APIRouter()
password_hash = PasswordHash.recommended()

SessionDep = Annotated[AsyncSession, Depends(get_session)]

LOGIN_FIELDS = """
      <label>
        Email
        <input type="email" name="email" autofocus required />
      </label>
      <label>
        Password
        <input type="password" name="password" required />
      </label>
"""

SIGNUP_FIELDS = (
    LOGIN_FIELDS
    + """
      <label>
        Invite code
        <input type="text" name="invite_code" required />
      </label>
"""
)

LOGIN_FOOTER = f'<p>No account? <a href="{SIGNUP_PATH}">Sign up</a></p>'
SIGNUP_FOOTER = f'<p>Already have an account? <a href="{LOGIN_PATH}">Log in</a></p>'


def _login_page(error: str = "") -> str:
    return form_page(
        title="log in",
        fields=LOGIN_FIELDS,
        submit="Log in",
        error=error,
        footer=LOGIN_FOOTER,
    )


def _signup_page(error: str = "") -> str:
    return form_page(
        title="sign up",
        fields=SIGNUP_FIELDS,
        submit="Sign up",
        error=error,
        footer=SIGNUP_FOOTER,
    )


async def require_auth(request: Request, call_next) -> Response:
    """Sends unauthenticated requests to the login page instead of onward."""
    if request.url.path in PUBLIC_PATHS or request.session.get("user_id"):
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


async def _landing_path(session: AsyncSession, user: User) -> str:
    """Users without Akahu tokens yet need onboarding before the dashboard."""
    statement = select(AkahuCredential).where(AkahuCredential.user_id == user.id)
    onboarded = (await session.exec(statement)).first() is not None
    return "/" if onboarded else ONBOARDING_PATH


@router.get(LOGIN_PATH)
async def login_form() -> HTMLResponse:
    return HTMLResponse(_login_page())


@router.post(LOGIN_PATH)
async def login(request: Request, session: SessionDep) -> Response:
    """Checks email/password and starts a session, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))

    user = (await session.exec(select(User).where(User.email == email))).first()
    if user is None or not password_hash.verify(password, user.password_hash):
        return HTMLResponse(_login_page("Wrong email or password"), status_code=401)

    request.session["user_id"] = user.id
    return RedirectResponse(await _landing_path(session, user), status_code=303)


@router.get(SIGNUP_PATH)
async def signup_form() -> HTMLResponse:
    return HTMLResponse(_signup_page())


@router.post(SIGNUP_PATH)
async def signup(request: Request, session: SessionDep) -> Response:
    """Creates an account behind an invite code, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))
    invite_code = str(form.get("invite_code", ""))

    if invite_code != os.environ["SIGNUP_INVITE_CODE"]:
        return HTMLResponse(_signup_page("Invalid invite code"), status_code=400)

    existing = (await session.exec(select(User).where(User.email == email))).first()
    if existing is not None:
        message = "An account with that email already exists"
        return HTMLResponse(_signup_page(message), status_code=400)

    user = User(email=email, password_hash=password_hash.hash(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(ONBOARDING_PATH, status_code=303)


@router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()
    return RedirectResponse(LOGIN_PATH, status_code=303)
