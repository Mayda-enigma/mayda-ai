"""
Simplified database helper for the search-llm project.
This module provides easy access to the restaurant database for LLM queries.
Supports both SQLite and PostgreSQL databases.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

@dataclass
class Dish:
    """Represents a dish from the database"""
    id: int
    name: str
    description: str
    price: float
    category: str
    restaurant: str

class FoodSearchDatabase:
    """
    Simplified database interface for food search queries.
    Works with both SQLite and PostgreSQL databases.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            database_url: Database connection URL. Examples:
                         - SQLite: "sqlite:///search_llm.db" or None (defaults to search_llm.db)
                         - PostgreSQL: "postgresql://user:pass@localhost/dbname"
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.connection = None
        self.db_type = None
        
    def connect(self):
        """Establish database connection"""
        if self.database_url and 'postgresql' in self.database_url and POSTGRES_AVAILABLE:
            # PostgreSQL connection
            try:
                self.connection = psycopg2.connect(self.database_url)
                self.db_type = 'postgresql'
                return
            except Exception as e:
                print(f"PostgreSQL connection failed: {e}, falling back to SQLite")
        
        # SQLite connection (default/fallback)
        db_path = 'search_llm.db'
        if self.database_url and 'sqlite' in self.database_url:
            db_path = self.database_url.replace('sqlite:///', '')
        
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.db_type = 'sqlite'
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results"""
        if not self.connection:
            self.connect()
        
        if self.db_type == 'postgresql':
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        else:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def search_dishes(self, 
                     name_query: Optional[str] = None,
                     category: Optional[str] = None, 
                     restaurant: Optional[str] = None,
                     min_price: Optional[float] = None,
                     max_price: Optional[float] = None) -> List[int]:
        """
        Search for dishes based on various criteria.
        Returns list of dish IDs.
        """
        # Use ILIKE for PostgreSQL, LIKE for SQLite
        like_op = 'ILIKE' if self.db_type == 'postgresql' else 'LIKE'
        placeholder = '%s' if self.db_type == 'postgresql' else '?'
        
        conditions = ["d.\"isAvailable\" = true"]
        params = []
        
        if name_query:
            conditions.append(f"(d.name {like_op} {placeholder} OR d.description {like_op} {placeholder})")
            search_term = f'%{name_query}%'
            params.extend([search_term, search_term])
        
        if category:
            conditions.append(f"mc.name {like_op} {placeholder}")
            params.append(f'%{category}%')
        
        if restaurant:
            conditions.append(f"(r.name {like_op} {placeholder} OR r.description {like_op} {placeholder})")
            restaurant_term = f'%{restaurant}%'
            params.extend([restaurant_term, restaurant_term])
        
        if min_price is not None:
            conditions.append(f"d.price >= {placeholder}")
            params.append(min_price)
        
        if max_price is not None:
            conditions.append(f"d.price <= {placeholder}")
            params.append(max_price)
        
        query = f"""
            SELECT DISTINCT d.id, d.price
            FROM dishes d
            JOIN menu_categories mc ON d."categoryId" = mc.id
            JOIN menus m ON mc."menuId" = m.id
            JOIN restaurants r ON m."restaurantId" = r.id
            WHERE {' AND '.join(conditions)}
            ORDER BY d.price
        """
        
        results = self._execute_query(query, tuple(params))
        return [row['id'] for row in results]
    
    def get_dish_details(self, dish_ids: List[int]) -> List[Dish]:
        """Get detailed information for specific dish IDs"""
        if not dish_ids:
            return []
        
        placeholder = '%s' if self.db_type == 'postgresql' else '?'
        placeholders = ','.join([placeholder for _ in dish_ids])
        
        query = f"""
            SELECT 
                d.id, d.name, d.description, d.price,
                mc.name as category,
                r.name as restaurant
            FROM dishes d
            JOIN menu_categories mc ON d."categoryId" = mc.id
            JOIN menus m ON mc."menuId" = m.id
            JOIN restaurants r ON m."restaurantId" = r.id
            WHERE d.id IN ({placeholders})
            ORDER BY d.price
        """
        
        results = self._execute_query(query, tuple(dish_ids))
        dishes = []
        for row in results:
            dishes.append(Dish(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                price=row['price'],
                category=row['category'],
                restaurant=row['restaurant']
            ))
        
        return dishes
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Backwards compatibility - allow both class names
RestaurantDatabase = FoodSearchDatabase