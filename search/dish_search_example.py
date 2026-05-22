"""
Example script showing how to use the ChromaDB embedding system.
This script demonstrates both populating the database and searching for dishes.
"""

import os
from typing import List
from chromadb_setup import DishEmbeddingsDB
from generate_embeddings import EmbedGenerator
from populate_embeddings import EmbeddingPipeline
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Search result with dish information."""
    dish_id: int
    name: str
    description: str
    price: float
    category: str
    restaurant: str
    distance: float

class DishSearchEngine:
    """
    Main search engine for finding similar dishes using embeddings.
    """
    
    def __init__(self, chromadb_path: str = "./chromadb"):
        """
        Initialize the search engine.
        
        Args:
            chromadb_path: Path to ChromaDB storage
        """
        self.chromadb_path = chromadb_path
        self.chromadb = DishEmbeddingsDB(chromadb_path)
        self.embed_generator = EmbedGenerator()
        self.chromadb.initialize()
    
    def search_by_text(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search for dishes based on text description.
        
        Args:
            query: Text description of what you're looking for
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        # Create a dummy dish object for embedding generation
        from dataclasses import dataclass
        
        @dataclass
        class QueryDish:
            name: str = query
            description: str = query
            price: float = 0
            popularity: float = 0
            ingredients: List[str] = None
            menucategory: str = ""
            menu: str = ""
            restaurant_name: str = ""
            restaurant_description: str = ""
            
            def __post_init__(self):
                if self.ingredients is None:
                    self.ingredients = []
        
        query_dish = QueryDish()
        query_embedding = self.embed_generator.generate_embedding(query_dish)
        
        # Search in ChromaDB
        results = self.chromadb.search_similar(query_embedding, top_k=top_k)
        
        # Format results
        search_results = []
        for result in results:
            metadata = result['metadata']
            search_result = SearchResult(
                dish_id=result['dish_id'],
                name=metadata.get('name', 'Unknown'),
                description=metadata.get('description', 'No description'),
                price=metadata.get('price', 0.0),
                category=metadata.get('category', 'Unknown'),
                restaurant=metadata.get('restaurant', 'Unknown'),
                distance=result['distance']
            )
            search_results.append(search_result)
        
        return search_results
    
    def search_similar_to_dish(self, dish_id: int, top_k: int = 10) -> List[SearchResult]:
        """
        Find dishes similar to a specific dish.
        
        Args:
            dish_id: ID of the reference dish
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        # Get the embedding for the reference dish
        reference_embedding = self.chromadb.get_embedding(dish_id)
        if reference_embedding is None:
            return []
        
        # Search for similar dishes
        results = self.chromadb.search_similar(reference_embedding, top_k=top_k + 1)
        
        # Remove the reference dish from results and format
        search_results = []
        for result in results:
            if result['dish_id'] != dish_id:  # Skip the reference dish
                metadata = result['metadata']
                search_result = SearchResult(
                    dish_id=result['dish_id'],
                    name=metadata.get('name', 'Unknown'),
                    description=metadata.get('description', 'No description'),
                    price=metadata.get('price', 0.0),
                    category=metadata.get('category', 'Unknown'),
                    restaurant=metadata.get('restaurant', 'Unknown'),
                    distance=result['distance']
                )
                search_results.append(search_result)
        
        return search_results[:top_k]
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        return self.chromadb.get_collection_stats()

def demonstrate_usage():
    """Demonstrate how to use the search engine."""
    print("ChromaDB Dish Search Engine Demo")
    print("=" * 40)
    
    # Initialize search engine
    search_engine = DishSearchEngine()
    
    # Check if we have any data
    stats = search_engine.get_collection_info()
    print(f"Collection stats: {stats}")
    
    if stats['total_embeddings'] == 0:
        print("\n⚠️ No embeddings found in database!")
        print("Please run the population script first:")
        print("python populate_embeddings.py --reset")
        return
    
    print(f"\n✓ Found {stats['total_embeddings']} dish embeddings in database")
    
    # Example searches
    search_queries = [
        "Italian pizza with cheese",
        "spicy Indian curry",
        "healthy salad",
        "American burger"
    ]
    
    print("\n🔍 Example text searches:")
    print("-" * 30)
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = search_engine.search_by_text(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.name} - {result.category}")
                print(f"     ${result.price:.2f} at {result.restaurant}")
                print(f"     Distance: {result.distance:.4f}")
        else:
            print("  No results found")
    
    print(f"\n🎯 Example similarity searches:")
    print("-" * 30)
    print("Finding dishes similar to the first dish in database...")
    
    # Find similar dishes to the first dish
    similar_results = search_engine.search_similar_to_dish(1, top_k=3)
    if similar_results:
        for i, result in enumerate(similar_results, 1):
            print(f"  {i}. {result.name} - {result.category}")
            print(f"     ${result.price:.2f} at {result.restaurant}")
            print(f"     Distance: {result.distance:.4f}")
    else:
        print("  No similar dishes found")

def main():
    """Main function with options."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Dish Search Example")
    parser.add_argument("--populate", action="store_true", help="Populate database first")
    parser.add_argument("--database-url", help="PostgreSQL database URL")
    parser.add_argument("--search", help="Search for dishes with this text")
    parser.add_argument("--similar", type=int, help="Find dishes similar to this dish ID")
    
    args = parser.parse_args()
    
    # Populate database if requested
    if args.populate:
        print("Populating ChromaDB with dish embeddings...")
        pipeline = EmbeddingPipeline(database_url=args.database_url)
        pipeline.run_full_pipeline(reset_chromadb=True)
        print("Database populated successfully!\n")
    
    # Perform search if requested
    if args.search:
        search_engine = DishSearchEngine()
        results = search_engine.search_by_text(args.search, top_k=5)
        
        print(f"Search results for: '{args.search}'")
        print("-" * 40)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name}")
            print(f"   Category: {result.category}")
            print(f"   Price: ${result.price:.2f}")
            print(f"   Restaurant: {result.restaurant}")
            print(f"   Similarity: {1 - result.distance:.3f}")
            print()
        
        return
    
    # Find similar dishes if requested
    if args.similar:
        search_engine = DishSearchEngine()
        results = search_engine.search_similar_to_dish(args.similar, top_k=5)
        
        print(f"Dishes similar to dish ID {args.similar}:")
        print("-" * 40)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name}")
            print(f"   Category: {result.category}")
            print(f"   Price: ${result.price:.2f}")
            print(f"   Restaurant: {result.restaurant}")
            print(f"   Similarity: {1 - result.distance:.3f}")
            print()
        
        return
    
    # Run demonstration
    demonstrate_usage()

if __name__ == "__main__":
    main()