"""
Search routes — semantic dish search with multilingual support.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import SearchServiceDep
from src.middleware.service_auth import require_service_token
from src.schemas.search_schema import (
    DishCreate,
    DishResponse,
    DishUpdate,
    SearchRequest,
    SearchResponse,
    SimilarityResponse,
    SimilaritySearch,
    TextSearchRequest,
    TextSearchResponse,
)

router = APIRouter(tags=["Search"])


# ── Search Endpoints ──


@router.post(
    "/search",
    response_model=SearchResponse,
    dependencies=[Depends(require_service_token)],
)
async def search_dishes(
    body: SearchRequest,
    service: SearchServiceDep,
):
    """
    Search for dishes by natural language query (Arabic, French, English, Darija).
    Matches backend gateway contract (SR-006).
    """
    return await service.search(query=body.query, restaurant_id=body.restaurant_id, limit=body.limit)


# ── CRUD Sync Endpoints (SR-007 area) ──


@router.post(
    "/dishes",
    response_model=DishResponse,
    dependencies=[Depends(require_service_token)],
)
async def create_dish(
    body: DishCreate,
    service: SearchServiceDep,
):
    """Index a new dish."""
    return await service.create_dish(dish=body)


@router.put(
    "/dishes/{dish_id}",
    response_model=DishResponse,
    dependencies=[Depends(require_service_token)],
)
async def update_dish(
    dish_id: int,
    body: DishUpdate,
    service: SearchServiceDep,
):
    """Update an existing indexed dish."""
    return await service.update_dish(dish_id=dish_id, dish=body)


@router.delete(
    "/dishes/{dish_id}",
    response_model=DishResponse,
    dependencies=[Depends(require_service_token)],
)
async def delete_dish(
    dish_id: int,
    service: SearchServiceDep,
):
    """Delete a dish from the index."""
    return await service.delete_dish(dish_id=dish_id)


# ── Database Management & Info Endpoints ──


@router.get(
    "/dishes/info",
    dependencies=[Depends(require_service_token)],
)
async def get_database_info(
    service: SearchServiceDep,
):
    """Get ChromaDB collection statistics and status."""
    return service.chroma_db.get_collection_info()


@router.get(
    "/dishes/list",
    dependencies=[Depends(require_service_token)],
)
async def list_all_dish_ids(
    service: SearchServiceDep,
):
    """List all indexed dish IDs."""
    ids = service.chroma_db.list_all_ids()
    return {"dish_ids": ids, "count": len(ids)}


@router.get(
    "/dishes/{dish_id}",
    dependencies=[Depends(require_service_token)],
)
async def get_dish_by_id(
    dish_id: int,
    service: SearchServiceDep,
):
    """Get indexed metadata for a specific dish ID."""
    dish = service.chroma_db.get_embedding_by_id(dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found in index")
    return {
        "id": dish["id"],
        "metadata": dish["metadata"],
        "embedding_dimensions": len(dish["embedding"]) if dish["embedding"] else 0,
    }


# ── Legacy Search Endpoints ──


@router.post(
    "/dishes/search",
    response_model=SimilarityResponse,
    dependencies=[Depends(require_service_token)],
)
async def search_similar_dishes(
    body: SimilaritySearch,
    service: SearchServiceDep,
):
    """Legacy vector-based similarity search."""
    results = await service.search_similar_dishes(
        query_vector=body.embedding,
        max_results=body.max_results or 10,
    )
    return SimilarityResponse(
        similar_dish_ids=results.get("ids", []),
        distances=results.get("distances", []),
        metadata=results.get("metadatas", []),
    )


@router.post(
    "/dishes/search-by-text",
    response_model=TextSearchResponse,
    dependencies=[Depends(require_service_token)],
)
async def search_dishes_by_text(
    body: TextSearchRequest,
    service: SearchServiceDep,
):
    """Legacy text-based query search returning a list of matching IDs."""
    ids = await service.search_dishes_by_text(
        query=body.query,
        max_results=body.max_results or 10,
    )
    return TextSearchResponse(dish_ids=ids)
