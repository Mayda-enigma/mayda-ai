import requests
import json
import time

# Test the fixed recommendations
def test_recommendations():
    print("🧪 Testing Fixed Recommendations Endpoint")
    print("="*50)
    
    time.sleep(1)  # Give server a moment
    
    try:
        response = requests.get('http://127.0.0.1:8000/users/1/recommendations')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"User ID: {data.get('user_id')}")
            print(f"Restaurant ID: {data.get('restaurant_id')}")
            print(f"Number of recommendations: {len(data.get('recommendations', []))}")
            
            if data.get('recommendations'):
                print("\nTop 3 recommendations:")
                for i, rec in enumerate(data['recommendations'][:3], 1):
                    dish = rec['dish']
                    print(f"  {i}. {dish['name']} - {dish['price']} DZD")
                    print(f"     Popularity: {dish['popularity']}/10")
                    print(f"     Confidence: {rec['confidence_score']:.2f}")
                    print(f"     {rec['explanation']}")
                    print()
            else:
                print("❌ No recommendations returned")
                
            # Test user preferences
            if data.get('user_preferences'):
                prefs = data['user_preferences']
                print(f"User preferences: {prefs.get('cuisine_preferences', [])}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_recommendations()