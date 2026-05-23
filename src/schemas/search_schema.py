"""
Pydantic schemas for the search service.
"""
from typing import Any

from pydantic import BaseModel, Field

# ── Search Schemas (SR-006 backend contract) ──

class SearchRequest(BaseModel):
    """Request body for POST /search."""
    query: str = Field(..., description="Query text in any language")
    restaurant_id: int | None = Field(None, description="Optional filter by restaurant ID")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results to return")


class SearchResultItem(BaseModel):
    """A single search result item."""
    dish_id: int = Field(..., description="ID of the matching dish")
    score: float = Field(..., description="Cosine similarity score (higher is more similar)")
    name: str = Field(..., description="Name of the dish")
    restaurant_name: str = Field(..., description="Name of the restaurant serving the dish")


class SearchResponse(BaseModel):
    """Response body for POST /search."""
    results: list[SearchResultItem] = Field(default_factory=list)
    language_detected: str = Field(..., description="Detected language code (en, fr, ar, da)")


# ── Sync / CRUD Schemas ──

class DishCreate(BaseModel):
    """Request schema for creating a dish in search index."""
    id: int = Field(..., description="Unique identifier for the dish")
    name: str = Field(..., description="Name of the dish")
    ingredients: str | list[str] = Field(..., description="Ingredients list or string")
    price: float | str = Field(..., description="Price of the dish")
    popularity: float | str = Field(..., description="Popularity score")
    menucategory: str = Field(..., description="Category of the menu item")
    menu: str = Field(..., description="Menu name")
    restaurant_name: str = Field(..., description="Restaurant name")
    restaurant_description: str = Field(..., description="Restaurant description")
    restaurant_id: int | None = Field(None, description="Optional restaurant ID for filtering")


class DishUpdate(DishCreate):
    """Request schema for updating a dish in the search index.

    Identical shape to DishCreate — kept as a distinct class so the OpenAPI
    schema and IDE hints make create vs update operations explicit at the
    route layer.
    """


class DishResponse(BaseModel):
    """Standard sync response."""
    message: str
    dish_id: int | None = None


# ── Legacy Search Schemas (Backwards compatibility) ──

class SimilaritySearch(BaseModel):
    """Request body for legacy POST /dishes/search."""
    embedding: list[float] = Field(..., description="Vector embedding for search query")
    max_results: int | None = Field(10, description="Max results limit")


class SimilarityResponse(BaseModel):
    """Response body for legacy POST /dishes/search."""
    similar_dish_ids: list[str]
    distances: list[float]
    metadata: list[dict[str, Any]]


class TextSearchRequest(BaseModel):
    """Request body for legacy POST /dishes/search-by-text."""
    query: str = Field(..., description="Query text")
    max_results: int | None = Field(10, description="Max results limit")


class TextSearchResponse(BaseModel):
    """Response body for legacy POST /dishes/search-by-text."""
    dish_ids: list[str]
