"""
JWT authentication against Supabase Auth.

Every protected route must take `user = Depends(get_current_user)` (or
`rate_limit(...)`, which includes it). Never trust a client-supplied user_id.
"""

import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database import supabase

logger = logging.getLogger("campushire.auth")

_bearer = HTTPBearer(auto_error=True)
_rate_hits: Dict[str, List[float]] = defaultdict(list)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Any:
    """Verify the bearer token with Supabase and return the Auth user object."""
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )

    try:
        result = supabase.auth.get_user(credentials.credentials)
        user = getattr(result, "user", None)
        if user is None or not getattr(user, "id", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session.",
            )
        return user
    except HTTPException:
        raise
    except Exception:
        logger.info("JWT verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )


def rate_limit(max_per_minute: int = 30) -> Callable:
    """Per-user sliding window for expensive (LLM / upload) routes."""

    def _dep(
        request: Request,
        user: Any = Depends(get_current_user),
    ) -> Any:
        key = getattr(user, "id", None) or (
            request.client.host if request.client else "anonymous"
        )
        now = time.time()
        window = [t for t in _rate_hits[key] if now - t < 60]
        if len(window) >= max_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a moment and try again.",
            )
        window.append(now)
        _rate_hits[key] = window
        return user

    return _dep
