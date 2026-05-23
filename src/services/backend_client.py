"""
HTTP client for communicating with the main mayda-backend API.
Uses httpx (replaces aiohttp per RC-006).
Forwards X-Service-Token and X-Request-Id on every outbound call.
"""

import logging
from typing import Any

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Async HTTP client targeting the mayda-backend REST API."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.base_url = settings.BACKEND_API_URL.rstrip("/")

    # ── internal helpers ──

    def _headers(self, request_id: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.SERVICE_TOKEN:
            headers["X-Service-Token"] = settings.SERVICE_TOKEN
        if request_id:
            headers["X-Request-Id"] = request_id
        return headers

    async def _get(
        self,
        path: str,
        params: dict | None = None,
        request_id: str | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp = await self.client.get(
                url,
                params=params,
                headers=self._headers(request_id),
                timeout=settings.BACKEND_API_TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning("Backend %s returned %s: %s", url, resp.status_code, resp.text[:200])
            return {}
        except httpx.RequestError as exc:
            logger.error("Backend request failed (%s): %s", url, exc)
            return {}

    # ── public API ──

    async def get_user_profile(self, user_id: int, request_id: str | None = None) -> dict:
        """GET /users/{id}/profile — returns user + preferences + order history + reviews."""
        return await self._get(f"/users/{user_id}/profile", request_id=request_id)

    async def get_user_order_history(self, user_id: int, limit: int = 20, request_id: str | None = None) -> list:
        profile = await self.get_user_profile(user_id, request_id=request_id)
        orders = profile.get("orderHistory", [])
        return orders[-limit:] if orders else []

    async def get_dishes(
        self,
        restaurant_id: int | None = None,
        available_only: bool = True,
        request_id: str | None = None,
    ) -> list:
        """GET /dishes — all dishes, optionally filtered."""
        params: dict[str, str] = {}
        if restaurant_id:
            params["restaurant_id"] = str(restaurant_id)
        if available_only:
            params["available_only"] = "true"
        result = await self._get("/dishes", params=params, request_id=request_id)
        return result if isinstance(result, list) else []

    async def get_restaurant_dishes(self, restaurant_id: int, request_id: str | None = None) -> list:
        """GET /restaurants/{id}/dishes"""
        result = await self._get(f"/restaurants/{restaurant_id}/dishes", request_id=request_id)
        return result if isinstance(result, list) else []

    async def get_user_reviews(self, user_id: int, request_id: str | None = None) -> list:
        profile = await self.get_user_profile(user_id, request_id=request_id)
        return profile.get("reviews", [])
