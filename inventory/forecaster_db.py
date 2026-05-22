# Enhanced Restaurant Inventory Forecaster with Database Integration
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Import database models
from database import (
    SessionLocal, FoodItem, InventoryRecord, ConsumptionHistory, 
    ForecastResult, RestockRecommendation
)

class DatabaseIntegratedForecaster:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.db = SessionLocal()
        self.food_items = {}  # Will store food item ID mappings
        self._load_food_items()

    def _load_food_items(self):
        """Load food items from database"""
        items = self.db.query(FoodItem).all()
        for item in items:
            self.food_items[item.name] = item.id
        print(f"✅ Loaded {len(self.food_items)} food items from database")

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()

    def save_sample_data_to_db(self, df: pd.DataFrame):
        """Save generated sample data to database"""
        print("💾 Saving consumption history to database...")
        
        saved_records = 0
        for _, row in df.iterrows():
            food_item_id = self.food_items.get(row['food_item'])
            if food_item_id is None:
                continue
                
            # Check if record already exists
            existing = self.db.query(ConsumptionHistory).filter(
                ConsumptionHistory.food_item_id == food_item_id,
                ConsumptionHistory.date == row['date']
            ).first()
            
            if existing:
                continue  # Skip if already exists
            
            consumption_record = ConsumptionHistory(
                food_item_id=food_item_id,
                date=row['date'],
                consumption=row['consumption'],
                day_of_week=row['day_of_week'],
                month=row['month'],
                is_weekend=bool(row['is_weekend']),
                weather=row['weather'],
                special_event=bool(row['special_event'])
            )
            
            self.db.add(consumption_record)
            saved_records += 1
            
            if saved_records % 100 == 0:
                self.db.commit()  # Commit in batches
        
        self.db.commit()
        print(f"✅ Saved {saved_records} consumption records to database")

    def update_inventory_from_history(self):
        """Update current inventory levels based on recent consumption history"""
        print("🔄 Updating inventory levels based on consumption history...")
        
        # Get the last 7 days of consumption for each item
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        recent_consumption = self.db.query(ConsumptionHistory, FoodItem.name)\
                                   .join(FoodItem, ConsumptionHistory.food_item_id == FoodItem.id)\
                                   .filter(ConsumptionHistory.date >= start_date)\
                                   .all()
        
        # Calculate total consumption per item
        consumption_totals = {}
        for record, food_name in recent_consumption:
            if food_name not in consumption_totals:
                consumption_totals[food_name] = 0
            consumption_totals[food_name] += record.consumption
        
        # Update inventory records
        updated_items = 0
        for food_name, total_consumed in consumption_totals.items():
            food_item_id = self.food_items.get(food_name)
            if food_item_id:
                inventory_record = self.db.query(InventoryRecord)\
                                         .filter(InventoryRecord.food_item_id == food_item_id)\
                                         .first()
                
                if inventory_record:
                    # Simulate realistic current stock (starting stock minus recent consumption)
                    estimated_current_stock = max(10, inventory_record.maximum_stock - total_consumed)
                    inventory_record.current_stock = estimated_current_stock
                    inventory_record.last_updated = datetime.utcnow()
                    updated_items += 1
        
        self.db.commit()
        print(f"✅ Updated inventory levels for {updated_items} items based on recent consumption")

    def load_historical_data_from_db(self, days_back: int = 365) -> pd.DataFrame:
        """Load historical consumption data from database"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Query consumption history with food item names
        records = self.db.query(ConsumptionHistory, FoodItem.name)\
                         .join(FoodItem, ConsumptionHistory.food_item_id == FoodItem.id)\
                         .filter(ConsumptionHistory.date >= start_date)\
                         .order_by(ConsumptionHistory.date)\
                         .all()
        
        # Convert to DataFrame
        data = []
        for record, food_name in records:
            data.append({
                'date': record.date,
                'food_item': food_name,
                'food_item_id': record.food_item_id,
                'consumption': record.consumption,
                'day_of_week': record.day_of_week,
                'month': record.month,
                'is_weekend': record.is_weekend,
                'weather': record.weather or 'sunny',
                'special_event': record.special_event
            })
        
        df = pd.DataFrame(data)
        print(f"📊 Loaded {len(df)} historical records from database")
        return df

    def update_inventory_after_consumption(self, food_item_name: str, consumption: float):
        """Update inventory levels after recording consumption"""
        food_item_id = self.food_items.get(food_item_name)
        if not food_item_id:
            return
        
        inventory_record = self.db.query(InventoryRecord)\
                                 .filter(InventoryRecord.food_item_id == food_item_id)\
                                 .first()
        
        if inventory_record:
            inventory_record.current_stock = max(0, inventory_record.current_stock - consumption)
            inventory_record.last_updated = datetime.utcnow()
            self.db.commit()

    def add_consumption_record(self, food_item: str, date: datetime, consumption: float, 
                             weather: str = 'sunny', special_event: bool = False, notes: str = None):
        """Add a single consumption record to the database"""
        food_item_id = self.food_items.get(food_item)
        if not food_item_id:
            raise ValueError(f"Food item '{food_item}' not found in database")
        
        # Check if record already exists for this date
        existing = self.db.query(ConsumptionHistory).filter(
            ConsumptionHistory.food_item_id == food_item_id,
            ConsumptionHistory.date.cast(date.date()) == date.date()
        ).first()
        
        if existing:
            print(f"⚠️ Consumption record for {food_item} on {date.date()} already exists. Updating...")
            existing.consumption = consumption
            existing.weather = weather
            existing.special_event = special_event
            if notes:
                existing.notes = notes
        else:
            # Create new consumption record
            consumption_record = ConsumptionHistory(
                food_item_id=food_item_id,
                date=date,
                consumption=consumption,
                day_of_week=date.weekday(),
                month=date.month,
                is_weekend=date.weekday() >= 5,
                weather=weather,
                special_event=special_event,
                notes=notes
            )
            self.db.add(consumption_record)
        
        # Update inventory levels
        self.update_inventory_after_consumption(food_item, consumption)
        
        self.db.commit()
        return True

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning (same as original)"""
        df = df.sort_values(['food_item', 'date'])

        # Add rolling averages
        df['consumption_7day_avg'] = df.groupby('food_item')['consumption'].rolling(7).mean().values
        df['consumption_14day_avg'] = df.groupby('food_item')['consumption'].rolling(14).mean().values
        df['consumption_30day_avg'] = df.groupby('food_item')['consumption'].rolling(30).mean().values

        # Add lag features
        df['consumption_lag1'] = df.groupby('food_item')['consumption'].shift(1)
        df['consumption_lag7'] = df.groupby('food_item')['consumption'].shift(7)

        # Encode categorical variables
        df['weather_sunny'] = (df['weather'] == 'sunny').astype(int)
        df['weather_rainy'] = (df['weather'] == 'rainy').astype(int)

        # Fill NaN values
        df = df.bfill().fillna(0)

        return df

    def train_models(self, use_database: bool = True):
        """Train forecasting models using data from database or generate sample data"""
        if use_database:
            df = self.load_historical_data_from_db()
            if df.empty:
                print("⚠️ No historical data found in database. Generating sample data...")
                df = self.generate_sample_data()
                self.save_sample_data_to_db(df)
        else:
            df = self.generate_sample_data()
            self.save_sample_data_to_db(df)

        # Store historical data for use in predictions
        self.historical_data = df.copy()
        
        df_prepared = self.prepare_features(df)

        feature_columns = [
            'day_of_week', 'month', 'is_weekend', 'special_event',
            'weather_sunny', 'weather_rainy',
            'consumption_7day_avg', 'consumption_14day_avg', 'consumption_30day_avg',
            'consumption_lag1', 'consumption_lag7'
        ]

        food_items = df['food_item'].unique()
        
        for item in food_items:
            item_data = df_prepared[df_prepared['food_item'] == item].copy()

            # Skip if not enough data
            if len(item_data) < 50:
                continue

            # Prepare training data
            X = item_data[feature_columns].values
            y = item_data['consumption'].values

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_scaled, y)

            # Store model and scaler
            self.models[item] = model
            self.scalers[item] = scaler

        print(f"✅ Trained models for {len(self.models)} food items")

    def predict_consumption(self, food_item: str, date: datetime, weather: str = 'sunny', special_event: int = 0) -> Optional[float]:
        """Predict consumption for a specific item and date"""
        if food_item not in self.models:
            return None

        # Prepare features for prediction
        day_of_week = date.weekday()
        month = date.month
        is_weekend = int(day_of_week >= 5)
        weather_sunny = int(weather == 'sunny')
        weather_rainy = int(weather == 'rainy')

        # Get actual historical data for lag features and rolling averages
        if hasattr(self, 'historical_data') and self.historical_data is not None:
            item_history = self.historical_data[
                self.historical_data['food_item'] == food_item
            ].copy()
            
            if not item_history.empty:
                item_history = item_history.sort_values('date')
                recent_data = item_history.tail(30)
                
                consumption_7day_avg = recent_data['consumption'].tail(7).mean() if len(recent_data) >= 7 else recent_data['consumption'].mean()
                consumption_14day_avg = recent_data['consumption'].tail(14).mean() if len(recent_data) >= 14 else recent_data['consumption'].mean()
                consumption_30day_avg = recent_data['consumption'].mean()
                
                consumption_lag1 = recent_data['consumption'].iloc[-1] if len(recent_data) >= 1 else consumption_7day_avg
                consumption_lag7 = recent_data['consumption'].iloc[-7] if len(recent_data) >= 7 else consumption_7day_avg
            else:
                consumption_7day_avg = consumption_14day_avg = consumption_30day_avg = 20
                consumption_lag1 = consumption_lag7 = 20
        else:
            consumption_7day_avg = consumption_14day_avg = consumption_30day_avg = 20
            consumption_lag1 = consumption_lag7 = 20

        features = np.array([[
            day_of_week, month, is_weekend, special_event,
            weather_sunny, weather_rainy,
            consumption_7day_avg, consumption_14day_avg, consumption_30day_avg,
            consumption_lag1, consumption_lag7
        ]])

        # Scale features
        features_scaled = self.scalers[food_item].transform(features)

        # Make prediction
        prediction = self.models[food_item].predict(features_scaled)[0]
        prediction = max(0, int(prediction))
        
        # Save prediction to database
        self.save_forecast_result(food_item, date, prediction)
        
        return prediction

    def save_forecast_result(self, food_item: str, forecast_date: datetime, predicted_consumption: float):
        """Save forecast result to database"""
        food_item_id = self.food_items.get(food_item)
        if not food_item_id:
            return
        
        forecast_result = ForecastResult(
            food_item_id=food_item_id,
            forecast_date=forecast_date,
            prediction_date=datetime.utcnow(),
            predicted_consumption=predicted_consumption,
            model_version="RandomForest_v1.0"
        )
        
        self.db.add(forecast_result)
        self.db.commit()

    def generate_restock_recommendations(self, days_ahead: int = 7, safety_margin: float = 0.2) -> Dict:
        """Generate and save restock recommendations to database"""
        # Get current inventory levels
        inventory_records = self.db.query(InventoryRecord, FoodItem.name)\
                                  .join(FoodItem, InventoryRecord.food_item_id == FoodItem.id)\
                                  .all()
        
        recommendations = {}
        
        for record, food_name in inventory_records:
            if food_name not in self.models:
                continue
            
            # Predict consumption for next N days
            daily_predictions = []
            current_date = datetime.now()
            total_predicted_consumption = 0
            
            for day in range(days_ahead):
                future_date = current_date + timedelta(days=day)
                predicted_consumption = self.predict_consumption(
                    food_name, future_date, weather='sunny', special_event=0
                )
                
                if predicted_consumption is not None:
                    daily_predictions.append({
                        'date': future_date.strftime('%Y-%m-%d'),
                        'predicted_consumption': predicted_consumption
                    })
                    total_predicted_consumption += predicted_consumption
            
            if daily_predictions:
                # Calculate restock needs
                current_stock = record.current_stock
                stock_needed = total_predicted_consumption * (1 + safety_margin)
                restock_needed = max(0, stock_needed - current_stock)
                
                # Determine priority level
                stock_ratio = current_stock / record.reorder_point if record.reorder_point > 0 else 1
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
                        estimated_cost=record.unit_cost * restock_needed if record.unit_cost else None
                    )
                    
                    # Check if recommendation already exists for today
                    existing = self.db.query(RestockRecommendation).filter(
                        RestockRecommendation.food_item_id == record.food_item_id,
                        RestockRecommendation.recommendation_date >= datetime.now().date()
                    ).first()
                    
                    if not existing:
                        self.db.add(recommendation)
                
                recommendations[food_name] = {
                    'current_stock': current_stock,
                    'predicted_consumption': total_predicted_consumption,
                    'stock_needed': int(stock_needed),
                    'restock_needed': int(restock_needed),
                    'priority_level': priority,
                    'daily_predictions': daily_predictions,
                    'status': 'RESTOCK NEEDED' if restock_needed > 0 else 'SUFFICIENT STOCK'
                }
        
        self.db.commit()
        return recommendations

    def generate_sample_data(self, days=365):
        """Generate realistic restaurant inventory data (same as original)"""
        np.random.seed(42)
        
        # Use food items from database
        food_items = list(self.food_items.keys())

        data = []
        start_date = datetime.now() - timedelta(days=days)

        for i in range(days):
            date = start_date + timedelta(days=i)

            # Add seasonality and day-of-week effects
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday
            month = date.month

            # Weekend multiplier
            weekend_mult = 1.3 if day_of_week >= 5 else 1.0

            # Seasonal multiplier
            if month in [12, 1, 2]:  # Winter
                seasonal_mult = 0.8
            elif month in [6, 7, 8]:  # Summer
                seasonal_mult = 1.2
            else:
                seasonal_mult = 1.0

            for item in food_items:
                # Base consumption with item-specific patterns
                base_consumption = {
                    'Chicken Breast': 25, 'Beef Steak': 15, 'Salmon': 12,
                    'Pasta': 30, 'Rice': 20, 'Tomatoes': 18, 'Onions': 15,
                    'Lettuce': 10, 'Cheese': 12, 'Bread': 35, 'Potatoes': 22,
                    'Carrots': 8, 'Bell Peppers': 10, 'Mushrooms': 7, 'Garlic': 3
                }.get(item, 15)  # Default to 15 if item not in dict

                # Add randomness, seasonality, and day effects
                daily_consumption = max(0, int(
                    base_consumption *
                    weekend_mult *
                    seasonal_mult *
                    np.random.normal(1, 0.2)  # Random variation
                ))

                # Weather effect (random)
                weather_effect = np.random.choice(['sunny', 'rainy', 'cloudy'], p=[0.6, 0.2, 0.2])
                if weather_effect == 'rainy':
                    daily_consumption = int(daily_consumption * 0.8)
                elif weather_effect == 'sunny':
                    daily_consumption = int(daily_consumption * 1.1)

                # Special events (random)
                special_event = np.random.choice([0, 1], p=[0.9, 0.1])
                if special_event:
                    daily_consumption = int(daily_consumption * 1.5)

                data.append({
                    'date': date,
                    'food_item': item,
                    'day_of_week': day_of_week,
                    'month': month,
                    'is_weekend': int(day_of_week >= 5),
                    'weather': weather_effect,
                    'special_event': special_event,
                    'consumption': daily_consumption
                })

        return pd.DataFrame(data)

    def print_forecast_summary(self, forecast_results: Dict, days_ahead: int = 7):
        """Print a formatted forecast summary"""
        print(f"\n🍽️  RESTAURANT INVENTORY FORECAST - NEXT {days_ahead} DAYS")
        print("=" * 60)

        urgent_items = []
        sufficient_items = []

        for item, data in forecast_results.items():
            if data['status'] == 'RESTOCK NEEDED':
                urgent_items.append((item, data))
            else:
                sufficient_items.append((item, data))

        # Print urgent items first
        if urgent_items:
            print("\n🚨 URGENT - RESTOCK NEEDED:")
            print("-" * 30)
            for item, data in urgent_items:
                print(f"{item:15} | Current: {data['current_stock']:3.0f} | "
                      f"Need: {data['predicted_consumption']:3.0f} | "
                      f"Order: {data['restock_needed']:3.0f} | "
                      f"Priority: {data['priority_level']}")

        if sufficient_items:
            print(f"\n✅ SUFFICIENT STOCK ({len(sufficient_items)} items):")
            print("-" * 30)
            for item, data in sufficient_items[:5]:  # Show top 5
                print(f"{item:15} | Current: {data['current_stock']:3.0f} | "
                      f"Need: {data['predicted_consumption']:3.0f}")

            if len(sufficient_items) > 5:
                print(f"... and {len(sufficient_items) - 5} more items with sufficient stock")

