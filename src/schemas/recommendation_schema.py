"""
Pydantic schemas for the Recommendation AI.
Matches the backend gateway contract (RC-003).
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Request ──


class RecommendRequest(BaseModel):
    """POST /recommendations request body — matches backend proxy contract."""

    user_id: int
    cart_item_ids: list[int] = Field(default_factory=list)
    time_of_day: str | None = None
    limit: int = Field(default=5, ge=1, le=20)
    restaurant_id: int | None = None


# ── Response ──


class DishInfo(BaseModel):
    """Dish details embedded in a recommendation."""

    id: int
    name: str
    description: str = ""
    price: float
    popularity: float = 0.0
    is_available: bool = True
    category_id: int | None = None


class Recommendation(BaseModel):
    """A single dish recommendation."""

    dish: DishInfo
    confidence_score: float = Field(ge=0.0, le=1.0)
    explanation: str = "Recommended based on your preferences"
    source: str = "llm"


class RecommendResponse(BaseModel):
    """POST /recommendations response body."""

    user_id: int
    recommendations: list[Recommendation]
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    model: str = "none"
    processing_time: float = 0.0
    total_available_dishes: int = 0
