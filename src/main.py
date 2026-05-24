"""
FastAPI application entry point for Mayda AI.
"""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.inventory_routes import router as inventory_router
from src.api.nutrition_routes import router as nutrition_router
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
    """Startup: initialize HTTP client only. Services are lazy-loaded.
    Shutdown: close httpx client."""
    logger.info("Starting %s v%s on port %s", settings.PROJECT_NAME, settings.VERSION, settings.PORT)
    logger.info("Backend API URL: %s", settings.BACKEND_API_URL)

    # Shared async HTTP client — reused across all requests
    http_client = httpx.AsyncClient()
    
    # Store on app.state so routes can access via Depends
    app.state.http_client = http_client
    
    # Services will be initialized lazily on first use
    app.state.recommendation_service = None
    app.state.search_service = None
    app.state.forecaster = None
    app.state.transcriber = None

    logger.info("FastAPI initialized with lazy service loading")

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
        {"name": "Voice", "description": "Speech transcription and order/chef command parsing"},
        {"name": "Nutrition", "description": "Food image analysis with calorie and macro estimation"},
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
app.include_router(nutrition_router, prefix="/api")


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


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """Serve the nutrition vision agent demo page."""
    demo_path = Path(__file__).resolve().parent.parent / "demo.html"
    return demo_path.read_text()


# ── Dev entry point ──

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
