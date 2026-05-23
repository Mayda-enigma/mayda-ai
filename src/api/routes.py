"""
API routes for the recommendation service.
POST /recommendations — matches backend gateway contract (RC-003).
GET  /health          — public health check.
"""
from fastapi import APIRouter, Depends, Request

from src.middleware.service_auth import require_service_token
from src.schemas.recommendation_schema import RecommendRequest, RecommendResponse
from src.services.recommendation_service import RecommendationService

router = APIRouter()


def _get_recommendation_service(request: Request) -> RecommendationService:
    """Retrieve the RecommendationService stored on app.state during lifespan."""
    return request.app.state.recommendation_service


# ── Public ──

@router.get("/health")
async def health_check():
    """Public health probe — no auth required."""
    return {"status": "healthy", "service": "recommendation"}


# ── Protected ──

@router.post(
    "/recommendations",
    response_model=RecommendResponse,
    dependencies=[Depends(require_service_token)],
)
async def post_recommendations(
    body: RecommendRequest,
    request: Request,
    service: RecommendationService = Depends(_get_recommendation_service),
):
    """Generate AI-powered recommendations for a user."""
    request_id: str | None = getattr(request.state, "request_id", None)
    return await service.recommend(body, request_id=request_id)
