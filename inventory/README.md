# 🍽️ Restaurant Inventory Forecasting System

A simple system to track food consumption and predict future needs for your
restaurant.

## 📋 Quick Setup

1. **Install Requirements**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Your database is already set up** with 5,475 historical records imported ✅

---

## 🎯 **Main Tasks**

### **1. Add New Daily Consumption Records**

#### **Method 1: Using Python Script (Easiest)**

Create a file called `add_consumption.py`:

```python
from forecaster_db import DatabaseIntegratedForecaster
from datetime import datetime

# Initialize the system
forecaster = DatabaseIntegratedForecaster()

# Add today's consumption - EDIT THESE VALUES
today_consumption = {
    'Chicken Breast': 28,     # kg used today
    'Beef Steak': 12,         # kg used today
    'Salmon': 8,              # kg used today
    'Pasta': 35,              # kg used today
    'Rice': 22,               # kg used today
    'Tomatoes': 15,           # kg used today
    'Onions': 18,             # kg used today
    'Lettuce': 12,            # kg used today
    'Cheese': 14,             # kg used today
    'Bread': 45,              # units used today
    'Potatoes': 25,           # kg used today
    'Carrots': 10,            # kg used today
    'Bell Peppers': 8,        # kg used today
    'Mushrooms': 6,           # kg used today
    'Garlic': 3               # kg used today
}

# Add records to database
for food_item, amount in today_consumption.items():
    forecaster.add_consumption_record(
        food_item=food_item,
        date=datetime.now(),
        consumption=amount,
        weather='sunny',          # Change: sunny/rainy/cloudy
        special_event=False       # Change to True for holidays/events
    )

print("✅ Today's consumption added to database!")
```

**To use:**

1. Edit the consumption amounts for today
2. Run: `python add_consumption.py`

#### **Method 2: Using Python Interactive**

You can also add records directly in Python:

```python
from forecaster_db import DatabaseIntegratedForecaster
from datetime import datetime

forecaster = DatabaseIntegratedForecaster()
forecaster.add_consumption_record('Chicken Breast', datetime.now(), 25, weather='sunny')
```

---

### **2. Get Predictions and Recommendations**

Create a file called `get_predictions.py`:

```python
from forecaster_db import DatabaseIntegratedForecaster
from datetime import datetime, timedelta

# Initialize the system
forecaster = DatabaseIntegratedForecaster()

# Train the AI model with your historical data
forecaster.train_models(use_database=True)

print("🔮 FORECASTING RESULTS")
print("=" * 50)

# Get predictions for specific items and dates
items_to_predict = ['Chicken Breast', 'Pasta', 'Tomatoes']

for item in items_to_predict:
    print(f"\n📊 {item} predictions:")

    # Tomorrow's prediction
    tomorrow = datetime.now() + timedelta(days=1)
    pred_sunny = forecaster.predict_consumption(item, tomorrow, weather='sunny')
    pred_rainy = forecaster.predict_consumption(item, tomorrow, weather='rainy')

    print(f"   Tomorrow (sunny): {pred_sunny} units")
    print(f"   Tomorrow (rainy): {pred_rainy} units")

    # Weekend prediction
    weekend_date = tomorrow + timedelta(days=(5 - tomorrow.weekday()))
    pred_weekend = forecaster.predict_consumption(item, weekend_date)
    print(f"   Weekend: {pred_weekend} units")

# Get automatic restock recommendations
print(f"\n🛒 RESTOCK RECOMMENDATIONS")
print("=" * 50)

recommendations = forecaster.generate_restock_recommendations(
    days_ahead=7,        # Predict for next 7 days
    safety_margin=0.2    # 20% extra safety stock
)

forecaster.print_forecast_summary(recommendations)
```

**To use:** Run `python get_predictions.py`

---

## 🗂️ **Available Food Items**

Your system tracks these 15 items:

- Chicken Breast, Beef Steak, Salmon, Pasta, Rice
- Tomatoes, Onions, Lettuce, Cheese, Bread
- Potatoes, Carrots, Bell Peppers, Mushrooms, Garlic

---

## 📊 **View Your Data**

### **See Consumption History**

```python
from forecaster_db import DatabaseIntegratedForecaster

forecaster = DatabaseIntegratedForecaster()
df = forecaster.load_historical_data_from_db(days_back=30)  # Last 30 days
print(df.head())
```

### **Interactive Analysis**

Use the Jupyter notebook `test.ipynb` for interactive data exploration and
analysis.

---

## ⚡ **Daily Workflow**

### **Every Day:**

1. **Record what you used**: Edit and run `add_consumption.py`
2. **Get tomorrow's predictions**: Run `get_predictions.py`
3. **Check restock alerts**: Look for items marked "RESTOCK NEEDED"

### **Weekly:**

- Review consumption analytics
- Update inventory levels if needed
- Adjust reorder points based on patterns

---

## 🤖 **How the AI Works**

The system uses your historical data to learn:

- **Seasonal patterns** (summer vs winter)
- **Day-of-week effects** (weekends vs weekdays)
- **Weather impact** (sunny vs rainy days)
- **Special events** (holidays, busy days)

**The more data you add, the better the predictions become!**

---

## 📁 **File Structure**

```
📁 Your Project/
├── 📄 database.py          # Database setup
├── 📄 forecaster_db.py     # AI forecasting engine
├── 📄 restaurant_inventory.db  # Your data (5,475+ records)
├── 📄 requirements.txt     # Dependencies
├── 📄 add_consumption.py   # ← Use this to add daily records
├── 📄 get_predictions.py   # ← Use this to get forecasts
├── 📄 test.ipynb          # Jupyter notebook for analysis
└── 📄 README.md           # This guide
```
