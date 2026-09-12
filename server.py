"""Vercel's entrypoint.

The Python runtime resolves `tool.vercel.entrypoint` as a path from the repo
root, which can't reach into the src layout — so the real app is re-exported
from here. Everything else (`uv run fastapi dev`) still points at
`thrifty.server:app` directly.
"""

from thrifty.server import app

__all__ = ["app"]
