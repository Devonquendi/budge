"""ASGI entrypoint for the FastAPI app."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from thrifty.routes import router

load_dotenv()

# Inside the package, so it resolves the same from source or site-packages.
WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="Thrifty")
app.include_router(router, prefix="/api")
app.frontend("/", directory=WEB_DIR)
