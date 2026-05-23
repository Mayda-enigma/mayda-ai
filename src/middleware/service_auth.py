"""
X-Service-Token validation middleware (AI-002 pattern).
Rejects any request without a valid service token on protected routes.
"""

from fastapi import Header, HTTPException

from src.core.config import settings


async def require_service_token(
    x_service_token: str | None = Header(None),
) -> None:
    """FastAPI dependency — raises 401 if token is missing or wrong."""
    if not settings.SERVICE_TOKEN:
        # No token configured → skip auth (dev mode)
        return
    if x_service_token != settings.SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing service token")
