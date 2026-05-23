"""Shared FastAPI dependency providers.

Each long-lived service is built once during lifespan and attached to
`app.state`; route handlers reach it via `Depends(...)`. Centralising the
two-liner getters here keeps the per-route files focused on HTTP shape.
"""

from typing import Annotated

from fastapi import Depends, Request

from src.services.inventory_forecaster import DatabaseIntegratedForecaster
from src.services.recommendation_service import RecommendationService
from src.services.search_service import SearchService
from src.services.voice_transcribe import Transcriber


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service


def get_forecaster(request: Request) -> DatabaseIntegratedForecaster:
    return request.app.state.forecaster


def get_transcriber(request: Request) -> Transcriber:
    return request.app.state.transcriber


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
ForecasterDep = Annotated[DatabaseIntegratedForecaster, Depends(get_forecaster)]
TranscriberDep = Annotated[Transcriber, Depends(get_transcriber)]
