from forecaster_db import DatabaseIntegratedForecaster
from datetime import datetime, timedelta

def get_predictions():
    """Get predictions and restock recommendations"""
    
    print("🔮 RESTAURANT FORECASTING SYSTEM")
    print("=" * 50)
    
    # Initialize and train the system
    print("🤖 Loading historical data and training AI models...")
    forecaster = DatabaseIntegratedForecaster()
    forecaster.train_models(use_database=True)
    
    print("\n📊 INDIVIDUAL ITEM PREDICTIONS")
    print("-" * 30)
    
    # Get predictions for key items
    key_items = ['Chicken Breast', 'Pasta', 'Tomatoes', 'Bread', 'Rice']
    
    for item in key_items:
        print(f"\n🥘 {item}:")
        
        # Tomorrow's predictions
        tomorrow = datetime.now() + timedelta(days=1)
        pred_sunny = forecaster.predict_consumption(item, tomorrow, weather='sunny')
        pred_rainy = forecaster.predict_consumption(item, tomorrow, weather='rainy')
        pred_event = forecaster.predict_consumption(item, tomorrow, weather='sunny', special_event=1)
        
        print(f"   Tomorrow (sunny): {pred_sunny} units")
        print(f"   Tomorrow (rainy): {pred_rainy} units") 
        print(f"   Special event:    {pred_event} units")
        
        # This weekend
        days_to_weekend = (5 - tomorrow.weekday()) % 7
        weekend_date = tomorrow + timedelta(days=days_to_weekend)
        if days_to_weekend == 0:  # If tomorrow is Saturday
            weekend_date = tomorrow
        pred_weekend = forecaster.predict_consumption(item, weekend_date)
        print(f"   Weekend:          {pred_weekend} units")
    
    print(f"\n🛒 AUTOMATIC RESTOCK RECOMMENDATIONS")
    print("=" * 50)
    
    # Get restock recommendations
    recommendations = forecaster.generate_restock_recommendations(
        days_ahead=7,        # Predict for next 7 days
        safety_margin=0.2    # 20% extra safety stock
    )
    
    # Display formatted recommendations
    forecaster.print_forecast_summary(recommendations, days_ahead=7)
    
    print(f"\n📈 QUICK STATS")
    print("-" * 20)
    
    # Count urgent vs sufficient items
    urgent_items = sum(1 for data in recommendations.values() if data['status'] == 'RESTOCK NEEDED')
    total_items = len(recommendations)
    
    print(f"Total items tracked: {total_items}")
    print(f"Need restocking: {urgent_items}")
    print(f"Sufficient stock: {total_items - urgent_items}")
    
    if urgent_items > 0:
        print(f"\n⚠️  ACTION NEEDED: {urgent_items} items need restocking!")
    else:
        print(f"\n✅ All items have sufficient stock for the next 7 days")
    
    print(f"\n💡 Tips:")
    print(f"   • Add daily consumption with: python add_consumption.py")
    print(f"   • Use test.ipynb for interactive analysis")
    print(f"   • The more data you add, the better the predictions!")

if __name__ == "__main__":
    get_predictions()