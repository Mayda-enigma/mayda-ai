"""
Recommendation routes — dish recommendations powered by LLM.
POST /recommendations — matches backend gateway contract (RC-003).
GET  /health          — public health check.
"""

from fastapi import APIRouter, Depends, Request

from src.api.deps import RecommendationServiceDep
from src.middleware.service_auth import require_service_token
from src.schemas.recommendation_schema import RecommendRequest, RecommendResponse

router = APIRouter(tags=["Recommendation"])


# ── Public ──


@router.get("/health")
async def health_check():
    """Public health probe — no auth required."""
    return {"status": "healthy", "service": "Mayda AI"}


# ── Protected ──


@router.post(
    "/recommendations",
    response_model=RecommendResponse,
    dependencies=[Depends(require_service_token)],
)
async def post_recommendations(
    body: RecommendRequest,
    request: Request,
    service: RecommendationServiceDep,
):
    """Generate AI-powered recommendations for a user."""
    request_id: str | None = getattr(request.state, "request_id", None)
    return await service.recommend(body, request_id=request_id)
