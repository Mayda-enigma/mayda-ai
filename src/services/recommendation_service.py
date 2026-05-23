"""
AI-powered recommendation engine.
Ported from recommendation-service/app/services/simple_recommendation_engine.py
with fixes for RC-003 (contract), RC-005 (error handling), RC-006 (httpx).

Supports Gemini (primary) with rule-based fallback when LLM is unavailable.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.schemas.recommendation_schema import (
    DishInfo,
    Recommendation,
    RecommendRequest,
    RecommendResponse,
)
from src.services.backend_client import BackendAPIClient


def _dish_info_from_backend(d: dict[str, Any]) -> DishInfo:
    """Build a DishInfo from a backend-dish dict.

    The shape mismatch between the backend (`isAvailable`, `categoryId`,
    camelCase) and our Pydantic schema (`is_available`, `category_id`,
    snake_case) is handled here once instead of at every callsite.
    """
    return DishInfo(
        id=d["id"],
        name=d["name"],
        description=d.get("description", ""),
        price=d.get("price", 0),
        popularity=d.get("popularity", 0),
        is_available=d.get("isAvailable", True),
        category_id=d.get("categoryId"),
    )


# Conditional LLM imports
try:
    import google.generativeai as genai  # type: ignore[import-untyped]

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)


class RecommendationService:
    """Stateless recommendation engine — receives its dependencies from the outside."""

    def __init__(self, backend: BackendAPIClient):
        self.backend = backend
        self.model = None
        self.provider = "none"
        self._init_llm()

    # ── LLM initialisation ──

    def _init_llm(self) -> None:
        if settings.GEMINI_API_KEY and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    model_name=settings.LLM_MODEL,
                    generation_config=genai.types.GenerationConfig(
                        temperature=settings.LLM_TEMPERATURE,
                        max_output_tokens=settings.LLM_MAX_TOKENS,
                    ),
                )
                self.provider = "gemini"
                logger.info("Initialized Gemini with model: %s", settings.LLM_MODEL)
            except Exception as exc:
                logger.error("Failed to initialise Gemini: %s", exc)
        else:
            logger.warning("No LLM provider available — using fallback recommendations")

    # ── public entry point ──

    async def recommend(
        self,
        req: RecommendRequest,
        request_id: str | None = None,
    ) -> RecommendResponse:
        """Generate recommendations for a user (matches POST /recommendations contract)."""
        start = datetime.now(UTC)

        # 1. Fetch user profile
        user_profile = await self.backend.get_user_profile(req.user_id, request_id=request_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

        # 2. Fetch dishes
        if req.restaurant_id:
            dishes = await self.backend.get_restaurant_dishes(req.restaurant_id, request_id=request_id)
        else:
            dishes = await self.backend.get_dishes(request_id=request_id)

        available = [d for d in dishes if d.get("isAvailable", True)]
        if not available:
            raise HTTPException(status_code=404, detail="No dishes available")

        # 3. Generate recommendations
        if self.provider != "none":
            recs = await self._llm_recommendations(user_profile, available, req)
        else:
            recs = self._fallback_recommendations(user_profile, available, req.limit)

        elapsed = (datetime.now(UTC) - start).total_seconds()

        return RecommendResponse(
            user_id=req.user_id,
            recommendations=recs[: req.limit],
            generated_at=datetime.now(UTC).isoformat(),
            model=self.provider,
            processing_time=round(elapsed, 3),
            total_available_dishes=len(available),
        )

    # ── LLM path ──

    async def _llm_recommendations(
        self,
        profile: dict[str, Any],
        dishes: list[dict[str, Any]],
        req: RecommendRequest,
    ) -> list[Recommendation]:
        try:
            prompt = self._build_prompt(profile, dishes, req)
            raw = await self._call_llm(prompt)
            if not raw:
                logger.warning("Empty LLM response, falling back")
                return self._fallback_recommendations(profile, dishes, req.limit)

            parsed = self._parse_llm_response(raw, dishes)
            return parsed if parsed else self._fallback_recommendations(profile, dishes, req.limit)
        except Exception as exc:
            logger.error("LLM recommendation failed: %s", exc)
            return self._fallback_recommendations(profile, dishes, req.limit)

    def _build_prompt(
        self,
        profile: dict[str, Any],
        dishes: list[dict[str, Any]],
        req: RecommendRequest,
    ) -> str:
        preferences = profile.get("preferences", {})
        recent_orders = profile.get("orderHistory", [])[-10:]

        # Simplify dishes to stay within token budget
        dish_lines: list[dict] = []
        for d in dishes[:50]:
            dish_lines.append(
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "description": (d.get("description") or "")[:100],
                    "price": d.get("price"),
                    "popularity": d.get("popularity", 0),
                    "categoryId": d.get("categoryId"),
                }
            )

        context_parts: list[str] = []
        if req.time_of_day:
            context_parts.append(f"Time of day: {req.time_of_day}")
        if req.cart_item_ids:
            context_parts.append(f"Already in cart: {req.cart_item_ids}")

        return f"""You are a restaurant recommendation expert. Recommend {req.limit} dishes for this user.

