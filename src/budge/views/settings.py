"""Settings: change the Akahu connection and the dashboard account selection."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from budge import credentials
from budge.auth import CurrentUserId, SessionDep
from budge.templating import templates
from budge.views.onboarding import BAD_TOKENS

SETTINGS_PATH = "/settings"
router = APIRouter(prefix=SETTINGS_PATH, tags=["settings"])


async def _page(
    request: Request,
    user_id: CurrentUserId,
    session: SessionDep,
    error: str = "",
    status_code: int = 200,
) -> Response:
    client = await credentials.client_for(session, user_id)
    accounts = await client.get_accounts() if client else []
    included = await credentials.included_account_ids(session, user_id)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "connected": client is not None,
            "accounts": accounts,
            "included": {a.id for a in accounts} if included is None else included,
            "saved": "saved" in request.query_params,
            "error": error,
        },
        status_code=status_code,
    )


@router.get("")
async def settings_page(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    return await _page(request, user_id, session)


@router.post("/accounts")
async def save_accounts(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    client = await credentials.client_for(session, user_id)
    if client is None:
        return RedirectResponse(SETTINGS_PATH, status_code=303)

    form = await request.form()
    chosen = {str(value) for value in form.getlist("account_id")}
    all_ids = [account.id for account in await client.get_accounts()]
    await credentials.set_included_account_ids(session, user_id, all_ids, chosen)
    return RedirectResponse(f"{SETTINGS_PATH}?saved", status_code=303)


@router.post("/akahu")
async def replace_tokens(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    form = await request.form()
    app_token = str(form.get("app_token", "")).strip()
    user_token = str(form.get("user_token", "")).strip()

    if not await credentials.verify_and_save(session, user_id, app_token, user_token):
        return await _page(request, user_id, session, BAD_TOKENS, status_code=400)

    return RedirectResponse(f"{SETTINGS_PATH}?saved", status_code=303)
