"""Signing in as one of the invented people, where BUDGE_DEMO=1."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from budge import demo
from budge.auth import SessionDep

router = APIRouter(prefix="/demo", tags=["demo"])

NOT_FOUND = 404


class SignIn(BaseModel):
    email: str


class Me(BaseModel):
    email: str
    name: str | None
    onboarded: bool


@router.get("/personas")
async def get_personas() -> list[demo.Persona]:
    """Who you can sign in as. Empty unless the demo is on."""
    return demo.ROSTER if demo.enabled() else []


@router.post("/session")
async def start_session(body: SignIn, request: Request, session: SessionDep) -> Me:
    """Seeds the roster if it isn't there yet, then signs in as one of them."""
    if not demo.enabled() or not demo.is_persona(body.email):
        raise HTTPException(status_code=NOT_FOUND, detail="Not found")

    users = await demo.seed(session)
    user = users[body.email.lower()]
    request.session["user_id"] = user.id
    # The fixture feed stands in for a bank connection.
    return Me(email=user.email, name=user.name, onboarded=True)
