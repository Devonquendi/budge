"""ASGI entrypoint for the FastAPI app."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from thrifty.auth import require_auth
from thrifty.auth import router as auth_router
from thrifty.onboarding import router as onboarding_router
from thrifty.routes import router as accounts_router

load_dotenv()

# Inside the package, so it resolves the same from source or site-packages.
WEB_DIR = Path(__file__).parent / "web"
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
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(accounts_router, prefix="/api")
app.frontend("/", directory=WEB_DIR)
