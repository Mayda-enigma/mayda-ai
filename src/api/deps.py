"""Shared FastAPI dependency providers.

Each long-lived service is built once during lifespan and attached to
`app.state`; route handlers reach it via `Depends(...)`. Centralising the
two-liner getters here keeps the per-route files focused on HTTP shape.
"""

import logging
from typing import Annotated

from fastapi import Depends, Request

from src.core.config import settings
from src.services.backend_client import BackendAPIClient
from src.services.chromadb_service import ChromaEmbeddingsDatabase
from src.services.embedding_generator import EmbedGenerator
from src.services.inventory_db_service import SessionLocal, init_inventory_db
from src.services.inventory_forecaster import DatabaseIntegratedForecaster
from src.services.multilingual_embedding import MultilingualEmbeddingModel
from src.services.recommendation_service import RecommendationService
from src.services.search_service import SearchService
from src.services.voice_transcribe import Transcriber

logger = logging.getLogger(__name__)


def get_recommendation_service(request: Request) -> RecommendationService:
    """Lazy-load recommendation service on first use."""
    if request.app.state.recommendation_service is None:
        logger.info("Initializing Recommendation Service...")
        backend = BackendAPIClient(request.app.state.http_client)
        request.app.state.recommendation_service = RecommendationService(backend)
        logger.info("Recommendation service initialized (LLM provider: %s)", request.app.state.recommendation_service.provider)
    return request.app.state.recommendation_service


def get_search_service(request: Request) -> SearchService:
    """Lazy-load search service on first use."""
    if request.app.state.search_service is None:
        logger.info("Initializing Search Service...")
        chroma_db = ChromaEmbeddingsDatabase(
            persist_directory=settings.CHROMA_DB_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME,
        )
        chroma_db.initialize_database()
        embed_gen = EmbedGenerator()
        multi_embed = MultilingualEmbeddingModel()
        
        request.app.state.search_service = SearchService(
            chroma_db=chroma_db,
            embed_generator=embed_gen,
            multilingual_model=multi_embed,
        )
        logger.info("Search service initialized (ChromaDB collection: %s)", settings.CHROMA_COLLECTION_NAME)
    return request.app.state.search_service


def get_forecaster(request: Request) -> DatabaseIntegratedForecaster:
    """Lazy-load forecaster service on first use."""
    if request.app.state.forecaster is None:
        logger.info("Initializing Inventory Forecaster...")
        
        # Initialize inventory database
        db_session = SessionLocal()
        try:
            init_inventory_db(db_session)
        finally:
            db_session.close()
        
        # Load or train forecaster models
        forecaster = DatabaseIntegratedForecaster()
        loaded_cached = forecaster.load_models(settings.INVENTORY_MODEL_PATH)
        if not loaded_cached:
            logger.info("No cached inventory models found. Training from historical data...")
            db_session = SessionLocal()
            try:
                forecaster.train_models(db_session, use_database=True)
                forecaster.save_models(settings.INVENTORY_MODEL_PATH)
            finally:
                db_session.close()
        
        request.app.state.forecaster = forecaster
        logger.info("Inventory forecaster initialized (persisted at: %s)", settings.INVENTORY_MODEL_PATH)
    return request.app.state.forecaster


def get_transcriber(request: Request) -> Transcriber:
    """Lazy-load transcriber service on first use."""
    if request.app.state.transcriber is None:
        logger.info("Initializing Whisper Transcriber...")
        transcriber = Transcriber(model_size=settings.WHISPER_MODEL)
        transcriber.initialize_model()
        request.app.state.transcriber = transcriber
        logger.info("Voice transcriber initialized (Whisper model: %s)", settings.WHISPER_MODEL)
    return request.app.state.transcriber


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
ForecasterDep = Annotated[DatabaseIntegratedForecaster, Depends(get_forecaster)]
TranscriberDep = Annotated[Transcriber, Depends(get_transcriber)]
