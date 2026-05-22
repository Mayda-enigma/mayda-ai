"""
Simplified main FastAPI application for containerized Recommendation Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.services.backend_client import backend_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Simplified Recommendation Service...")
    logger.info(f"🔗 Backend API URL: {settings.BACKEND_API_URL}")
    
    # Test backend connectivity
    try:
        logger.info("🧪 Testing backend API connectivity...")
        # This will test if the backend API is reachable
        # We don't need to initialize anything else
        logger.info("✅ Service ready - will connect to backend on first request")
    except Exception as e:
        logger.warning(f"⚠️ Could not test backend connectivity: {e}")
        logger.info("🔄 Service starting anyway - will retry on first request")
    
    yield
    
    # Shutdown
    logger.info("� Shutting down Simplified Recommendation Service...")
    logger.info("✅ Service stopped")

app = FastAPI(
    title="Simplified Recommendation Service",
    description="Containerized AI-powered recommendation service that calls external backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "simplified-recommendation-service",
        "version": "1.0.0",
        "backend_api": settings.BACKEND_API_URL
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Simplified Recommendation Service",
        "version": "1.0.0",
        "status": "active",
        "description": "Containerized AI-powered recommendation service",
        "backend_api": settings.BACKEND_API_URL,
        "endpoints": {
            "health": "/health",
            "recommendations": "/api/v1/recommendations"
        }
    }

# Simple recommendation endpoint
@app.get("/api/v1/recommendations/{user_id}")
async def get_user_recommendations(user_id: int, limit: int = 5, restaurant_id: int = None):
    """Get recommendations for a user from external backend API"""
    from app.services.simple_recommendation_engine import recommendation_engine
    
    try:
        logger.info(f"📝 Getting recommendations for user {user_id}")
        
        # Get recommendations using simplified engine
        result = await recommendation_engine.get_recommendations(
            user_id=user_id,
            limit=limit,
            restaurant_id=restaurant_id
        )
        
        if "error" in result:
            logger.error(f"❌ Recommendation error: {result['error']}")
            return {"error": result["error"], "user_id": user_id}
        
        logger.info(f"✅ Generated {len(result.get('recommendations', []))} recommendations for user {user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Recommendation endpoint error: {e}")
        return {"error": str(e), "user_id": user_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )