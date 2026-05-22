# Database setup and models for Restaurant Inventory Forecasting System
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = "sqlite:///./restaurant_inventory.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Food Items table - stores information about each food item
class FoodItem(Base):
    __tablename__ = "food_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=True)
    unit = Column(String(20), default="units")  # kg, units, liters, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_records = relationship("InventoryRecord", back_populates="food_item")
    consumption_history = relationship("ConsumptionHistory", back_populates="food_item")

# Inventory Records table - stores current stock levels and restocking info
class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    
    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    current_stock = Column(Float, nullable=False, default=0)
    minimum_stock = Column(Float, nullable=False, default=10)
    maximum_stock = Column(Float, nullable=False, default=100)
    reorder_point = Column(Float, nullable=False, default=20)
    supplier = Column(String(100), nullable=True)
    unit_cost = Column(Float, nullable=True)
    last_restocked = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    food_item = relationship("FoodItem", back_populates="inventory_records")

# Consumption History table - stores daily consumption data
class ConsumptionHistory(Base):
    __tablename__ = "consumption_history"
    
    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    consumption = Column(Float, nullable=False, default=0)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    month = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, default=False)
    weather = Column(String(20), nullable=True)  # sunny, rainy, cloudy
    special_event = Column(Boolean, default=False)
    temperature = Column(Float, nullable=True)
    predicted_consumption = Column(Float, nullable=True)  # For comparison with actual
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    food_item = relationship("FoodItem", back_populates="consumption_history")

# Forecast Results table - stores prediction results
class ForecastResult(Base):
    __tablename__ = "forecast_results"
    
    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    prediction_date = Column(DateTime, nullable=False)  # When the prediction was made
    predicted_consumption = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    accuracy_score = Column(Float, nullable=True)  # If actual consumption is available later
    created_at = Column(DateTime, default=datetime.utcnow)

# Restock Recommendations table - stores ordering recommendations
class RestockRecommendation(Base):
    __tablename__ = "restock_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    recommendation_date = Column(DateTime, default=datetime.utcnow)
    current_stock = Column(Float, nullable=False)
    predicted_consumption = Column(Float, nullable=False)
    recommended_order_quantity = Column(Float, nullable=False)
    priority_level = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="pending")  # pending, ordered, received, cancelled
    supplier_recommended = Column(String(100), nullable=True)
    estimated_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_database():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_sample_food_items():
    """Initialize database with sample food items"""
    db = SessionLocal()
    try:
        # Check if food items already exist
        existing_items = db.query(FoodItem).count()
        if existing_items > 0:
            print(f"Database already has {existing_items} food items.")
            return
        
        # Sample food items with categories
        food_items_data = [
            {"name": "Chicken Breast", "category": "Meat", "unit": "kg"},
            {"name": "Beef Steak", "category": "Meat", "unit": "kg"},
            {"name": "Salmon", "category": "Fish", "unit": "kg"},
            {"name": "Pasta", "category": "Carbs", "unit": "kg"},
            {"name": "Rice", "category": "Carbs", "unit": "kg"},
            {"name": "Tomatoes", "category": "Vegetables", "unit": "kg"},
            {"name": "Onions", "category": "Vegetables", "unit": "kg"},
            {"name": "Lettuce", "category": "Vegetables", "unit": "kg"},
            {"name": "Cheese", "category": "Dairy", "unit": "kg"},
            {"name": "Bread", "category": "Bakery", "unit": "units"},
            {"name": "Potatoes", "category": "Vegetables", "unit": "kg"},
            {"name": "Carrots", "category": "Vegetables", "unit": "kg"},
            {"name": "Bell Peppers", "category": "Vegetables", "unit": "kg"},
            {"name": "Mushrooms", "category": "Vegetables", "unit": "kg"},
            {"name": "Garlic", "category": "Spices", "unit": "kg"},
        ]
        
        # Create food items
        for item_data in food_items_data:
            food_item = FoodItem(**item_data)
            db.add(food_item)
        
        db.commit()
        print(f"✅ Added {len(food_items_data)} food items to database")
        
        # Initialize inventory records with sample data
        food_items = db.query(FoodItem).all()
        for item in food_items:
            inventory_record = InventoryRecord(
                food_item_id=item.id,
                current_stock=50.0,
                minimum_stock=10.0,
                maximum_stock=200.0,
                reorder_point=25.0,
                unit_cost=5.0 + (item.id * 0.5)  # Sample pricing
            )
            db.add(inventory_record)
        
        db.commit()
        print(f"✅ Added inventory records for {len(food_items)} items")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create database and initialize with sample data
    create_database()
    init_sample_food_items()