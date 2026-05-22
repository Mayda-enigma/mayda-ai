"""
Embedding generator for dish objects using all-MiniLM-L6-v2 model.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

class EmbedGenerator:
    def __init__(self):
        """Initialize the embedding generator with the sentence transformer model."""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, dish) -> np.ndarray:
        """
        Generate embedding for a dish object.
        
        Args:
            dish: An object with the following properties:
                - name: str
                - ingredients: str or list
                - price: float or str
                - popularity: float or str
                - menucategory: str
                - menu: str
                - restaurant_name: str
                - restaurant_description: str
        
        Returns:
            np.ndarray: The embedding vector for the dish
        """
        # Convert ingredients to string if it's a list
        ingredients_str = dish.ingredients
        if isinstance(dish.ingredients, list):
            ingredients_str = ', '.join(dish.ingredients)
        
        # Create a comprehensive text representation of the dish
        dish_text = f"""
        Name: {dish.name}
        Ingredients: {ingredients_str}
        Price: {dish.price}
        Popularity: {dish.popularity}
        Menu Category: {dish.menucategory}
        Menu: {dish.menu}
        Restaurant: {dish.restaurant_name}
        Restaurant Description: {dish.restaurant_description}
        """.strip()
        
        # Generate and return the embedding
        embedding = self.model.encode(dish_text, convert_to_numpy=True)
        return embedding