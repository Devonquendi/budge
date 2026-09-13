"""Login, signup, and logout pages."""

import os

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.auth import (
    LOGIN_PATH,
    ONBOARDING_PATH,
    SIGNUP_PATH,
    SessionDep,
    password_hash,
)
from budge.db.models import AkahuCredential, User
from budge.templating import templates

router = APIRouter(tags=["auth"])


@router.get(LOGIN_PATH)
async def login_form(request: Request) -> Response:
    return templates.TemplateResponse(request, "login.html")


@router.post(LOGIN_PATH)
async def login(request: Request, session: SessionDep) -> Response:
    """Checks email/password and starts a session, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))

    user = (await session.exec(select(User).where(User.email == email))).first()
    if user is None or not password_hash.verify(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"email": email, "error": "Wrong email or password"},
            status_code=401,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(await _landing_path(session, user), status_code=303)


@router.get(SIGNUP_PATH)
async def signup_form(request: Request, invite: str = "") -> Response:
    """?invite=<code> prefills the invite field so a shared link just works."""
    return templates.TemplateResponse(request, "signup.html", {"invite": invite})


@router.post(SIGNUP_PATH)
async def signup(request: Request, session: SessionDep) -> Response:
    """Creates an account behind an invite code, or re-shows the form."""
    form = await request.form()
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))
    invite_code = str(form.get("invite_code", ""))

    def fail(message: str) -> Response:
        return templates.TemplateResponse(
            request,
            "signup.html",
            {"email": email, "invite": invite_code, "error": message},
            status_code=400,
        )

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
    return RedirectResponse(ONBOARDING_PATH, status_code=303)


@router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()
    return RedirectResponse(LOGIN_PATH, status_code=303)


async def _landing_path(session: AsyncSession, user: User) -> str:
    """Users without Akahu tokens yet need onboarding before the dashboard."""
    statement = select(AkahuCredential).where(AkahuCredential.user_id == user.id)
    onboarded = (await session.exec(statement)).first() is not None
    return "/" if onboarded else ONBOARDING_PATH
