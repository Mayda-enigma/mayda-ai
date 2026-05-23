from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from src.schemas.recommendation_schema import DishInfo, Recommendation, RecommendResponse


class TestHealthEndpoint:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_root(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "Mayda AI"
        assert "capabilities" in data


class TestAuthEndpoints:
    @pytest.mark.parametrize("method,path,body", [
        ("POST", "/api/recommendations", {"user_id": 1}),
        ("POST", "/api/search", {"query": "test"}),
        ("POST", "/api/forecast", {"item": "Chicken", "date": "2026-06-01T00:00:00"}),
        ("GET", "/api/recommendations/restock", None),
        ("GET", "/api/items", None),
        ("GET", "/api/dishes/info", None),
    ])
    async def test_protected_routes_reject_without_token(self, client: AsyncClient, method: str, path: str, body):
        resp = await client.get(path) if method == "GET" else await client.post(path, json=body)
        assert resp.status_code == 401

    async def test_valid_token_accepted(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/items", headers=auth_headers)
        assert resp.status_code == 200


class TestVoiceEndpoints:
    """These work without mocks — pure business logic."""

    async def test_parse_chef_lance(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/parse/chef", json={"text": "commande 12 lance"}, headers=auth_headers)
        assert resp.status_code == 200
        d = resp.json()
        assert d["type"] == "lance"
        assert d["order_number"] == "12"
        assert d["confidence"] >= 65

    async def test_parse_chef_prete(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/parse/chef", json={"text": "commande 5 prête"}, headers=auth_headers)
        assert resp.status_code == 200
        d = resp.json()
        assert d["type"] == "prete"
        assert d["order_number"] == "5"

    async def test_parse_chef_garbage(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/parse/chef", json={"text": "bonjour"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["type"] is None

    async def test_parse_order(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/parse/order", json={
            "text": "two burgers and a coke",
            "menu_items": [{"id": 1, "name": "Burger"}, {"id": 2, "name": "Coca-Cola"}],
        }, headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1

    async def test_parse_order_empty(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/parse/order", json={
            "text": "",
            "menu_items": [],
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestInventoryEndpoint:
    async def test_items_list(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/items", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_forecast_with_mock(self, client: AsyncClient, app, auth_headers):
        from src.api.deps import get_forecaster

        fc_mock = MagicMock()
        fc_mock.predict_consumption.return_value = None
        app.dependency_overrides[get_forecaster] = lambda: fc_mock

        resp = await client.post("/api/forecast", json={
            "item": "UnknownItem", "date": "2026-06-01T00:00:00",
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestRecommendationEndpoint:
    async def test_recommendation_with_mock(self, client: AsyncClient, app, auth_headers):
        from src.api.deps import get_recommendation_service

        rec_mock = AsyncMock(spec=["recommend"])
        rec_mock.recommend = AsyncMock(return_value=RecommendResponse(
            user_id=1,
            recommendations=[
                Recommendation(
                    dish=DishInfo(id=1, name="Pizza", price=10.0),
                    confidence_score=0.9, explanation="Good", source="llm",
                )
            ],
            model="gemini", processing_time=0.5, total_available_dishes=10,
        ))
        app.dependency_overrides[get_recommendation_service] = lambda: rec_mock

        resp = await client.post("/api/recommendations", json={"user_id": 1}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == 1
        assert data["recommendations"][0]["dish"]["name"] == "Pizza"