def import_csv_to_database(csv_file_path: str):
    """
    Simple function to import your CSV file into the database
    Call this function to load your existing CSV data as historical records
    """
    print(f"🚀 Starting CSV import process...")
    print(f"📂 CSV file: {csv_file_path}")
    
    # Initialize database first
    from database import create_database, init_sample_food_items
    create_database()
    init_sample_food_items()
    
    # Initialize forecaster and load CSV
    forecaster = DatabaseIntegratedForecaster()
    saved, skipped = forecaster.load_csv_to_database(csv_file_path)
    
    if saved > 0:
        print(f"\n🎉 Success! Your CSV data is now in the database as historical records")
        print(f"📊 You can now use this data for forecasting and analysis")
        
        # Show some statistics
        total_records = forecaster.db.query(ConsumptionHistory).count()
        print(f"📈 Total historical records in database: {total_records}")
        
    return forecaster

if __name__ == "__main__":
    # Example usage - uncomment the line below and update the path to your CSV file
    # forecaster = import_csv_to_database("restaurant_inventory_data.csv")
    
    # Or use the regular flow
    forecaster = DatabaseIntegratedForecaster()
    forecaster.train_models(use_database=True)
    recommendations = forecaster.generate_restock_recommendations()
    forecaster.print_forecast_summary(recommendations)