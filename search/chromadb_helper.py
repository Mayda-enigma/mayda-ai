"""
ChromaDB helper for the search-llm project.
This module provides easy access to vector embeddings storage and retrieval using ChromaDB.
"""

import chromadb
import numpy as np
from typing import List, Dict, Any, Optional, Union
import os


class ChromaEmbeddingsDatabase:
    """
    ChromaDB interface for vector embeddings storage and retrieval.
    Creates a collection called 'embeddings' to store vectors with IDs and metadata.
    """
    
    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "embeddings"):
        """
        Initialize ChromaDB client and collection
        
        Args:
            persist_directory: Directory to persist the database. If None, uses './chroma_db'
            collection_name: Name of the collection to store embeddings (default: 'embeddings')
        """
        self.persist_directory = persist_directory or os.path.join(os.getcwd(), 'chroma_db')
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    def initialize_database(self):
        """Initialize ChromaDB client and create/get the embeddings collection"""
        # Create persistent client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Create or get collection
        # ChromaDB collections are like tables - they store embeddings with IDs and metadata
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Vector embeddings storage for search-llm project"}
        )
        
        print(f"ChromaDB initialized at: {self.persist_directory}")
        print(f"Collection '{self.collection_name}' ready")
        
    def add_embedding(self, 
                     embedding_id: Union[str, int], 
                     embedding_vector: Union[List[float], np.ndarray],
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Add a single embedding to the database
        
        Args:
            embedding_id: Unique identifier for the embedding (will be converted to string)
            embedding_vector: The embedding vector (list of floats or numpy array)
            metadata: Optional metadata dictionary to store with the embedding
        """
        if not self.collection:
            self.initialize_database()
            
        # Convert numpy array to list if needed
        if isinstance(embedding_vector, np.ndarray):
            embedding_vector = embedding_vector.tolist()
            
        # ChromaDB requires string IDs
        str_id = str(embedding_id)
        
        # Add to collection
        self.collection.add(
            ids=[str_id],
            embeddings=[embedding_vector],
            metadatas=[metadata] if metadata else None
        )
        
    def add_embeddings_batch(self, 
                           embedding_ids: List[Union[str, int]], 
                           embedding_vectors: Union[List[List[float]], List[np.ndarray]],
                           metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Add multiple embeddings to the database in batch
        
        Args:
            embedding_ids: List of unique identifiers for embeddings
            embedding_vectors: List of embedding vectors
            metadatas: Optional list of metadata dictionaries
        """
        if not self.collection:
            self.initialize_database()
            
        # Convert all IDs to strings
        str_ids = [str(id_) for id_ in embedding_ids]
        
        # Convert numpy arrays to lists if needed
        processed_vectors = []
        for vector in embedding_vectors:
            if isinstance(vector, np.ndarray):
                processed_vectors.append(vector.tolist())
            else:
                processed_vectors.append(vector)
        
        # Add to collection
        self.collection.add(
            ids=str_ids,
            embeddings=processed_vectors,
            metadatas=metadatas
        )
        
    def get_embedding_by_id(self, embedding_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Retrieve an embedding by its ID
        
        Args:
            embedding_id: The ID to search for
            
        Returns:
            Dictionary containing id, embedding, and metadata, or None if not found
        """
        if not self.collection:
            self.initialize_database()
            
        str_id = str(embedding_id)
        
        try:
            results = self.collection.get(ids=[str_id], include=['embeddings', 'metadatas'])
            
            if results['ids'] and len(results['ids']) > 0:
                # Handle embeddings - ChromaDB returns numpy arrays
                embedding = None
                if 'embeddings' in results and results['embeddings'] is not None and len(results['embeddings']) > 0:
                    embedding = results['embeddings'][0].tolist() if hasattr(results['embeddings'][0], 'tolist') else results['embeddings'][0]
                
                # Handle metadata
                metadata = None
                if 'metadatas' in results and results['metadatas'] is not None and len(results['metadatas']) > 0:
                    metadata = results['metadatas'][0]
                
                return {
                    'id': results['ids'][0],
                    'embedding': embedding,
                    'metadata': metadata
                }
            return None
            
        except Exception as e:
            print(f"Error retrieving embedding {str_id}: {e}")
            return None
    
    def search_similar(self, 
                      query_vector: Union[List[float], np.ndarray], 
                      n_results: int = 10,
                      where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for similar embeddings using cosine similarity
        
        Args:
            query_vector: The query embedding vector
            n_results: Number of similar results to return (default: 10)
            where: Optional metadata filter conditions
            
        Returns:
            Dictionary containing ids, distances, and metadatas of similar embeddings
        """
        if not self.collection:
            self.initialize_database()
            
        # Convert numpy array to list if needed
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
            
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where,
            include=['distances', 'metadatas']
        )
        
        return {
            'ids': results['ids'][0] if results['ids'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
    
    def update_embedding(self, 
                        embedding_id: Union[str, int], 
                        embedding_vector: Union[List[float], np.ndarray] = None,
                        metadata: Dict[str, Any] = None):
        """
        Update an existing embedding's vector or metadata
        
        Args:
            embedding_id: The ID of the embedding to update
            embedding_vector: New embedding vector (optional)
            metadata: New metadata (optional)
        """
        if not self.collection:
            self.initialize_database()
            
        str_id = str(embedding_id)
        
        # Prepare update data
        update_data = {"ids": [str_id]}
        
        if embedding_vector is not None:
            if isinstance(embedding_vector, np.ndarray):
                embedding_vector = embedding_vector.tolist()
            update_data["embeddings"] = [embedding_vector]
            
        if metadata is not None:
            update_data["metadatas"] = [metadata]
            
        self.collection.update(**update_data)
    
    def delete_embedding(self, embedding_id: Union[str, int]):
        """
        Delete an embedding by its ID
        
        Args:
            embedding_id: The ID of the embedding to delete
        """
        if not self.collection:
            self.initialize_database()
            
        str_id = str(embedding_id)
        self.collection.delete(ids=[str_id])
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection
        
        Returns:
            Dictionary containing collection statistics and metadata
        """
        if not self.collection:
            self.initialize_database()
            
        count = self.collection.count()
        
        return {
            'name': self.collection_name,
            'count': count,
            'persist_directory': self.persist_directory
        }
    
    def list_all_ids(self) -> List[str]:
        """
        Get all embedding IDs in the collection
        
        Returns:
            List of all IDs in the collection
        """
        if not self.collection:
            self.initialize_database()
            
        results = self.collection.get(include=[])  # Only get IDs
        return results['ids']
    
    def clear_collection(self):
        """
        Delete all embeddings from the collection
        Warning: This operation cannot be undone!
        """
        if not self.collection:
            self.initialize_database()
            
        # Get all IDs and delete them
        all_ids = self.list_all_ids()
        if all_ids:
            self.collection.delete(ids=all_ids)
            print(f"Cleared {len(all_ids)} embeddings from collection '{self.collection_name}'")
        else:
            print("Collection is already empty")


def create_embeddings_database(persist_directory: Optional[str] = None) -> ChromaEmbeddingsDatabase:
    """
    Convenience function to create and initialize a ChromaDB embeddings database
    
    Args:
        persist_directory: Directory to persist the database
        
    Returns:
        Initialized ChromaEmbeddingsDatabase instance
    """
    db = ChromaEmbeddingsDatabase(persist_directory=persist_directory)
    db.initialize_database()
    return db


# Example usage and testing
if __name__ == "__main__":
    # Create database
    db = create_embeddings_database()
    
    # Example embedding (384 dimensions for all-MiniLM-L6-v2 model)
    example_embedding = np.random.rand(384).tolist()
    
    # Add an embedding
    db.add_embedding(
        embedding_id=1,
        embedding_vector=example_embedding,
        metadata={"dish_name": "Chicken Curry", "category": "Main Course", "price": 12.99}
    )
    
    # Retrieve the embedding
    result = db.get_embedding_by_id(1)
    print("Retrieved embedding:", result)
    
    # Get collection info
    info = db.get_collection_info()
    print("Collection info:", info)
    
    # Search for similar embeddings
    similar = db.search_similar(example_embedding, n_results=5)
    print("Similar embeddings:", similar)