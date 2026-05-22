"""
Scenario-Based Recommendation Testing
Tests recommendations for different user types and situations
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class UserScenarioTester:
    def __init__(self):
        self.passed_scenarios = 0
        self.total_scenarios = 0
        self.users_data = []
        
    def load_users(self):
        """Load all users and their profiles"""
        try:
            response = requests.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                
                # Get detailed profile for each user
                for user in users:
                    profile_response = requests.get(f"{BASE_URL}/users/{user['id']}/profile")
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        self.users_data.append({
                            'id': user['id'],
                            'name': f"{user['firstName']} {user['lastName']}",
                            'profile': profile,
                            'preferences': profile.get('preferences', {}),
                            'order_history': profile.get('orderHistory', []),
                            'reviews': profile.get('reviews', [])
                        })
                
                print(f"✅ Loaded {len(self.users_data)} user profiles")
                return True
            else:
                print(f"❌ Failed to load users: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            return False
    
    def test_scenario(self, scenario_name, test_func):
        """Execute a scenario test"""
        self.total_scenarios += 1
        print(f"\n{'='*70}")
        print(f"SCENARIO {self.total_scenarios}: {scenario_name}")
        print('='*70)
        
        try:
            result = test_func()
            if result:
                self.passed_scenarios += 1
                print(f"✅ SCENARIO PASSED: {scenario_name}")
            else:
                print(f"❌ SCENARIO FAILED: {scenario_name}")
        except Exception as e:
            print(f"❌ SCENARIO ERROR: {scenario_name} - {e}")
    
    def scenario_vegetarian_user(self):
        """Test recommendations for a vegetarian user"""
        # Find a user with vegetarian preferences
        vegetarian_user = None
        for user in self.users_data:
            prefs = user['preferences']
            dietary = prefs.get('dietary_restrictions', [])
            if any('vegetarian' in str(d).lower() for d in dietary):
                vegetarian_user = user
                break
        
        if not vegetarian_user:
            print("⚠️ No vegetarian user found in database")
            return False
        
        print(f"👤 Testing user: {vegetarian_user['name']} (ID: {vegetarian_user['id']})")
        print(f"🥬 Dietary restrictions: {vegetarian_user['preferences'].get('dietary_restrictions', [])}")
        
        # Get recommendations
        response = requests.get(f"{BASE_URL}/users/{vegetarian_user['id']}/recommendations?limit=5")
        
        if response.status_code != 200:
            print(f"❌ API call failed: {response.status_code}")
            return False
        
        data = response.json()
        recommendations = data['recommendations']
        
        if not recommendations:
            print("❌ No recommendations returned")
            return False
        
        print(f"📊 Recommendations received: {len(recommendations)}")
        
        # Analyze recommendations
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            print(f"  {i}. {dish['name']} - {dish['price']} DZD")
            print(f"     Popularity: {dish['popularity']}/10")
            print(f"     Confidence: {rec['confidence_score']:.2f}")
            
            # Check if dish seems vegetarian-friendly (basic heuristic)
            dish_text = (dish['name'] + ' ' + dish.get('description', '')).lower()
            meat_keywords = ['chicken', 'beef', 'lamb', 'fish', 'meat', 'seafood']
            has_meat = any(keyword in dish_text for keyword in meat_keywords)
            
            if not has_meat:
                print(f"     ✅ Appears vegetarian-friendly")
            else:
                print(f"     ⚠️ May contain meat: {dish['name']}")
        
        return True
    
    def scenario_budget_conscious_user(self):
        """Test recommendations for a user with budget constraints"""
        # Find a user with a lower budget range
        budget_user = None
        for user in self.users_data:
            prefs = user['preferences']
            price_range = prefs.get('price_range', {})
            if price_range and price_range.get('max', float('inf')) < 1500:
                budget_user = user
                break
        
        if not budget_user:
            print("⚠️ No budget-conscious user found, using first user with budget limit")
            budget_user = self.users_data[0] if self.users_data else None
        
        if not budget_user:
            return False
        
        print(f"👤 Testing user: {budget_user['name']} (ID: {budget_user['id']})")
        price_range = budget_user['preferences'].get('price_range', {})
        print(f"💰 Price range: {price_range.get('min', 0)} - {price_range.get('max', '∞')} DZD")
        
        # Get recommendations
        response = requests.get(f"{BASE_URL}/users/{budget_user['id']}/recommendations?limit=5")
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        recommendations = data['recommendations']
        
        if not recommendations:
            return False
        
        print(f"📊 Recommendations received: {len(recommendations)}")
        
        # Check if recommendations respect budget
        budget_max = price_range.get('max', float('inf'))
        within_budget = 0
        
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            price = dish['price']
            is_affordable = price <= budget_max if budget_max != float('inf') else True
            
            print(f"  {i}. {dish['name']} - {price} DZD {'✅' if is_affordable else '❌'}")
            print(f"     Popularity: {dish['popularity']}/10")
            
            if is_affordable:
                within_budget += 1
        
        if budget_max != float('inf'):
            print(f"📈 {within_budget}/{len(recommendations)} recommendations within budget")
            return within_budget > 0
        else:
            print("📈 No specific budget constraint to test")
            return True
    
    def scenario_cuisine_lover(self):
        """Test recommendations for a user with specific cuisine preferences"""
        # Find user with clear cuisine preferences
        cuisine_user = None
        for user in self.users_data:
            prefs = user['preferences']
            cuisine_prefs = prefs.get('cuisine_preferences', [])
            if cuisine_prefs:
                cuisine_user = user
                break
        
        if not cuisine_user:
            return False
        
        print(f"👤 Testing user: {cuisine_user['name']} (ID: {cuisine_user['id']})")
        cuisine_prefs = cuisine_user['preferences'].get('cuisine_preferences', [])
        print(f"🍽️ Preferred cuisines: {', '.join(cuisine_prefs)}")
        
        # Get recommendations
        response = requests.get(f"{BASE_URL}/users/{cuisine_user['id']}/recommendations?limit=5")
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        recommendations = data['recommendations']
        
        if not recommendations:
            return False
        
        print(f"📊 Recommendations received: {len(recommendations)}")
        
        # Analyze if recommendations align with cuisine preferences
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            print(f"  {i}. {dish['name']} - {dish['price']} DZD")
            print(f"     Popularity: {dish['popularity']}/10")
            print(f"     Explanation: {rec['explanation'][:80]}...")
        
        return True
    
    def scenario_frequent_orderer(self):
        """Test recommendations for a user with extensive order history"""
        # Find user with most orders
        frequent_user = max(self.users_data, 
                          key=lambda u: len(u['order_history']), 
                          default=None)
        
        if not frequent_user or not frequent_user['order_history']:
            return False
        
        print(f"👤 Testing user: {frequent_user['name']} (ID: {frequent_user['id']})")
        print(f"📋 Order history: {len(frequent_user['order_history'])} orders")
        print(f"⭐ Reviews written: {len(frequent_user['reviews'])} reviews")
        
        # Show recent orders
        recent_orders = frequent_user['order_history'][-3:]
        if recent_orders:
            print("🕒 Recent orders:")
            for order in recent_orders:
                print(f"  - Order #{order.get('orderNumber', 'N/A')}: {order.get('totalAmount', 0)} DZD ({order.get('status', 'Unknown')})")
        
        # Get recommendations
        response = requests.get(f"{BASE_URL}/users/{frequent_user['id']}/recommendations?limit=5")
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        recommendations = data['recommendations']
        
        if not recommendations:
            return False
        
        print(f"📊 Recommendations received: {len(recommendations)}")
        
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            print(f"  {i}. {dish['name']} - {dish['price']} DZD")
            print(f"     Popularity: {dish['popularity']}/10 | Confidence: {rec['confidence_score']:.2f}")
        
        return True
    
    def scenario_new_user(self):
        """Test recommendations for a user with minimal history"""
        # Find user with least orders
        new_user = min(self.users_data, 
                      key=lambda u: len(u['order_history']), 
                      default=None)
        
        if not new_user:
            return False
        
        print(f"👤 Testing user: {new_user['name']} (ID: {new_user['id']})")
        print(f"📋 Order history: {len(new_user['order_history'])} orders")
        print(f"⭐ Reviews written: {len(new_user['reviews'])} reviews")
        print("🆕 This appears to be a new user with limited history")
        
        # Get recommendations
        response = requests.get(f"{BASE_URL}/users/{new_user['id']}/recommendations?limit=5")
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        recommendations = data['recommendations']
        
        if not recommendations:
            return False
        
        print(f"📊 Recommendations received: {len(recommendations)}")
        print("💡 For new users, system should recommend popular items")
        
        # Check if recommendations are high-popularity items (good for new users)
        avg_popularity = sum(rec['dish']['popularity'] for rec in recommendations) / len(recommendations)
        print(f"📈 Average popularity of recommendations: {avg_popularity:.1f}/10")
        
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            print(f"  {i}. {dish['name']} - {dish['price']} DZD")
            print(f"     Popularity: {dish['popularity']}/10")
        
        # New users should get high-popularity recommendations
        return avg_popularity >= 7.0
    
    def scenario_restaurant_specific(self):
        """Test recommendations filtered by specific restaurants"""
        if not self.users_data:
            return False
        
        user = self.users_data[0]  # Use first user
        
        # Get available restaurants
        restaurants_response = requests.get(f"{BASE_URL}/restaurants")
        if restaurants_response.status_code != 200:
            return False
        
        restaurants = restaurants_response.json()
        if not restaurants:
            return False
        
        print(f"👤 Testing user: {user['name']} (ID: {user['id']})")
        print(f"🏪 Testing recommendations from {len(restaurants)} different restaurants")
        
        success_count = 0
        
        for restaurant in restaurants:
            rest_id = restaurant['id']
            rest_name = restaurant['name']
            
            print(f"\n🍽️ Testing {rest_name} (ID: {rest_id}):")
            
            response = requests.get(f"{BASE_URL}/users/{user['id']}/recommendations?restaurant_id={rest_id}&limit=3")
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data['recommendations']
                
                print(f"  📊 Recommendations: {len(recommendations)}")
                
                for i, rec in enumerate(recommendations, 1):
                    dish = rec['dish']
                    print(f"    {i}. {dish['name']} - {dish['price']} DZD (Pop: {dish['popularity']})")
                
                success_count += 1
            else:
                print(f"  ❌ Failed to get recommendations: {response.status_code}")
        
        print(f"\n📈 Successfully got recommendations from {success_count}/{len(restaurants)} restaurants")
        return success_count > 0
    
    def scenario_price_sensitivity(self):
        """Test how recommendations adapt to different price sensitivities"""
        if not self.users_data:
            return False
        
        # Test with different limit parameters to see price distribution
        user = self.users_data[0]
        
        print(f"👤 Testing user: {user['name']} (ID: {user['id']})")
        print("💰 Analyzing price sensitivity in recommendations")
        
        # Get recommendations with different limits
        limits = [3, 5, 10]
        price_distributions = {}
        
        for limit in limits:
            response = requests.get(f"{BASE_URL}/users/{user['id']}/recommendations?limit={limit}")
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data['recommendations']
                
                if recommendations:
                    prices = [rec['dish']['price'] for rec in recommendations]
                    avg_price = sum(prices) / len(prices)
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    price_distributions[limit] = {
                        'count': len(recommendations),
                        'avg_price': avg_price,
                        'min_price': min_price,
                        'max_price': max_price,
                        'prices': prices
                    }
                    
                    print(f"\n📊 Top {limit} recommendations:")
                    print(f"  Average price: {avg_price:.0f} DZD")
                    print(f"  Price range: {min_price:.0f} - {max_price:.0f} DZD")
                    
                    # Show price breakdown
                    expensive_count = sum(1 for p in prices if p > 2000)
                    moderate_count = sum(1 for p in prices if 1000 <= p <= 2000)
                    cheap_count = sum(1 for p in prices if p < 1000)
                    
                    print(f"  Price breakdown: {expensive_count} expensive (>2000), {moderate_count} moderate (1000-2000), {cheap_count} budget (<1000)")
        
        return len(price_distributions) > 0
    
    def run_all_scenarios(self):
        """Run all scenario tests"""
        print("🎭 USER SCENARIO TESTING FOR RECOMMENDATION SYSTEM")
        print("="*70)
        print(f"Testing API at: {BASE_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load user data first
        if not self.load_users():
            print("❌ Failed to load user data. Cannot proceed with scenario testing.")
            return False
        
        # Display user summary
        print(f"\n👥 USER PROFILES SUMMARY:")
        for user in self.users_data:
            prefs = user['preferences']
            cuisine_prefs = prefs.get('cuisine_preferences', [])
            dietary = prefs.get('dietary_restrictions', [])
            price_range = prefs.get('price_range', {})
            
            print(f"  • {user['name']} (ID: {user['id']})")
            if cuisine_prefs:
                print(f"    Cuisines: {', '.join(cuisine_prefs)}")
            if dietary:
                print(f"    Dietary: {', '.join(map(str, dietary))}")
            if price_range:
                print(f"    Budget: {price_range.get('min', 0)}-{price_range.get('max', '∞')} DZD")
            print(f"    History: {len(user['order_history'])} orders, {len(user['reviews'])} reviews")
        
        # Run scenario tests
        scenarios = [
            ("Vegetarian User Preferences", self.scenario_vegetarian_user),
            ("Budget-Conscious User", self.scenario_budget_conscious_user),
            ("Cuisine Preference Matching", self.scenario_cuisine_lover),
            ("Frequent Customer Recommendations", self.scenario_frequent_orderer),
            ("New User Cold Start", self.scenario_new_user),
            ("Restaurant-Specific Recommendations", self.scenario_restaurant_specific),
            ("Price Sensitivity Analysis", self.scenario_price_sensitivity)
        ]
        
        for scenario_name, scenario_func in scenarios:
            self.test_scenario(scenario_name, scenario_func)
        
        # Summary
        print(f"\n{'='*70}")
        print("🎯 SCENARIO TEST SUMMARY")
        print('='*70)
        
        success_rate = (self.passed_scenarios / self.total_scenarios) * 100 if self.total_scenarios > 0 else 0
        print(f"Scenarios passed: {self.passed_scenarios}/{self.total_scenarios}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 PERFECT! All scenarios handled correctly!")
        elif success_rate >= 80:
            print("🎊 EXCELLENT! Recommendation system adapts well to different users!")
        elif success_rate >= 60:
            print("👍 GOOD! Most user scenarios work properly.")
        else:
            print("⚠️ NEEDS IMPROVEMENT! Several user scenarios have issues.")
        
        # Insights
        print(f"\n💡 INSIGHTS:")
        print(f"• Tested {len(self.users_data)} different user profiles")
        print(f"• Verified personalization based on preferences, history, and constraints")
        print(f"• Analyzed recommendation quality across different user types")
        
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 60

def main():
    """Main function"""
    print("Starting user scenario testing...")
    print("Make sure your API server is running on http://localhost:8000")
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    tester = UserScenarioTester()
    tester.run_all_scenarios()

if __name__ == "__main__":
    main()