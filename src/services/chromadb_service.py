"""
ChromaDB helper for vector embeddings storage and retrieval.
Ported from mayda-ai/search/chromadb_helper.py.
"""

import logging
import os
from typing import Any

import chromadb
import numpy as np

logger = logging.getLogger(__name__)


class ChromaEmbeddingsDatabase:
    """
    ChromaDB interface for vector embeddings storage and retrieval.
    Creates a collection to store vectors with IDs and metadata.
    """

    def __init__(self, persist_directory: str | None = None, collection_name: str = "dishes"):
        """
        Initialize ChromaDB client and collection properties.
        """
        self.persist_directory = persist_directory or os.path.join(os.getcwd(), "chroma_db")
        self.collection_name = collection_name
        self.client: chromadb.PersistentClient | None = None
        self.collection: chromadb.Collection | None = None

    def initialize_database(self) -> None:
        """Initialize ChromaDB client and create/get the embeddings collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Vector embeddings storage for dishes search",
                    "hnsw:space": "cosine",
                },
            )

            logger.info("ChromaDB initialized at: %s", self.persist_directory)
            logger.info("Collection '%s' ready", self.collection_name)
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB: %s", exc)
            raise

    def add_embedding(
        self,
        embedding_id: str | int,
        embedding_vector: list[float] | np.ndarray,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a single embedding to the database.
        """
        if not self.collection:
            self.initialize_database()

        # Convert numpy array to list if needed
        if isinstance(embedding_vector, np.ndarray):
            embedding_vector = embedding_vector.tolist()

        str_id = str(embedding_id)

        # Add to collection
        self.collection.add(  # type: ignore
            ids=[str_id],
            embeddings=[embedding_vector],
            metadatas=[metadata] if metadata else None,
        )

    def add_embeddings_batch(
        self,
        embedding_ids: list[str | int],
        embedding_vectors: list[list[float]] | list[np.ndarray],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add multiple embeddings to the database in batch.
        """
        if not self.collection:
            self.initialize_database()

        str_ids = [str(id_) for id_ in embedding_ids]

        processed_vectors = []
        for vector in embedding_vectors:
            if isinstance(vector, np.ndarray):
                processed_vectors.append(vector.tolist())
            else:
                processed_vectors.append(vector)

        self.collection.add(  # type: ignore
            ids=str_ids,
            embeddings=processed_vectors,
            metadatas=metadatas,
        )

    def get_embedding_by_id(self, embedding_id: str | int) -> dict[str, Any] | None:
        """
        Retrieve an embedding by its ID.
        """
        if not self.collection:
            self.initialize_database()

        str_id = str(embedding_id)

        try:
            results = self.collection.get(  # type: ignore
                ids=[str_id], include=["embeddings", "metadatas"]
            )

            if results["ids"] and len(results["ids"]) > 0:
                embedding = None
                if "embeddings" in results and results["embeddings"] is not None and len(results["embeddings"]) > 0:
                    embedding = (
                        results["embeddings"][0].tolist()
                        if hasattr(results["embeddings"][0], "tolist")
                        else results["embeddings"][0]
                    )

                metadata = None
                if "metadatas" in results and results["metadatas"] is not None and len(results["metadatas"]) > 0:
                    metadata = results["metadatas"][0]

                return {"id": results["ids"][0], "embedding": embedding, "metadata": metadata}
            return None

        except Exception as exc:
            logger.error("Error retrieving embedding %s: %s", str_id, exc)
            return None

    def search_similar(
        self,
        query_vector: list[float] | np.ndarray,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar embeddings.
        """
        if not self.collection:
            self.initialize_database()

        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()

        results = self.collection.query(  # type: ignore
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where,
            include=["distances", "metadatas"],
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        }

    def update_embedding(
        self,
        embedding_id: str | int,
        embedding_vector: list[float] | np.ndarray | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Update an existing embedding's vector or metadata.
        """
        if not self.collection:
            self.initialize_database()

        str_id = str(embedding_id)
        update_data: dict[str, Any] = {"ids": [str_id]}

        if embedding_vector is not None:
            if isinstance(embedding_vector, np.ndarray):
                embedding_vector = embedding_vector.tolist()
            update_data["embeddings"] = [embedding_vector]

        if metadata is not None:
            update_data["metadatas"] = [metadata]

        self.collection.update(**update_data)  # type: ignore

    def delete_embedding(self, embedding_id: str | int) -> None:
        """
        Delete an embedding by its ID.
        """
        if not self.collection:
            self.initialize_database()

        str_id = str(embedding_id)
        self.collection.delete(ids=[str_id])  # type: ignore

    def get_collection_info(self) -> dict[str, Any]:
        """
        Get information about the collection.
        """
        if not self.collection:
            self.initialize_database()

        count = self.collection.count()  # type: ignore

        return {
            "name": self.collection_name,
            "count": count,
            "persist_directory": self.persist_directory,
        }

    def list_all_ids(self) -> list[str]:
        """
        Get all embedding IDs in the collection.
        """
        if not self.collection:
            self.initialize_database()

        results = self.collection.get(include=[])  # type: ignore
        return results["ids"]

    def clear_collection(self) -> None:
        """
        Delete all embeddings from the collection.
        """
        if not self.collection:
            self.initialize_database()

        all_ids = self.list_all_ids()
        if all_ids:
            self.collection.delete(ids=all_ids)  # type: ignore
            logger.info("Cleared %d embeddings from collection '%s'", len(all_ids), self.collection_name)
        else:
            logger.info("Collection is already empty")
