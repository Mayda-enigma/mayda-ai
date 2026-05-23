from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.core.config import settings
from src.middleware.request_id import RequestIdMiddleware
from src.middleware.service_auth import require_service_token


class TestServiceAuth:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        with patch.object(settings, "SERVICE_TOKEN", "secret"):
            result = await require_service_token(x_service_token="secret")
            assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        with patch.object(settings, "SERVICE_TOKEN", "secret"):
            with pytest.raises(HTTPException) as exc:
                await require_service_token(x_service_token="wrong")
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token(self):
        with patch.object(settings, "SERVICE_TOKEN", "secret"):
            with pytest.raises(HTTPException) as exc:
                await require_service_token(x_service_token=None)
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_token_configured_skips_auth(self):
        with patch.object(settings, "SERVICE_TOKEN", ""):
            result = await require_service_token(x_service_token=None)
            assert result is None

    @pytest.mark.asyncio
    async def test_no_token_configured_any_value_passes(self):
        with patch.object(settings, "SERVICE_TOKEN", ""):
            result = await require_service_token(x_service_token="anything")
            assert result is None


class TestRequestIdMiddleware:
    def test_middleware_class_exists(self):
        assert hasattr(RequestIdMiddleware, "dispatch")
        assert callable(RequestIdMiddleware.dispatch)
