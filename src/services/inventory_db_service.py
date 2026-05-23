"""
SQLAlchemy models and database setup for the Restaurant Inventory Forecasting System.
Ported and refactored from mayda-ai/inventory/database.py.
"""

import logging
import os
from collections.abc import Generator
from datetime import UTC, datetime

from alembic.config import Config
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
)
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from alembic import command
from src.core.config import settings

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()


def run_migrations() -> None:
    """Apply pending Alembic migrations to the inventory database."""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.INVENTORY_DATABASE_URL)

    engine = create_engine(settings.INVENTORY_DATABASE_URL)
    inspector = inspect(engine)

    if inspector.has_table("alembic_version"):
        with engine.connect() as conn:
            existing = conn.execute(sa_text("SELECT version_num FROM alembic_version")).scalar()
    else:
        existing = None

    if existing is None and inspector.has_table("food_items"):
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(alembic_cfg)
        command.stamp(alembic_cfg, script.get_current_head())
        logger.info("Stamped existing database at head migration.")
        return

    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully.")


# ── ORM Models ──


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=True)
    unit = Column(String(20), default="units")  # kg, units, liters, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    inventory_records = relationship("InventoryRecord", back_populates="food_item", cascade="all, delete-orphan")
    consumption_history = relationship("ConsumptionHistory", back_populates="food_item", cascade="all, delete-orphan")


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    current_stock = Column(Float, nullable=False, default=0.0)
    minimum_stock = Column(Float, nullable=False, default=10.0)
    maximum_stock = Column(Float, nullable=False, default=100.0)
    reorder_point = Column(Float, nullable=False, default=20.0)
    supplier = Column(String(100), nullable=True)
    unit_cost = Column(Float, nullable=True)
    last_restocked = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    notes = Column(Text, nullable=True)

    # Relationships
    food_item = relationship("FoodItem", back_populates="inventory_records")


class ConsumptionHistory(Base):
    __tablename__ = "consumption_history"

    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    consumption = Column(Float, nullable=False, default=0.0)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    month = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, default=False)
    weather = Column(String(20), nullable=True)  # sunny, rainy, cloudy
    special_event = Column(Boolean, default=False)
    temperature = Column(Float, nullable=True)
    predicted_consumption = Column(Float, nullable=True)  # For comparison
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    food_item = relationship("FoodItem", back_populates="consumption_history")


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    prediction_date = Column(DateTime, nullable=False)  # When prediction was made
    predicted_consumption = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    accuracy_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class RestockRecommendation(Base):
    __tablename__ = "restock_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    recommendation_date = Column(DateTime, default=lambda: datetime.now(UTC))
    current_stock = Column(Float, nullable=False)
    predicted_consumption = Column(Float, nullable=False)
    recommended_order_quantity = Column(Float, nullable=False)
    priority_level = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="pending")  # pending, ordered, received, cancelled
    supplier_recommended = Column(String(100), nullable=True)
    estimated_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


# ── Database Initialization & Connections ──

# Engine and Session Factory
engine = create_engine(
    settings.INVENTORY_DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.INVENTORY_DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_inventory_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and closes it on exit.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_inventory_db(db: Session) -> None:
    """
    Creates tables if they do not exist and populates the initial sample items.
    """
    # Ensure data directory exists if SQLite is used
    if settings.INVENTORY_DATABASE_URL.startswith("sqlite:///./"):
        db_path = settings.INVENTORY_DATABASE_URL.replace("sqlite:///./", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            logger.info("Creating directory: %s", db_dir)
            os.makedirs(db_dir, exist_ok=True)

    # Apply schema migrations
    run_migrations()

    # Seeding standard food items and baseline inventory metrics if empty
    existing_items = db.query(FoodItem).count()
    if existing_items > 0:
        logger.info("Food items already initialized in database (%d items).", existing_items)
        return

    logger.info("Pre-populating standard food items...")
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

    for item_data in food_items_data:
        food_item = FoodItem(**item_data)
        db.add(food_item)
    db.commit()

    logger.info("Pre-populating default inventory configurations...")
    food_items = db.query(FoodItem).all()
    for item in food_items:
        inventory_record = InventoryRecord(
            food_item_id=item.id,
            current_stock=50.0,
            minimum_stock=10.0,
            maximum_stock=200.0,
            reorder_point=25.0,
            unit_cost=5.0 + (item.id * 0.5),
            supplier="Standard Wholesale Food Group",
        )
        db.add(inventory_record)
    db.commit()
    logger.info("Database successfully seeded with standard items.")
