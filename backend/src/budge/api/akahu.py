"""The user's Akahu connection: the two tokens budge reads their banks with."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from budge import credentials, demo
from budge.auth import CurrentUserId, SessionDep

router = APIRouter(prefix="/akahu", tags=["akahu"])

BAD_TOKENS = "Akahu rejected those tokens. Check both and try again."
NO_AKAHU_HERE = "This deployment runs the demo, so it can't hold bank credentials."


class Tokens(BaseModel):
    app_token: str
    user_token: str


class Connection(BaseModel):
    connected: bool


@router.get("")
async def get_connection(user_id: CurrentUserId, session: SessionDep) -> Connection:
    """Whether tokens are stored. The tokens themselves are never sent back."""
    credential = await credentials.get(session, user_id)
    return Connection(connected=credential is not None)


@router.put("")
async def connect(
    body: Tokens, user_id: CurrentUserId, session: SessionDep
) -> Connection:
    """Stores tokens, replacing any already held, but only if Akahu accepts them."""
    # Also refused in credentials.save, but that would reach the browser as a 500.
    if demo.enabled():
        raise HTTPException(status_code=403, detail=NO_AKAHU_HERE)
    saved = await credentials.verify_and_save(
        session, user_id, body.app_token.strip(), body.user_token.strip()
    )
    if not saved:
        raise HTTPException(status_code=400, detail=BAD_TOKENS)
    return Connection(connected=True)


@router.delete("", status_code=204)
async def disconnect(user_id: CurrentUserId, session: SessionDep) -> Response:
    """Forgets the tokens, sending the user back to onboarding on the next load."""
    await credentials.forget(session, user_id)
    return Response(status_code=204)
