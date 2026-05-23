"""
FastAPI application entry point for Mayda AI.
"""
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.inventory_routes import router as inventory_router
from src.api.routes import router
from src.api.search_routes import router as search_router
from src.api.voice_routes import router as voice_router
from src.core.config import settings
from src.middleware.request_id import RequestIdMiddleware
from src.services.backend_client import BackendAPIClient
from src.services.chromadb_service import ChromaEmbeddingsDatabase
from src.services.embedding_generator import EmbedGenerator
from src.services.inventory_db_service import SessionLocal, init_inventory_db
from src.services.inventory_forecaster import DatabaseIntegratedForecaster
from src.services.multilingual_embedding import MultilingualEmbeddingModel
from src.services.recommendation_service import RecommendationService
from src.services.search_service import SearchService
from src.services.voice_transcribe import Transcriber

# ── Logging ──
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize recommendation, search, inventory, and voice services.
       Shutdown: close httpx client."""
    logger.info("Starting %s v%s on port %s", settings.PROJECT_NAME, settings.VERSION, settings.PORT)
    logger.info("Backend API URL: %s", settings.BACKEND_API_URL)

    # Shared async HTTP client — reused across all requests
    http_client = httpx.AsyncClient()
    backend = BackendAPIClient(http_client)
    rec_service = RecommendationService(backend)

    # Initialize Search Service components
    chroma_db = ChromaEmbeddingsDatabase(
        persist_directory=settings.CHROMA_DB_DIR,
        collection_name=settings.CHROMA_COLLECTION_NAME,
    )
    chroma_db.initialize_database()
    embed_gen = EmbedGenerator()
    multi_embed = MultilingualEmbeddingModel()

    search_service = SearchService(
        chroma_db=chroma_db,
        embed_generator=embed_gen,
        multilingual_model=multi_embed,
    )

    # Initialize Inventory database and seed values if empty
    db_session = SessionLocal()
    try:
        init_inventory_db(db_session)
    finally:
        db_session.close()

    # Initialize and load/train Inventory Forecaster models (joblib persistence)
    forecaster = DatabaseIntegratedForecaster()
    loaded_cached = forecaster.load_models(settings.INVENTORY_MODEL_PATH)
    if not loaded_cached:
        logger.info("No cached inventory models found. Training from historical data/generating seed data...")
        db_session = SessionLocal()
        try:
            forecaster.train_models(db_session, use_database=True)
            forecaster.save_models(settings.INVENTORY_MODEL_PATH)
        finally:
            db_session.close()

    # Store on app.state so routes can access via Depends
    app.state.http_client = http_client
    app.state.recommendation_service = rec_service
    app.state.search_service = search_service
    app.state.forecaster = forecaster

    # Eager Whisper Transcriber instantiation
    transcriber = Transcriber(model_size=settings.WHISPER_MODEL)
    transcriber.initialize_model()
    app.state.transcriber = transcriber

    logger.info("Recommendation service ready (LLM provider: %s)", rec_service.provider)
    logger.info("Search service ready (ChromaDB collection: %s)", settings.CHROMA_COLLECTION_NAME)
    logger.info("Inventory forecaster service ready (persisted at: %s)", settings.INVENTORY_MODEL_PATH)
    logger.info("Voice transcriber ready (Whisper model: %s)", settings.WHISPER_MODEL)

    yield

    # Cleanup
    await http_client.aclose()
    logger.info("Shutting down %s", settings.PROJECT_NAME)


# ── App ──

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Mayda AI — recommendation, search, inventory forecasting, and voice processing",
    openapi_tags=[
        {"name": "Recommendation", "description": "AI-powered dish recommendations"},
        {"name": "Search", "description": "Semantic dish search with multilingual support"},
        {"name": "Inventory", "description": "Consumption forecasting and restock recommendations"},
        {"name": "Voice", "description": "Speech transcription and order parsing"},
    ],
    lifespan=lifespan,
)

# ── Middleware ──

# Request-ID first (outermost)
app.add_middleware(RequestIdMiddleware)

# CORS — restricted to gateway origin (RC-005: no more ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.GATEWAY_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──

app.include_router(router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(voice_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "capabilities": {
            "Recommendation": {
                "recommendations": "POST /api/recommendations",
            },
            "Search": {
                "search": "POST /api/search",
                "dishes_crud": "GET/PUT/DELETE /api/dishes",
            },
            "Inventory": {
                "forecast": "POST /api/forecast",
                "bulk_forecast": "POST /api/forecast/bulk",
                "restock": "GET /api/recommendations/restock",
                "consumption": "POST /api/consumption",
            },
            "Voice": {
                "transcribe": "POST /api/transcribe",
                "parse_chef": "POST /api/parse/chef",
                "parse_order": "POST /api/parse/order",
            },
        },
        "health": "/api/health",
        "docs": "/docs",
    }


# ── Dev entry point ──

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
