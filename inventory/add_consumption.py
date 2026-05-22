from forecaster_db import DatabaseIntegratedForecaster
from datetime import datetime

def add_daily_consumption():
    """Add today's consumption to the database"""
    
    print("🍽️ Adding Daily Consumption Records")
    print("=" * 40)
    
    # Initialize the system
    forecaster = DatabaseIntegratedForecaster()
    
    # TODAY'S CONSUMPTION - EDIT THESE VALUES FOR YOUR ACTUAL USAGE
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
    
    # SETTINGS - CHANGE THESE AS NEEDED
    weather_today = 'sunny'        # Options: 'sunny', 'rainy', 'cloudy'
    special_event_today = False    # Change to True for holidays/busy days
    
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"🌤️ Weather: {weather_today}")
    print(f"🎉 Special Event: {special_event_today}")
    print()
    
    # Add records to database
    added_count = 0
    for food_item, amount in today_consumption.items():
        try:
            forecaster.add_consumption_record(
                food_item=food_item,
                date=datetime.now(),
                consumption=amount,
                weather=weather_today,
                special_event=special_event_today
            )
            print(f"✅ {food_item}: {amount} units")
            added_count += 1
        except Exception as e:
            print(f"❌ {food_item}: Error - {str(e)}")
    
    print(f"\n🎉 Successfully added {added_count} consumption records to database!")
    print(f"💡 Edit the values in this file to match your actual daily usage")

if __name__ == "__main__":
    add_daily_consumption()