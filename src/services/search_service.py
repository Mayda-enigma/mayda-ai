"""
Orchestration service for dish search and indexing operations.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from src.services.chromadb_service import ChromaEmbeddingsDatabase
from src.services.embedding_generator import EmbedGenerator
from src.services.multilingual_embedding import MultilingualEmbeddingModel
from src.schemas.search_schema import (
    DishCreate,
    DishUpdate,
    DishResponse,
    SearchResultItem,
    SearchResponse,
)

logger = logging.getLogger(__name__)


class SearchService:
    """
    SearchService orchestrates ChromaDB interactions, embedding generation,
    multilingual text search, and CRUD sync logic.
    """

    def __init__(
        self,
        chroma_db: ChromaEmbeddingsDatabase,
        embed_generator: EmbedGenerator,
        multilingual_model: MultilingualEmbeddingModel,
    ):
        self.chroma_db = chroma_db
        self.embed_generator = embed_generator
        self.multilingual_model = multilingual_model

    async def search(
        self, query: str, restaurant_id: Optional[int] = None, limit: int = 10
    ) -> SearchResponse:
        """
        Search for dishes by natural language query (Arabic, French, English, Darija).
        Supports filtering by restaurant_id and returns similarity scores.
        """
        try:
            # Detect language
            detected_lang = self.multilingual_model._detect_language(query)

            # Generate query embedding
            embedding_vector, _ = self.multilingual_model.embed_multilingual_query(query)

            # Prepare metadata filters
            where = None
            if restaurant_id is not None:
                where = {"restaurant_id": restaurant_id}

            # Search ChromaDB
            results = self.chroma_db.search_similar(
                query_vector=embedding_vector,
                n_results=limit,
                where=where,
            )

            # Format search result items
            search_items = []
            ids = results.get("ids", [])
            distances = results.get("distances", [])
            metadatas = results.get("metadatas", [])

            for i in range(len(ids)):
                dish_id_str = ids[i]
                distance = distances[i]
                metadata = metadatas[i] or {}

                # Calculate similarity score from cosine distance
                # Cosine distance is in [0, 2]. Cosine similarity is 1.0 - distance.
                score = round(1.0 - distance, 4)

                try:
                    dish_id = int(dish_id_str)
                except ValueError:
                    continue

                search_items.append(
                    SearchResultItem(
                        dish_id=dish_id,
                        score=score,
                        name=metadata.get("name", "Unknown"),
                        restaurant_name=metadata.get("restaurant_name", "Unknown"),
                    )
                )

            # Sort by score descending just in case
            search_items.sort(key=lambda x: x.score, reverse=True)

            return SearchResponse(results=search_items, language_detected=detected_lang)

        except Exception as exc:
            logger.error("Error executing query search: %s", exc)
            raise HTTPException(status_code=500, detail=f"Search execution failed: {str(exc)}")

    # ── CRUD operations for Dish Indexing ──

    async def create_dish(self, dish: DishCreate) -> DishResponse:
        """
        Create a new dish entry in ChromaDB with generated embeddings.
        """
        # Check if already exists
        existing = self.chroma_db.get_embedding_by_id(dish.id)
        if existing is not None:
            raise HTTPException(status_code=400, detail=f"Dish with ID {dish.id} already exists in index")

        try:
            # Generate embedding
            embedding = self.embed_generator.generate_embedding(dish)

            # Prepare metadata
            metadata = {
                "name": dish.name,
                "ingredients": dish.ingredients if isinstance(dish.ingredients, str) else ", ".join(dish.ingredients),
                "price": str(dish.price),
                "popularity": str(dish.popularity),
                "menucategory": dish.menucategory,
                "menu": dish.menu,
                "restaurant_name": dish.restaurant_name,
                "restaurant_description": dish.restaurant_description,
            }
            if dish.restaurant_id is not None:
                metadata["restaurant_id"] = dish.restaurant_id

            # Add to ChromaDB
            self.chroma_db.add_embedding(
                embedding_id=dish.id,
                embedding_vector=embedding,
                metadata=metadata,
            )

            logger.info("Dish '%s' (ID: %d) indexed successfully.", dish.name, dish.id)
            return DishResponse(
                message=f"Dish '{dish.name}' indexed successfully",
                dish_id=dish.id,
            )
        except Exception as exc:
            logger.error("Error creating dish in index: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error indexing dish: {str(exc)}")

    async def update_dish(self, dish_id: int, dish: DishUpdate) -> DishResponse:
        """
        Update an existing dish entry in ChromaDB and regenerate embeddings.
        """
        if dish.id != dish_id:
            raise HTTPException(status_code=400, detail="Dish ID in path and request body must match")

        existing = self.chroma_db.get_embedding_by_id(dish_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found in index")

        try:
            # Regenerate embedding
            embedding = self.embed_generator.generate_embedding(dish)

            # Prepare metadata
            metadata = {
                "name": dish.name,
                "ingredients": dish.ingredients if isinstance(dish.ingredients, str) else ", ".join(dish.ingredients),
                "price": str(dish.price),
                "popularity": str(dish.popularity),
                "menucategory": dish.menucategory,
                "menu": dish.menu,
                "restaurant_name": dish.restaurant_name,
                "restaurant_description": dish.restaurant_description,
            }
            if dish.restaurant_id is not None:
                metadata["restaurant_id"] = dish.restaurant_id

            # Update in ChromaDB
            self.chroma_db.update_embedding(
                embedding_id=dish_id,
                embedding_vector=embedding,
                metadata=metadata,
            )

            logger.info("Dish '%s' (ID: %d) updated in index successfully.", dish.name, dish.id)
            return DishResponse(
                message=f"Dish '{dish.name}' updated in index successfully",
                dish_id=dish_id,
            )
        except Exception as exc:
            logger.error("Error updating dish in index: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error updating dish in index: {str(exc)}")

    async def delete_dish(self, dish_id: int) -> DishResponse:
        """
        Remove a dish entry from ChromaDB index.
        """
        existing = self.chroma_db.get_embedding_by_id(dish_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Dish with ID {dish_id} not found in index")

        try:
            self.chroma_db.delete_embedding(dish_id)
            logger.info("Dish ID: %d deleted from index successfully.", dish_id)
            return DishResponse(
                message=f"Dish with ID {dish_id} deleted from index successfully",
                dish_id=dish_id,
            )
        except Exception as exc:
            logger.error("Error deleting dish from index: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error deleting dish from index: {str(exc)}")

    # ── Legacy Search Wrappers ──

    async def search_similar_dishes(
        self, query_vector: List[float], max_results: int = 10
    ) -> Dict[str, Any]:
        """Legacy similar dishes vector query search."""
        return self.chroma_db.search_similar(query_vector=query_vector, n_results=max_results)

    async def search_dishes_by_text(self, query: str, max_results: int = 10) -> List[str]:
        """Legacy text-based similar dishes query returning IDs list."""
        embedding_vector, _ = self.multilingual_model.embed_multilingual_query(query)
        results = self.chroma_db.search_similar(query_vector=embedding_vector, n_results=max_results)
        return results.get("ids", [])
