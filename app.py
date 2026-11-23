"""Vercel FastAPI entrypoint; local development continues to use knowdoc.api."""
from knowdoc.api import app

__all__ = ["app"]
