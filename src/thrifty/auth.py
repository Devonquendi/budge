"""Per-user accounts: invite-gated signup, login, and session handling."""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pwdlib import PasswordHash
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from thrifty.db.models import User
from thrifty.db.session import get_session

LOGIN_PATH = "/login"
SIGNUP_PATH = "/signup"
router = APIRouter()
password_hash = PasswordHash.recommended()

SessionDep = Annotated[AsyncSession, Depends(get_session)]

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Thrifty &mdash; {title}</title>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
  />
</head>
<body>
  <main class="container" style="max-width: 24rem">
    <h1>Thrifty</h1>
    <form method="post">
      {fields}
      {error}
      <button type="submit">{submit}</button>
    </form>
  </main>
</body>
</html>
"""

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


def _error(message: str) -> str:
    return f'<p style="color: var(--pico-del-color)">{message}</p>' if message else ""


async def require_auth(request: Request, call_next) -> Response:
    """Sends unauthenticated requests to the login page instead of onward."""
    if request.url.path in (LOGIN_PATH, SIGNUP_PATH) or request.session.get("user_id"):
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


@router.get(LOGIN_PATH)
async def login_form() -> HTMLResponse:
    return HTMLResponse(
        PAGE.format(title="log in", fields=LOGIN_FIELDS, error="", submit="Log in")
    )


@router.post(LOGIN_PATH)
async def login(request: Request, session: SessionDep) -> Response:
    """Checks email/password and starts a session, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))

    user = (await session.exec(select(User).where(User.email == email))).first()
    if user is None or not password_hash.verify(password, user.password_hash):
        page = PAGE.format(
            title="log in",
            fields=LOGIN_FIELDS,
            error=_error("Wrong email or password"),
            submit="Log in",
        )
        return HTMLResponse(page, status_code=401)

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get(SIGNUP_PATH)
async def signup_form() -> HTMLResponse:
    return HTMLResponse(
        PAGE.format(title="sign up", fields=SIGNUP_FIELDS, error="", submit="Sign up")
    )


@router.post(SIGNUP_PATH)
async def signup(request: Request, session: SessionDep) -> Response:
    """Creates an account behind an invite code, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))
    invite_code = str(form.get("invite_code", ""))

    def fail(message: str) -> HTMLResponse:
        page = PAGE.format(
            title="sign up",
            fields=SIGNUP_FIELDS,
            error=_error(message),
            submit="Sign up",
        )
        return HTMLResponse(page, status_code=400)

    if invite_code != os.environ["SIGNUP_INVITE_CODE"]:
        return fail("Invalid invite code")

    existing = (await session.exec(select(User).where(User.email == email))).first()
    if existing is not None:
        return fail("An account with that email already exists")

    user = User(email=email, password_hash=password_hash.hash(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()
    return RedirectResponse(LOGIN_PATH, status_code=303)
