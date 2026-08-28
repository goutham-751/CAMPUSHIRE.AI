"""Helpers that keep internal exception text off the public API."""

from backend.config import settings


def client_error_detail(exc: Exception, fallback: str = "An unexpected error occurred.") -> str:
    """Return a client-safe error string. Internal details stay in logs unless DEBUG."""
    if settings.DEBUG:
        return str(exc)
    return fallback
