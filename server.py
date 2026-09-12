"""Vercel's entrypoint — re-exported here since it can't resolve into src/."""

from thrifty.server import app

__all__ = ["app"]
