"""Onboarding: connect Akahu, then choose which accounts the dashboard uses."""

from html import escape

import httpx2
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from thrifty import credentials
from thrifty.akahu import AkahuClient
from thrifty.akahu.models import Account
from thrifty.auth import ONBOARDING_PATH, CurrentUserId, SessionDep
from thrifty.pages import form_page

ACCOUNTS_PATH = f"{ONBOARDING_PATH}/accounts"
router = APIRouter(tags=["onboarding"])

TOKENS_INTRO = """
    <p>
      Thrifty reads your bank data through
      <a href="https://my.akahu.nz" target="_blank" rel="noopener">Akahu</a>.
      Create a personal app there, connect your banks, then paste its two tokens
      below.
    </p>
"""

TOKENS_FIELDS = """
      <label>
        App ID token
        <input type="text" name="app_token" placeholder="app_token_..." autofocus required />
      </label>
      <label>
        User token
        <input type="password" name="user_token" placeholder="user_token_..." required />
      </label>
"""

ACCOUNTS_INTRO = """
    <p>Tick the accounts you spend from. Those are the ones the dashboard adds up.</p>
"""


def _tokens_page(error: str = "") -> str:
    return form_page(
        title="connect Akahu",
        intro=TOKENS_INTRO,
        fields=TOKENS_FIELDS,
        submit="Connect",
        error=error,
        width="30rem",
    )


def _accounts_page(accounts: list[Account], included: set[str]) -> str:
    fields = "\n".join(
        f'      <label><input type="checkbox" name="account_id"'
        f' value="{escape(account.id)}"{" checked" if account.id in included else ""} />'
        f" {escape(account.name)}"
        f" &mdash; {account.currency} {account.balance_current:,.2f}</label>"
        for account in accounts
    )
    return form_page(
        title="choose accounts",
        intro=ACCOUNTS_INTRO,
        fields=fields,
        submit="Save",
        width="34rem",
    )


@router.get(ONBOARDING_PATH)
async def tokens_form() -> HTMLResponse:
    return HTMLResponse(_tokens_page())


@router.post(ONBOARDING_PATH)
async def connect(
    request: Request, user_id: CurrentUserId, session: SessionDep
) -> Response:
    """Verifies the tokens against Akahu before storing them encrypted."""
    form = await request.form()
    app_token = str(form.get("app_token", "")).strip()
    user_token = str(form.get("user_token", "")).strip()

    try:
        await AkahuClient(app_token=app_token, user_token=user_token).get_accounts()
    except httpx2.HTTPError:
        return HTMLResponse(
            _tokens_page("Akahu rejected those tokens. Check both and try again."),
            status_code=400,
        )

    await credentials.save(session, user_id, app_token, user_token)
    return RedirectResponse(ACCOUNTS_PATH, status_code=303)


@router.get(ACCOUNTS_PATH)
async def accounts_form(user_id: CurrentUserId, session: SessionDep) -> Response:
    client = await credentials.client_for(session, user_id)
    if client is None:
        return RedirectResponse(ONBOARDING_PATH)

    accounts = await client.get_accounts()
    included = await credentials.included_account_ids(session, user_id)
    # No selection saved yet, so start with everything ticked.
    return HTMLResponse(
        _accounts_page(
            accounts, {a.id for a in accounts} if included is None else included
        )
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
