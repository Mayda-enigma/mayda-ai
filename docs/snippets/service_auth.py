"""
Copy-paste helper: X-Service-Token validation dependency.

See docs/conventions/service-token.md for the rationale.
"""

import os

from fastapi import Header, HTTPException

SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")


async def require_service_token(
    x_service_token: str | None = Header(None),
) -> None:
    """Raise 401 unless the inbound header matches the configured token."""
    if not SERVICE_TOKEN or x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid service token")
