"""
Embedding generator for dish objects using all-MiniLM-L6-v2 model.
Ported from mayda-ai/search/generate_embeddings.py.
"""

import logging
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbedGenerator:
    """
    Generates embeddings for dish configurations using a sentence-transformer model.
    """

    def __init__(self) -> None:
        """Initialize the embedding generator with the sentence transformer model."""
        logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2')...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer initialized.")

    def generate_embedding(self, dish: Any) -> np.ndarray:
        """
        Generate embedding for a dish object. Supports both object attribute
        access and dictionary indexing.
        """

        # Helper to get field from dish (dictionary or object)
        def get_field(name: str, default: Any = "") -> Any:
            if isinstance(dish, dict):
                return dish.get(name, default)
            return getattr(dish, name, default)

        name = get_field("name")
        ingredients = get_field("ingredients")
        price = get_field("price")
        popularity = get_field("popularity")
        menucategory = get_field("menucategory")
        menu = get_field("menu")
        restaurant_name = get_field("restaurant_name")
        restaurant_description = get_field("restaurant_description")

        # Convert ingredients to string if it's a list
        ingredients_str = ingredients
        if isinstance(ingredients, list):
            ingredients_str = ", ".join(ingredients)
        elif not isinstance(ingredients, str):
            ingredients_str = ""

        # Create a comprehensive text representation of the dish
        dish_text = f"""
Name: {name}
Ingredients: {ingredients_str}
Price: {price}
Popularity: {popularity}
Menu Category: {menucategory}
Menu: {menu}
Restaurant: {restaurant_name}
Restaurant Description: {restaurant_description}
""".strip()

        # Generate and return the embedding
        embedding = self.model.encode(dish_text, convert_to_numpy=True)
        return embedding
