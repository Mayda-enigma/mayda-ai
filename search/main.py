"""
FastAPI CRUD operations for ChromaDB dish management.
This module provides REST API endpoints for creating, reading, updating, and deleting dishes in ChromaDB.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union, Optional
import numpy as np
from contextlib import asynccontextmanager
from chromadb_helper import ChromaEmbeddingsDatabase
from generate_embeddings import EmbedGenerator
from model import MultilingualEmbeddingModel

# Initialize database and embedding generator (lazy loading)
chroma_db = ChromaEmbeddingsDatabase(collection_name="dishes")
embed_generator = None
multilingual_model = None

def get_embed_generator():
    """Lazy initialization of embedding generator"""
    global embed_generator
    if embed_generator is None:
        embed_generator = EmbedGenerator()
    return embed_generator

def get_multilingual_model():
    """Lazy initialization of multilingual embedding model"""
    global multilingual_model
    if multilingual_model is None:
        multilingual_model = MultilingualEmbeddingModel()
    return multilingual_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB on application startup"""
    chroma_db.initialize_database()
    print("ChromaDB initialized successfully")
    yield
    # Cleanup if needed

# Initialize FastAPI app
app = FastAPI(
    title="Dish Search API",
    description="CRUD operations for dish management with vector embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models for request/response
class DishCreate(BaseModel):
    id: int = Field(..., description="Unique identifier for the dish")
    name: str = Field(..., description="Name of the dish")
    ingredients: Union[str, List[str]] = Field(..., description="Ingredients as string or list")
    price: Union[float, str] = Field(..., description="Price of the dish")
    popularity: Union[float, str] = Field(..., description="Popularity rating")
    menucategory: str = Field(..., description="Menu category")
    menu: str = Field(..., description="Menu name")
    restaurant_name: str = Field(..., description="Restaurant name")
    restaurant_description: str = Field(..., description="Restaurant description")

class DishUpdate(BaseModel):
    id: int = Field(..., description="Unique identifier for the dish")
    name: str = Field(..., description="Name of the dish")
    ingredients: Union[str, List[str]] = Field(..., description="Ingredients as string or list")
    price: Union[float, str] = Field(..., description="Price of the dish")
    popularity: Union[float, str] = Field(..., description="Popularity rating")
    menucategory: str = Field(..., description="Menu category")
    menu: str = Field(..., description="Menu name")
    restaurant_name: str = Field(..., description="Restaurant name")
    restaurant_description: str = Field(..., description="Restaurant description")

class SimilaritySearch(BaseModel):
    embedding: List[float] = Field(..., description="Embedding vector for similarity search")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")

class DishDelete(BaseModel):
    id: int = Field(..., description="ID of the dish to delete")

class DishResponse(BaseModel):
    message: str
    dish_id: Optional[int] = None

class SimilarityResponse(BaseModel):
    similar_dish_ids: List[str]
    distances: List[float]
    metadata: List[Dict[str, Any]]

class TextSearchRequest(BaseModel):
    query: str = Field(..., description="Text query for dish search in any supported language")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")

class TextSearchResponse(BaseModel):
    dish_ids: List[str] = Field(..., description="Array of dish IDs matching the search query")

# Initialize database on startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB on application startup"""
    chroma_db.initialize_database()
    print("ChromaDB initialized successfully")
    yield
    # Cleanup if needed

# Update FastAPI app with lifespan
app = FastAPI(
    title="Dish Search API",
    description="CRUD operations for dish management with vector embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# CREATE - POST endpoint
@app.post("/dishes", response_model=DishResponse)
async def create_dish(dish: DishCreate):
    """
    Create a new dish with embedding generation and store in ChromaDB
    
    Args:
        dish: DishCreate model with all dish information
        
    Returns:
        DishResponse with success message and dish ID
    """
    try:
        # Check if dish ID already exists
        existing_dish = chroma_db.get_embedding_by_id(dish.id)
        if existing_dish is not None:
            raise HTTPException(status_code=400, detail=f"Dish with ID {dish.id} already exists")
        
        # Generate embedding for the dish
        embedding = get_embed_generator().generate_embedding(dish)
        
        # Prepare metadata (all dish info except ID)
        metadata = {
            "name": dish.name,
            "ingredients": dish.ingredients if isinstance(dish.ingredients, str) else ", ".join(dish.ingredients),
            "price": str(dish.price),
            "popularity": str(dish.popularity),
            "menucategory": dish.menucategory,
            "menu": dish.menu,
            "restaurant_name": dish.restaurant_name,
            "restaurant_description": dish.restaurant_description
        }
        
        # Add to ChromaDB
        chroma_db.add_embedding(
            embedding_id=dish.id,
            embedding_vector=embedding,
            metadata=metadata
        )
        
        return DishResponse(
            message=f"Dish '{dish.name}' created successfully",
            dish_id=dish.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating dish: {str(e)}")

# READ - GET endpoint
@app.post("/dishes/search", response_model=SimilarityResponse)
async def search_similar_dishes(search_request: SimilaritySearch):
    """
    Find similar dishes based on embedding vector
    
    Args:
        search_request: SimilaritySearch model with embedding and max_results
        
    Returns:
        SimilarityResponse with similar dish IDs, distances, and metadata
    """
    try:
        # Search for similar embeddings
        results = chroma_db.search_similar(
            query_vector=search_request.embedding,
            n_results=search_request.max_results
        )
        
        return SimilarityResponse(
            similar_dish_ids=results['ids'],
            distances=results['distances'],
            metadata=results['metadatas']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching dishes: {str(e)}")

# Text-based search endpoint with multilingual support
@app.post("/dishes/search-by-text", response_model=TextSearchResponse)
async def search_dishes_by_text(search_request: TextSearchRequest):
    """
    Search for dishes using natural language text queries in multiple languages
    (Arabic, French, English, Darija)
    
    Args:
        search_request: TextSearchRequest model with query text and max_results
        
    Returns:
        TextSearchResponse with array of dish IDs that match the query
    """
    try:
        # Get the multilingual embedding model
        multilingual_model = get_multilingual_model()
        
        # Generate embedding from the text query
        embedding_vector, _ = multilingual_model.embed_multilingual_query(search_request.query)
        
        # Search for similar dishes using the generated embedding
        results = chroma_db.search_similar(
            query_vector=embedding_vector,
            n_results=search_request.max_results
        )
        
        # Return just the dish IDs as requested
        return TextSearchResponse(dish_ids=results['ids'])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching dishes by text: {str(e)}")

# UPDATE - PUT endpoint
@app.put("/dishes/{dish_id}", response_model=DishResponse)
async def update_dish(dish_id: int, dish: DishUpdate):
    """
    Update an existing dish with new data and regenerate embedding
    
    Args:
        dish_id: ID of the dish to update
        dish: DishUpdate model with updated dish information
        
    Returns:
        DishResponse with success message
    """
    try:
        # Check if the dish exists
        existing_dish = chroma_db.get_embedding_by_id(dish_id)
        if existing_dish is None:
            raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found")
        
        # Verify that the ID in the request matches the path parameter
        if dish.id != dish_id:
            raise HTTPException(status_code=400, detail="Dish ID in request body must match path parameter")
        
        # Generate new embedding for the updated dish
        embedding = get_embed_generator().generate_embedding(dish)
        
        # Prepare updated metadata
        metadata = {
            "name": dish.name,
            "ingredients": dish.ingredients if isinstance(dish.ingredients, str) else ", ".join(dish.ingredients),
            "price": str(dish.price),
            "popularity": str(dish.popularity),
            "menucategory": dish.menucategory,
            "menu": dish.menu,
            "restaurant_name": dish.restaurant_name,
            "restaurant_description": dish.restaurant_description
        }
        
        # Update in ChromaDB
        chroma_db.update_embedding(
            embedding_id=dish_id,
            embedding_vector=embedding,
            metadata=metadata
        )
        
        return DishResponse(
            message=f"Dish '{dish.name}' updated successfully",
            dish_id=dish_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dish: {str(e)}")

# DELETE - DELETE endpoint
@app.delete("/dishes/{dish_id}", response_model=DishResponse)
async def delete_dish(dish_id: int):
    """
    Delete a dish by its ID
    
    Args:
        dish_id: ID of the dish to delete
        
    Returns:
        DishResponse with success message
    """
    try:
        # Check if the dish exists
        existing_dish = chroma_db.get_embedding_by_id(dish_id)
        if existing_dish is None:
            raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found")
        
        # Delete from ChromaDB
        chroma_db.delete_embedding(dish_id)
        
        return DishResponse(
            message=f"Dish with ID {dish_id} deleted successfully",
            dish_id=dish_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting dish: {str(e)}")

# Additional endpoints for database management

@app.get("/dishes/info")
async def get_database_info():
    """Get information about the ChromaDB collection"""
    try:
        info = chroma_db.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database info: {str(e)}")

@app.get("/dishes/list")
async def list_all_dish_ids():
    """Get all dish IDs in the database"""
    try:
        ids = chroma_db.list_all_ids()
        return {"dish_ids": ids, "count": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing dish IDs: {str(e)}")

@app.get("/dishes/{dish_id}")
async def get_dish_by_id(dish_id: int):
    """Get a specific dish by its ID"""
    try:
        dish = chroma_db.get_embedding_by_id(dish_id)
        if dish is None:
            raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found")
        
        return {
            "id": dish["id"],
            "metadata": dish["metadata"],
            "embedding_dimensions": len(dish["embedding"]) if dish["embedding"] else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dish: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Dish Search API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)