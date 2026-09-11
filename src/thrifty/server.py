"""ASGI entrypoint for the FastAPI app."""

from dotenv import load_dotenv
from fastapi import FastAPI

from thrifty.routes import router

# No-op in production, where real env vars are injected directly and no
# .env file exists.
load_dotenv()

app = FastAPI(title="Thrifty")
app.include_router(router, prefix="/api")
