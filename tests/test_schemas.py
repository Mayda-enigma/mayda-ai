from datetime import datetime

from src.schemas.inventory_schema import (
    BulkForecastRequest,
    ConsumptionLogInput,
    ConsumptionLogResponse,
    ForecastRequest,
    ForecastResponse,
)
from src.schemas.recommendation_schema import (
    DishInfo,
    Recommendation,
    RecommendRequest,
    RecommendResponse,
)
from src.schemas.search_schema import (
    DishCreate,
    DishResponse,
    DishUpdate,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    TextSearchRequest,
)
from src.schemas.voice_schema import (
    ChefParseRequest,
    ChefParseResponse,
    MenuItem,
    OrderParseItem,
    OrderParseRequest,
    OrderParseResponse,
)


class TestRecommendationSchemas:
    def test_recommend_request_defaults(self):
        req = RecommendRequest(user_id=1)
        assert req.user_id == 1
        assert req.cart_item_ids == []
        assert req.time_of_day is None
        assert req.limit == 5
        assert req.restaurant_id is None

    def test_recommend_request_limit_bounds(self):
        RecommendRequest(user_id=1, limit=1)
        RecommendRequest(user_id=1, limit=20)

    def test_dish_info(self):
        d = DishInfo(id=1, name="Pizza", price=12.5)
        assert d.id == 1
        assert d.name == "Pizza"
        assert d.price == 12.5
        assert d.description == ""
        assert d.is_available is True

    def test_recommendation(self):
        dish = DishInfo(id=1, name="Pasta", price=10.0)
        rec = Recommendation(dish=dish, confidence_score=0.85, explanation="Great match", source="llm")
        assert rec.dish.name == "Pasta"
        assert rec.confidence_score == 0.85
        assert rec.source == "llm"

    def test_recommend_response(self):
        dish = DishInfo(id=1, name="Salad", price=8.0)
        rec = Recommendation(dish=dish, confidence_score=0.9, source="fallback")
        resp = RecommendResponse(user_id=1, recommendations=[rec], model="gemini")
        assert resp.user_id == 1
        assert len(resp.recommendations) == 1
        assert resp.model == "gemini"


class TestSearchSchemas:
    def test_search_request(self):
        req = SearchRequest(query="chicken")
        assert req.query == "chicken"
        assert req.limit == 10
        assert req.restaurant_id is None

    def test_search_result_item(self):
        item = SearchResultItem(dish_id=1, score=0.95, name="Burger", restaurant_name="Bob's")
        assert item.dish_id == 1
        assert item.score == 0.95

    def test_search_response(self):
        resp = SearchResponse(results=[], language_detected="en")
        assert resp.language_detected == "en"
        assert resp.results == []

    def test_dish_create(self):
        dish = DishCreate(
            id=1,
            name="Taco",
            ingredients="meat, cheese",
            price="9.99",
            popularity="80",
            menucategory="Main",
            menu="Lunch",
            restaurant_name="Taqueria",
            restaurant_description="Mexican food",
        )
        assert dish.name == "Taco"
        assert dish.restaurant_id is None

    def test_dish_update_inherits_create(self):
        assert DishUpdate.__bases__[0].__name__ == "DishCreate"

    def test_dish_response(self):
        resp = DishResponse(message="ok", dish_id=1)
        assert resp.message == "ok"
        assert resp.dish_id == 1

    def test_text_search_request(self):
        req = TextSearchRequest(query="pizza")
        assert req.query == "pizza"
        assert req.max_results == 10


class TestInventorySchemas:
    def test_forecast_request(self):
        req = ForecastRequest(item="Chicken", date=datetime(2026, 6, 1))
        assert req.item == "Chicken"
        assert req.weather == "sunny"
        assert req.special_event == 0

    def test_forecast_response(self):
        resp = ForecastResponse(item="Rice", date="2026-06-01", units=25.0, model_version="v1", generated_at="now")
        assert resp.item == "Rice"
        assert resp.units == 25.0

    def test_bulk_forecast(self):
        req = BulkForecastRequest(
            items=[
                ForecastRequest(item="a", date=datetime(2026, 1, 1)),
            ]
        )
        assert len(req.items) == 1

    def test_consumption_log_input(self):
        c = ConsumptionLogInput(food_item="Beef", consumption=10.0)
        assert c.food_item == "Beef"
        assert c.consumption == 10.0
        assert c.notes is None

    def test_consumption_log_response(self):
        r = ConsumptionLogResponse(message="logged")
        assert r.status == "ok"


class TestVoiceSchemas:
    def test_chef_parse_request(self):
        r = ChefParseRequest(text="commande 12 lance")
        assert r.text == "commande 12 lance"

    def test_chef_parse_response(self):
        r = ChefParseResponse(type="lance", order_number="12", confidence=85, matched_phrase="test", message="ok")
        assert r.type == "lance"
        assert r.order_number == "12"

    def test_menu_item(self):
        m = MenuItem(id=1, name="Burger")
        assert m.id == 1

    def test_order_parse_request(self):
        r = OrderParseRequest(text="two burgers", menu_items=[MenuItem(id=1, name="Burger")])
        assert len(r.menu_items) == 1

    def test_order_parse_item(self):
        i = OrderParseItem(menu_item_id=1, confidence=90)
        assert i.menu_item_id == 1
        assert i.quantity == 1

    def test_order_parse_response(self):
        r = OrderParseResponse(items=[OrderParseItem(menu_item_id=1, confidence=90)])
        assert len(r.items) == 1
