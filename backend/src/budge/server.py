"""ASGI entrypoint for the FastAPI app."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from budge.api import accounts, akahu, auth

load_dotenv()

SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

app = FastAPI(title="Budge")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["AUTH_SECRET"],
    max_age=SESSION_MAX_AGE,
    # Vercel sets VERCEL=1 in production, where requests are HTTPS only.
    https_only=bool(os.environ.get("VERCEL")),
)

for router in (auth.router, akahu.router, accounts.router):
    app.include_router(router, prefix="/api")
