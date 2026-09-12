"""Shared-secret login gating the dashboard and API."""

import os
import secrets

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

LOGIN_PATH = "/login"
router = APIRouter()

LOGIN_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Thrifty &mdash; log in</title>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
  />
</head>
<body>
  <main class="container" style="max-width: 24rem">
    <h1>Thrifty</h1>
    <form method="post">
      <label>
        Password
        <input type="password" name="password" autofocus required />
      </label>
      {error}
      <button type="submit">Log in</button>
    </form>
  </main>
</body>
</html>
"""


async def require_auth(request: Request, call_next) -> Response:
    """Sends unauthenticated requests to the login page instead of onward."""
    if request.url.path == LOGIN_PATH or request.session.get("authed"):
        return await call_next(request)
    if request.url.path.startswith("/api"):
        return Response(status_code=401)
    return RedirectResponse(LOGIN_PATH)


@router.get(LOGIN_PATH)
async def login_form() -> HTMLResponse:
    """Password entry form."""
    return HTMLResponse(LOGIN_PAGE.format(error=""))


@router.post(LOGIN_PATH)
async def login(request: Request) -> Response:
    """Checks the password and starts a session, or re-shows the form."""
    form = await request.form()
    password = form.get("password", "")
    if secrets.compare_digest(str(password), os.environ["AUTH_SECRET"]):
        request.session["authed"] = True
        return RedirectResponse("/", status_code=303)

    error = '<p style="color: var(--pico-del-color)">Wrong password</p>'
    return HTMLResponse(LOGIN_PAGE.format(error=error), status_code=401)
