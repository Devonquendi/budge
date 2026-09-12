"""ASGI entrypoint for the FastAPI app."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from thrifty.api import accounts
from thrifty.auth import require_auth
from thrifty.templating import STATIC_DIR
from thrifty.views import auth, dashboard, onboarding, settings

load_dotenv()

SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

app = FastAPI(title="Thrifty")
app.add_middleware(BaseHTTPMiddleware, dispatch=require_auth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["AUTH_SECRET"],
    max_age=SESSION_MAX_AGE,
    # Vercel sets VERCEL=1 in production, where requests are HTTPS only.
    https_only=bool(os.environ.get("VERCEL")),
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(onboarding.router)
app.include_router(settings.router)
app.include_router(accounts.router, prefix="/api")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
