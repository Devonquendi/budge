"""The dashboard page."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from budge import credentials
from budge.auth import ONBOARDING_PATH, CurrentUserId, SessionDep
from budge.templating import templates

router = APIRouter(tags=["dashboard"])


@router.get("/")
async def dashboard(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    """Balances are fetched client-side from /api/accounts."""
    if await credentials.get(session, user_id) is None:
        return RedirectResponse(ONBOARDING_PATH)
    return templates.TemplateResponse(request, "dashboard.html")
