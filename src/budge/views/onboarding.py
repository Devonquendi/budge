"""First-run setup: connect Akahu, then pick the dashboard accounts."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from budge import credentials
from budge.auth import ONBOARDING_PATH, CurrentUserId, SessionDep
from budge.templating import templates

ACCOUNTS_PATH = f"{ONBOARDING_PATH}/accounts"
router = APIRouter(tags=["onboarding"])

BAD_TOKENS = "Akahu rejected those tokens. Check both and try again."


@router.get(ONBOARDING_PATH)
async def tokens_form(request: Request) -> Response:
    return templates.TemplateResponse(request, "onboarding/tokens.html")


@router.post(ONBOARDING_PATH)
async def connect(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    form = await request.form()
    app_token = str(form.get("app_token", "")).strip()
    user_token = str(form.get("user_token", "")).strip()

    if not await credentials.verify_and_save(session, user_id, app_token, user_token):
        return templates.TemplateResponse(
            request,
            "onboarding/tokens.html",
            {"error": BAD_TOKENS},
            status_code=400,
        )

    return RedirectResponse(ACCOUNTS_PATH, status_code=303)


@router.get(ACCOUNTS_PATH)
async def accounts_form(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    client = await credentials.client_for(session, user_id)
    if client is None:
        return RedirectResponse(ONBOARDING_PATH)

    accounts = await client.get_accounts()
    included = await credentials.included_account_ids(session, user_id)
    return templates.TemplateResponse(
        request,
        "onboarding/accounts.html",
        # No selection saved yet, so start with everything ticked.
        {
            "accounts": accounts,
            "included": {a.id for a in accounts} if included is None else included,
        },
    )


@router.post(ACCOUNTS_PATH)
async def choose_accounts(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    client = await credentials.client_for(session, user_id)
    if client is None:
        return RedirectResponse(ONBOARDING_PATH, status_code=303)

    form = await request.form()
    chosen = {str(value) for value in form.getlist("account_id")}
    all_ids = [account.id for account in await client.get_accounts()]
    await credentials.set_included_account_ids(session, user_id, all_ids, chosen)
    return RedirectResponse("/", status_code=303)
