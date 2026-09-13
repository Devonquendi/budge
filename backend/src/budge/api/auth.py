"""Signing in, signing up, and who the caller is."""

import os
import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge import credentials
from budge.auth import CurrentUser, SessionDep, password_hash, user_id
from budge.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

WRONG_CREDENTIALS = "Wrong email or password"


class Login(BaseModel):
    email: EmailStr
    password: str


class SignUp(Login):
    invite_code: str


class Me(BaseModel):
    """Everything the browser app needs to pick a landing page."""

    email: str
    onboarded: bool


async def _me(session: AsyncSession, user: User) -> Me:
    credential = await credentials.get(session, user_id(user))
    return Me(email=user.email, onboarded=credential is not None)


async def _by_email(session: AsyncSession, email: str) -> User | None:
    return (await session.exec(select(User).where(User.email == email))).first()


@router.post("/login")
async def login(body: Login, request: Request, session: SessionDep) -> Me:
    """Starts a session. The cookie is the only thing the caller needs after this."""
    user = await _by_email(session, body.email)
    if user is None or not password_hash.verify(body.password, user.password_hash):
        # One message for both cases, so this can't be used to probe for emails.
        raise HTTPException(status_code=401, detail=WRONG_CREDENTIALS)

    request.session["user_id"] = user.id
    return await _me(session, user)


@router.post("/signup", status_code=201)
async def signup(body: SignUp, request: Request, session: SessionDep) -> Me:
    """Creates an account behind an invite code and signs it straight in."""
    # Constant-time: a plain != leaks the code's length and prefix through
    # how long the comparison takes.
    expected = os.environ["SIGNUP_INVITE_CODE"]
    if not secrets.compare_digest(body.invite_code.encode(), expected.encode()):
        raise HTTPException(status_code=400, detail="Invalid invite code")

    if await _by_email(session, body.email) is not None:
        raise HTTPException(
            status_code=400, detail="An account with that email already exists"
        )

    user = User(email=body.email, password_hash=password_hash.hash(body.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    request.session["user_id"] = user.id
    return await _me(session, user)


@router.post("/logout", status_code=204)
async def logout(request: Request) -> Response:
    """Public on purpose: an expired session should still be able to clear itself."""
    request.session.clear()
    return Response(status_code=204)


@router.get("/me")
async def me(user: CurrentUser, session: SessionDep) -> Me:
    return await _me(session, user)
