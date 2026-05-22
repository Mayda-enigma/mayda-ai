"""
Restaurant Inventory Forecasting Engine using Random Forest regression.
Refactored from mayda-ai/inventory/forecaster_db.py.
"""
from datetime import datetime, timedelta, timezone
import logging
import os
from typing import Dict, List, Optional, Tuple, Union, Any
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

# Narrow warnings filter to specific categories as per IN-008
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from src.services.inventory_db_service import (
    FoodItem,
    InventoryRecord,
    ConsumptionHistory,
    ForecastResult,
    RestockRecommendation,
)

logger = logging.getLogger(__name__)


class DatabaseIntegratedForecaster:
    """
    State-free database-integrated forecaster.
    Trained models and scalers are loaded in-memory.
    All database transactions accept db: Session.
    """

    def __init__(self) -> None:
        self.models: Dict[str, RandomForestRegressor] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.food_items: Dict[str, int] = {}  # Caches food name -> food ID mappings

    def _ensure_food_items_loaded(self, db: Session) -> None:
        """Ensures food items are loaded into cash from database."""
        if not self.food_items:
            items = db.query(FoodItem).all()
            for item in items:
                self.food_items[item.name] = item.id
            logger.info("Loaded %d food items from database.", len(self.food_items))

    def save_models(self, path: str) -> None:
        """
        Serialize in-memory models and scalers to a single joblib file.
        """
        import joblib

        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"models": self.models, "scalers": self.scalers}, path)
        logger.info("Forecaster models saved successfully to: %s", path)

    def load_models(self, path: str) -> bool:
        """
        Load serialized models and scalers from a joblib file.
        """
        import joblib

        if not os.path.exists(path):
            logger.warning("No model file found at path: %s", path)
            return False
        try:
            data = joblib.load(path)
            self.models = data.get("models", {})
            self.scalers = data.get("scalers", {})
            logger.info("Successfully loaded forecaster models for %d items from %s", len(self.models), path)
            return True
        except Exception as exc:
            logger.error("Error loading models from %s: %s", path, exc)
            return False

    def save_sample_data_to_db(self, df: pd.DataFrame, db: Session) -> None:
        """Save generated sample data to database."""
        self._ensure_food_items_loaded(db)
        logger.info("Saving generated consumption history to database...")

        saved_records = 0
        for _, row in df.iterrows():
            food_item_id = self.food_items.get(row["food_item"])
            if food_item_id is None:
                continue

            # Check if record already exists for this food_item and date
            existing = (
                db.query(ConsumptionHistory)
                .filter(
                    ConsumptionHistory.food_item_id == food_item_id,
                    ConsumptionHistory.date == row["date"],
                )
                .first()
            )

            if existing:
                continue

            consumption_record = ConsumptionHistory(
                food_item_id=food_item_id,
                date=row["date"],
                consumption=float(row["consumption"]),
                day_of_week=int(row["day_of_week"]),
                month=int(row["month"]),
                is_weekend=bool(row["is_weekend"]),
                weather=row["weather"],
                special_event=bool(row["special_event"]),
            )

            db.add(consumption_record)
            saved_records += 1

            if saved_records % 100 == 0:
                db.commit()

        db.commit()
        logger.info("Saved %d consumption records to database.", saved_records)

    def update_inventory_from_history(self, db: Session) -> None:
        """Update current inventory levels based on recent consumption history."""
        self._ensure_food_items_loaded(db)
        logger.info("Updating inventory levels based on consumption history...")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        recent_consumption = (
            db.query(ConsumptionHistory, FoodItem.name)
            .join(FoodItem, ConsumptionHistory.food_item_id == FoodItem.id)
            .filter(ConsumptionHistory.date >= start_date)
            .all()
        )

        # Calculate total consumption per item
        consumption_totals: Dict[str, float] = {}
        for record, food_name in recent_consumption:
            if food_name not in consumption_totals:
                consumption_totals[food_name] = 0.0
            consumption_totals[food_name] += record.consumption

        # Update inventory records
        updated_items = 0
        for food_name, total_consumed in consumption_totals.items():
            food_item_id = self.food_items.get(food_name)
            if food_item_id:
                inventory_record = (
                    db.query(InventoryRecord)
                    .filter(InventoryRecord.food_item_id == food_item_id)
                    .first()
                )

                if inventory_record:
                    estimated_current_stock = max(
                        10.0, inventory_record.maximum_stock - total_consumed
                    )
                    inventory_record.current_stock = float(estimated_current_stock)
                    inventory_record.last_updated = datetime.now(timezone.utc)
                    updated_items += 1

        db.commit()
        logger.info("Updated inventory levels for %d items based on recent consumption", updated_items)

    def load_historical_data_from_db(self, db: Session, days_back: int = 365) -> pd.DataFrame:
        """Load historical consumption data from database."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        records = (
            db.query(ConsumptionHistory, FoodItem.name)
            .join(FoodItem, ConsumptionHistory.food_item_id == FoodItem.id)
            .filter(ConsumptionHistory.date >= start_date)
            .order_by(ConsumptionHistory.date)
            .all()
        )

        data = []
        for record, food_name in records:
            data.append(
                {
                    "date": record.date,
                    "food_item": food_name,
                    "food_item_id": record.food_item_id,
                    "consumption": record.consumption,
                    "day_of_week": record.day_of_week,
                    "month": record.month,
                    "is_weekend": record.is_weekend,
                    "weather": record.weather or "sunny",
                    "special_event": record.special_event,
                }
            )

        df = pd.DataFrame(data)
        logger.info("Loaded %d historical records from database.", len(df))
        return df

    def update_inventory_after_consumption(
        self, food_item_name: str, consumption: float, db: Session
    ) -> None:
        """Update inventory levels after recording consumption."""
        self._ensure_food_items_loaded(db)
        food_item_id = self.food_items.get(food_item_name)
        if not food_item_id:
            return

        inventory_record = (
            db.query(InventoryRecord)
            .filter(InventoryRecord.food_item_id == food_item_id)
            .first()
        )

        if inventory_record:
            inventory_record.current_stock = max(0.0, inventory_record.current_stock - consumption)
            inventory_record.last_updated = datetime.now(timezone.utc)
            db.commit()

    def add_consumption_record(
        self,
        food_item: str,
        date: datetime,
        consumption: float,
        db: Session,
        weather: str = "sunny",
        special_event: bool = False,
        notes: Optional[str] = None,
    ) -> bool:
        """Add a single consumption record to the database."""
        self._ensure_food_items_loaded(db)
        food_item_id = self.food_items.get(food_item)
        if not food_item_id:
            raise ValueError(f"Food item '{food_item}' not found in database")

        # Strip hours for daily record match
        query_date = date.date()

        # Check if record already exists for this date (timezone-safe date match)
        existing = (
            db.query(ConsumptionHistory)
            .filter(
                ConsumptionHistory.food_item_id == food_item_id,
                # Simple date range match for exact day
                ConsumptionHistory.date >= datetime.combine(query_date, datetime.min.time()),
                ConsumptionHistory.date <= datetime.combine(query_date, datetime.max.time()),
            )
            .first()
        )

        if existing:
            logger.info("Consumption record for %s on %s already exists. Updating...", food_item, query_date)
            existing.consumption = float(consumption)
            existing.weather = weather
            existing.special_event = special_event
            if notes:
                existing.notes = notes
        else:
            # Create new consumption record
            consumption_record = ConsumptionHistory(
                food_item_id=food_item_id,
                date=date,
                consumption=float(consumption),
                day_of_week=date.weekday(),
                month=date.month,
                is_weekend=date.weekday() >= 5,
                weather=weather,
                special_event=special_event,
                notes=notes,
            )
            db.add(consumption_record)

        # Update inventory levels
        self.update_inventory_after_consumption(food_item, float(consumption), db)

        db.commit()
        return True

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning."""
        df = df.sort_values(["food_item", "date"])

        # Add rolling averages
        df["consumption_7day_avg"] = (
            df.groupby("food_item")["consumption"]
            .rolling(window=7, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )
        df["consumption_14day_avg"] = (
            df.groupby("food_item")["consumption"]
            .rolling(window=14, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )
        df["consumption_30day_avg"] = (
            df.groupby("food_item")["consumption"]
            .rolling(window=30, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )

        # Add lag features
        df["consumption_lag1"] = df.groupby("food_item")["consumption"].shift(1)
        df["consumption_lag7"] = df.groupby("food_item")["consumption"].shift(7)

        # Encode categorical variables
        df["weather_sunny"] = (df["weather"] == "sunny").astype(int)
        df["weather_rainy"] = (df["weather"] == "rainy").astype(int)

        # Fill NaN values
        df = df.bfill().fillna(0)

        return df

    def train_models(self, db: Session, use_database: bool = True) -> None:
        """Train forecasting models using data from database or generate sample data."""
        self._ensure_food_items_loaded(db)

        if use_database:
            df = self.load_historical_data_from_db(db)
            if df.empty:
                logger.info("No historical data found in database. Generating sample data...")
                df = self.generate_sample_data()
                self.save_sample_data_to_db(df, db)
        else:
            df = self.generate_sample_data()
            self.save_sample_data_to_db(df, db)

        # Store historical data for use in predictions
        self.historical_data = df.copy()

        df_prepared = self.prepare_features(df)

        feature_columns = [
            "day_of_week",
            "month",
            "is_weekend",
            "special_event",
            "weather_sunny",
            "weather_rainy",
            "consumption_7day_avg",
            "consumption_14day_avg",
            "consumption_30day_avg",
            "consumption_lag1",
            "consumption_lag7",
        ]

        food_items = df["food_item"].unique()

        trained_count = 0
        for item in food_items:
            item_data = df_prepared[df_prepared["food_item"] == item].copy()

            # Skip if not enough data
            if len(item_data) < 20:  # Relaxed minimum length for testing/bootstrap
                continue

            X = item_data[feature_columns].values
            y = item_data["consumption"].values

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train model
            model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            model.fit(X_scaled, y)

            # Store model and scaler
            self.models[item] = model
            self.scalers[item] = scaler
            trained_count += 1

        logger.info("Trained forecaster models for %d food items.", trained_count)

    def predict_consumption(
        self,
        food_item: str,
        date: datetime,
        db: Session,
        weather: str = "sunny",
        special_event: int = 0,
        skip_save: bool = False,
    ) -> Optional[float]:
        """Predict consumption for a specific item and date."""
        self._ensure_food_items_loaded(db)

        if food_item not in self.models:
            logger.warning("No trained model found for food item: %s", food_item)
            return None

        day_of_week = date.weekday()
        month = date.month
        is_weekend = int(day_of_week >= 5)
        weather_sunny = int(weather == "sunny")
        weather_rainy = int(weather == "rainy")

        # Get historical data for lag features and rolling averages
        if not hasattr(self, "historical_data") or self.historical_data is None:
            # Dynamically load from database if not loaded in-memory
            self.historical_data = self.load_historical_data_from_db(db)

        item_history = self.historical_data[self.historical_data["food_item"] == food_item].copy()

        if not item_history.empty:
            item_history = item_history.sort_values("date")
            recent_data = item_history.tail(30)

            consumption_7day_avg = (
                recent_data["consumption"].tail(7).mean()
                if len(recent_data) >= 7
                else recent_data["consumption"].mean()
            )
            consumption_14day_avg = (
                recent_data["consumption"].tail(14).mean()
                if len(recent_data) >= 14
                else recent_data["consumption"].mean()
            )
            consumption_30day_avg = recent_data["consumption"].mean()

            consumption_lag1 = (
                recent_data["consumption"].iloc[-1]
                if len(recent_data) >= 1
                else consumption_7day_avg
            )
            consumption_lag7 = (
                recent_data["consumption"].iloc[-7]
                if len(recent_data) >= 7
                else consumption_7day_avg
            )
        else:
            consumption_7day_avg = consumption_14day_avg = consumption_30day_avg = 20.0
            consumption_lag1 = consumption_lag7 = 20.0

        features = np.array(
            [
                [
                    day_of_week,
                    month,
                    is_weekend,
                    special_event,
                    weather_sunny,
                    weather_rainy,
                    consumption_7day_avg,
                    consumption_14day_avg,
                    consumption_30day_avg,
                    consumption_lag1,
                    consumption_lag7,
                ]
            ]
        )

        # Scale features
        features_scaled = self.scalers[food_item].transform(features)

        # Make prediction
        prediction = self.models[food_item].predict(features_scaled)[0]
        prediction_val = max(0.0, float(int(prediction)))

        # Save prediction result to DB
        if not skip_save:
            self.save_forecast_result(food_item, date, prediction_val, db)

        return prediction_val

    def save_forecast_result(
        self, food_item: str, forecast_date: datetime, predicted_consumption: float, db: Session
    ) -> None:
        """Save forecast result to database."""
        self._ensure_food_items_loaded(db)
        food_item_id = self.food_items.get(food_item)
        if not food_item_id:
            return

        forecast_result = ForecastResult(
            food_item_id=food_item_id,
            forecast_date=forecast_date,
            prediction_date=datetime.now(timezone.utc),
            predicted_consumption=predicted_consumption,
            model_version="RandomForest_v1.0",
        )

        db.add(forecast_result)
        db.commit()

    def generate_restock_recommendations(
        self, db: Session, days_ahead: int = 7, safety_margin: float = 0.2
    ) -> Dict[str, Any]:
        """Generate and save restock recommendations to database."""
        self._ensure_food_items_loaded(db)

        # Get current inventory levels
        inventory_records = (
            db.query(InventoryRecord, FoodItem.name)
            .join(FoodItem, InventoryRecord.food_item_id == FoodItem.id)
            .all()
        )

        recommendations = {}

        for record, food_name in inventory_records:
            if food_name not in self.models:
                continue

            # Predict consumption for next N days
            daily_predictions = []
            current_date = datetime.now(timezone.utc)
            total_predicted_consumption = 0.0

            for day in range(days_ahead):
                future_date = current_date + timedelta(days=day)
                predicted_consumption = self.predict_consumption(
                    food_name, future_date, db, weather="sunny", special_event=0, skip_save=True
                )

                if predicted_consumption is not None:
                    daily_predictions.append(
                        {
                            "date": future_date.strftime("%Y-%m-%d"),
                            "predicted_consumption": predicted_consumption,
                        }
                    )
                    total_predicted_consumption += predicted_consumption

            if daily_predictions:
                current_stock = record.current_stock
                stock_needed = total_predicted_consumption * (1 + safety_margin)
                restock_needed = max(0.0, stock_needed - current_stock)

                # Determine priority level
                stock_ratio = current_stock / record.reorder_point if record.reorder_point > 0 else 1.0
                if stock_ratio <= 0.5:
                    priority = "urgent"
                elif stock_ratio <= 0.8:
                    priority = "high"
                elif stock_ratio <= 1.0:
                    priority = "medium"
                else:
                    priority = "low"

                # Save recommendation to database
                if restock_needed > 0:
                    recommendation = RestockRecommendation(
                        food_item_id=record.food_item_id,
                        current_stock=current_stock,
                        predicted_consumption=total_predicted_consumption,
                        recommended_order_quantity=restock_needed,
                        priority_level=priority,
                        supplier_recommended=record.supplier,
                        estimated_cost=record.unit_cost * restock_needed if record.unit_cost else None,
                    )

                    # Check if recommendation already exists for today
                    existing = (
                        db.query(RestockRecommendation)
                        .filter(
                            RestockRecommendation.food_item_id == record.food_item_id,
                            RestockRecommendation.recommendation_date >= datetime.now(timezone.utc).date(),
                        )
                        .first()
                    )

                    if not existing:
                        db.add(recommendation)

                recommendations[food_name] = {
                    "current_stock": current_stock,
                    "predicted_consumption": total_predicted_consumption,
                    "stock_needed": int(stock_needed),
                    "restock_needed": int(restock_needed),
                    "priority_level": priority,
                    "daily_predictions": daily_predictions,
                    "status": "RESTOCK NEEDED" if restock_needed > 0 else "SUFFICIENT STOCK",
                }

        db.commit()
        return recommendations

    def generate_sample_data(self, days: int = 365) -> pd.DataFrame:
        """Generate realistic restaurant inventory data."""
        np.random.seed(42)

        # Fallback food items list if no DB items loaded yet
        food_items = list(self.food_items.keys())
        if not food_items:
            food_items = [
                "Chicken Breast",
                "Beef Steak",
                "Salmon",
                "Pasta",
                "Rice",
                "Tomatoes",
                "Onions",
                "Lettuce",
                "Cheese",
                "Bread",
                "Potatoes",
                "Carrots",
                "Bell Peppers",
                "Mushrooms",
                "Garlic",
            ]

        data = []
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        for i in range(days):
            date = start_date + timedelta(days=i)

            day_of_week = date.weekday()
            month = date.month

            weekend_mult = 1.3 if day_of_week >= 5 else 1.0

            if month in [12, 1, 2]:
                seasonal_mult = 0.8
            elif month in [6, 7, 8]:
                seasonal_mult = 1.2
            else:
                seasonal_mult = 1.0

            for item in food_items:
                base_consumption = {
                    "Chicken Breast": 25,
                    "Beef Steak": 15,
                    "Salmon": 12,
                    "Pasta": 30,
                    "Rice": 20,
                    "Tomatoes": 18,
                    "Onions": 15,
                    "Lettuce": 10,
                    "Cheese": 12,
                    "Bread": 35,
                    "Potatoes": 22,
                    "Carrots": 8,
                    "Bell Peppers": 10,
                    "Mushrooms": 7,
                    "Garlic": 3,
                }.get(item, 15)

                daily_consumption = max(
                    0,
                    int(
                        base_consumption
                        * weekend_mult
                        * seasonal_mult
                        * np.random.normal(1.0, 0.2)
                    ),
                )

                weather_effect = np.random.choice(
                    ["sunny", "rainy", "cloudy"], p=[0.6, 0.2, 0.2]
                )
                if weather_effect == "rainy":
                    daily_consumption = int(daily_consumption * 0.8)
                elif weather_effect == "sunny":
                    daily_consumption = int(daily_consumption * 1.1)

                special_event = np.random.choice([0, 1], p=[0.9, 0.1])
                if special_event:
                    daily_consumption = int(daily_consumption * 1.5)

                data.append(
                    {
                        "date": date,
                        "food_item": item,
                        "day_of_week": day_of_week,
                        "month": month,
                        "is_weekend": int(day_of_week >= 5),
                        "weather": weather_effect,
                        "special_event": special_event,
                        "consumption": daily_consumption,
                    }
                )

        return pd.DataFrame(data)