USER PROFILE:
- Name: {profile.get("user", {}).get("firstName", "")} {profile.get("user", {}).get("lastName", "")}
- Preferences: {json.dumps(preferences)}
- Total Orders: {len(recent_orders)}
- Recent Orders: {len(recent_orders)} recent orders

CONTEXT: {"; ".join(context_parts) if context_parts else "None"}

AVAILABLE DISHES ({len(dish_lines)} dishes):
{json.dumps(dish_lines, indent=2)}

Respond ONLY with a JSON array of recommendations:
[
  {{
    "dish_id": 1,
    "confidence_score": 0.95,
    "explanation": "Perfect for your Italian preferences and past orders"
  }}
]

Consider user preferences, dietary restrictions, price range, and context.
Return ONLY the JSON array, no additional text."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_llm(self, prompt: str) -> str:
        if self.provider == "gemini" and self.model:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        return ""

    def _parse_llm_response(
        self,
        raw: str,
        dishes: list[dict[str, Any]],
    ) -> list[Recommendation]:
        try:
            # Extract JSON from possible markdown fences
            text = raw.strip()
            if "```json" in text:
                text = text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "[" in text and "]" in text:
                text = text[text.find("[") : text.rfind("]") + 1]

            items = json.loads(text)
            if not isinstance(items, list):
                return []

            lookup = {d["id"]: d for d in dishes}
            recs: list[Recommendation] = []
            for item in items:
                dish_id = item.get("dish_id")
                if dish_id and dish_id in lookup:
                    recs.append(
                        Recommendation(
                            dish=_dish_info_from_backend(lookup[dish_id]),
                            confidence_score=min(max(float(item.get("confidence_score", 0.5)), 0), 1),
                            explanation=item.get("explanation", "Recommended based on your preferences"),
                            source="llm",
                        )
                    )
            return recs
        except (json.JSONDecodeError, Exception) as exc:
            logger.error("Failed to parse LLM response: %s", exc)
            return []

    # ── Fallback path ──

    def _fallback_recommendations(
        self,
        profile: dict[str, Any],
        dishes: list[dict[str, Any]],
        limit: int,
    ) -> list[Recommendation]:
        logger.info("Using fallback recommendation algorithm")
        preferences = profile.get("preferences", {})
        price_range = preferences.get("price_range", {})
        max_price = price_range.get("max", float("inf"))
        min_price = price_range.get("min", 0)
        cuisine_prefs = [c.lower() for c in preferences.get("cuisine_preferences", [])]

        scored: list[tuple[dict, float]] = []
        for d in dishes:
            if not d.get("isAvailable", True):
                continue
            price = d.get("price", 0)
            if price > max_price or price < min_price:
                continue

            score = d.get("popularity", 0) / 10.0
            if min_price <= price <= max_price * 0.8:
                score += 0.2

            name_lower = (d.get("name") or "").lower()
            desc_lower = (d.get("description") or "").lower()
            for cuisine in cuisine_prefs:
                if cuisine in name_lower or cuisine in desc_lower:
                    score += 0.3
                    break

            scored.append((d, min(score, 1.0)))

        scored.sort(key=lambda x: x[1], reverse=True)

        recs: list[Recommendation] = []
        for d, score in scored[:limit]:
            recs.append(
                Recommendation(
                    dish=_dish_info_from_backend(d),
                    confidence_score=score,
                    explanation=f"Popular choice (score: {score:.2f}) matching your preferences",
                    source="fallback",
                )
            )
        return recs
