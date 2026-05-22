"""
Comprehensive Recommendation System Test
Tests all recommendation endpoints and functionality
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class RecommendationTester:
    def __init__(self):
        self.passed_tests = 0
        self.total_tests = 0
        self.results = []
    
    def test(self, test_name, test_func):
        """Execute a test and track results"""
        self.total_tests += 1
        print(f"\n{'='*60}")
        print(f"TEST {self.total_tests}: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            if result:
                self.passed_tests += 1
                self.results.append(f"✅ {test_name}")
                print(f"✅ PASSED: {test_name}")
            else:
                self.results.append(f"❌ {test_name}")
                print(f"❌ FAILED: {test_name}")
        except Exception as e:
            self.results.append(f"❌ {test_name} - ERROR: {str(e)}")
            print(f"❌ ERROR in {test_name}: {e}")
    
    def test_server_health(self):
        """Test if the server is running and healthy"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"Server Status: {data['status']}")
                print(f"Data Summary: {data['data_summary']}")
                return True
            else:
                print(f"Health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server! Make sure it's running on localhost:8000")
            return False
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def test_basic_recommendations(self):
        """Test basic recommendation endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/users/1/recommendations")
            
            if response.status_code != 200:
                print(f"Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_keys = ['user_id', 'user_preferences', 'recommendations', 'generated_at']
            for key in required_keys:
                if key not in data:
                    print(f"Missing key in response: {key}")
                    return False
            
            # Check if recommendations are returned
            recommendations = data['recommendations']
            if not recommendations:
                print("No recommendations returned!")
                return False
            
            print(f"✅ User ID: {data['user_id']}")
            print(f"✅ Recommendations returned: {len(recommendations)}")
            print(f"✅ User preferences loaded: {bool(data['user_preferences'])}")
            
            # Validate recommendation structure
            for i, rec in enumerate(recommendations[:3]):
                if 'dish' not in rec or 'confidence_score' not in rec:
                    print(f"Invalid recommendation structure at index {i}")
                    return False
                
                dish = rec['dish']
                print(f"  Recommendation {i+1}: {dish['name']} ({dish['price']} DZD)")
                print(f"    Popularity: {dish['popularity']}/10")
                print(f"    Confidence: {rec['confidence_score']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"Error testing basic recommendations: {e}")
            return False
    
    def test_recommendations_with_restaurant_filter(self):
        """Test recommendations with restaurant filter"""
        try:
            # First get available restaurants
            restaurants_response = requests.get(f"{BASE_URL}/restaurants")
            if restaurants_response.status_code != 200:
                print("Cannot get restaurants list")
                return False
            
            restaurants = restaurants_response.json()
            if not restaurants:
                print("No restaurants available")
                return False
            
            restaurant_id = restaurants[0]['id']
            restaurant_name = restaurants[0]['name']
            
            # Test with restaurant filter
            response = requests.get(f"{BASE_URL}/users/1/recommendations?restaurant_id={restaurant_id}&limit=3")
            
            if response.status_code != 200:
                print(f"Failed with status code: {response.status_code}")
                return False
            
            data = response.json()
            
            print(f"✅ Testing with restaurant: {restaurant_name} (ID: {restaurant_id})")
            print(f"✅ Filtered recommendations: {len(data['recommendations'])}")
            print(f"✅ Restaurant ID in response: {data.get('restaurant_id')}")
            
            # Show filtered recommendations
            for i, rec in enumerate(data['recommendations']):
                dish = rec['dish']
                print(f"  {i+1}. {dish['name']} - {dish['price']} DZD (Popularity: {dish['popularity']})")
            
            return True
            
        except Exception as e:
            print(f"Error testing restaurant filter: {e}")
            return False
    
    def test_multiple_users(self):
        """Test recommendations for multiple users"""
        try:
            # Get available users
            users_response = requests.get(f"{BASE_URL}/users")
            if users_response.status_code != 200:
                print("Cannot get users list")
                return False
            
            users = users_response.json()
            if len(users) < 2:
                print("Need at least 2 users for this test")
                return False
            
            results = {}
            for user in users[:3]:  # Test first 3 users
                user_id = user['id']
                user_name = f"{user['firstName']} {user['lastName']}"
                
                response = requests.get(f"{BASE_URL}/users/{user_id}/recommendations?limit=2")
                
                if response.status_code == 200:
                    data = response.json()
                    results[user_name] = len(data['recommendations'])
                    
                    print(f"✅ {user_name} (ID: {user_id}): {len(data['recommendations'])} recommendations")
                    
                    # Show user preferences
                    preferences = data.get('user_preferences', {})
                    if preferences.get('cuisine_preferences'):
                        print(f"    Prefers: {', '.join(preferences['cuisine_preferences'])}")
                else:
                    print(f"❌ Failed for user {user_name}: {response.status_code}")
                    return False
            
            print(f"✅ Successfully tested recommendations for {len(results)} users")
            return True
            
        except Exception as e:
            print(f"Error testing multiple users: {e}")
            return False
    
    def test_recommendation_quality(self):
        """Test the quality and logic of recommendations"""
        try:
            response = requests.get(f"{BASE_URL}/users/1/recommendations?limit=5")
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            recommendations = data['recommendations']
            
            if not recommendations:
                print("No recommendations to test quality")
                return False
            
            # Test 1: Recommendations should be sorted by popularity/confidence
            popularities = [rec['dish']['popularity'] for rec in recommendations]
            is_sorted = all(popularities[i] >= popularities[i+1] for i in range(len(popularities)-1))
            
            if is_sorted:
                print("✅ Recommendations are properly sorted by popularity")
            else:
                print("❌ Recommendations are not sorted properly")
                return False
            
            # Test 2: All dishes should be available
            available_count = sum(1 for rec in recommendations if rec['dish']['isAvailable'])
            if available_count == len(recommendations):
                print(f"✅ All {available_count} recommended dishes are available")
            else:
                print(f"❌ Some recommended dishes are not available")
                return False
            
            # Test 3: Confidence scores should be reasonable (0-1)
            confidence_scores = [rec['confidence_score'] for rec in recommendations]
            valid_scores = all(0 <= score <= 1 for score in confidence_scores)
            
            if valid_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                print(f"✅ All confidence scores are valid (avg: {avg_confidence:.2f})")
            else:
                print("❌ Some confidence scores are out of range")
                return False
            
            # Test 4: Each recommendation should have an explanation
            explanations = [rec.get('explanation', '') for rec in recommendations]
            has_explanations = all(len(exp) > 0 for exp in explanations)
            
            if has_explanations:
                print("✅ All recommendations have explanations")
            else:
                print("❌ Some recommendations lack explanations")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error testing recommendation quality: {e}")
            return False
    
    def test_user_preferences_integration(self):
        """Test that user preferences are properly integrated"""
        try:
            response = requests.get(f"{BASE_URL}/users/1/recommendations")
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            user_prefs = data.get('user_preferences', {})
            
            if not user_prefs:
                print("❌ No user preferences found")
                return False
            
            print("✅ User preferences loaded:")
            
            # Check cuisine preferences
            cuisine_prefs = user_prefs.get('cuisine_preferences', [])
            if cuisine_prefs:
                print(f"  Cuisine preferences: {', '.join(cuisine_prefs)}")
            
            # Check dietary restrictions
            dietary = user_prefs.get('dietary_restrictions', [])
            if dietary:
                print(f"  Dietary restrictions: {', '.join(dietary)}")
            
            # Check price range
            price_range = user_prefs.get('price_range', {})
            if price_range:
                print(f"  Price range: {price_range.get('min', 0)} - {price_range.get('max', 0)} DZD")
            
            # Check favorite flavors
            flavors = user_prefs.get('favorite_flavors', [])
            if flavors:
                print(f"  Favorite flavors: {', '.join(flavors[:3])}")
            
            print("✅ User preferences successfully integrated into recommendations")
            return True
            
        except Exception as e:
            print(f"Error testing user preferences: {e}")
            return False
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        try:
            test_results = []
            
            # Test 1: Non-existent user
            response = requests.get(f"{BASE_URL}/users/999/recommendations")
            if response.status_code == 404:
                print("✅ Properly handles non-existent user (404)")
                test_results.append(True)
            else:
                print(f"❌ Wrong response for non-existent user: {response.status_code}")
                test_results.append(False)
            
            # Test 2: Invalid limit parameter
            response = requests.get(f"{BASE_URL}/users/1/recommendations?limit=0")
            if response.status_code == 200:
                data = response.json()
                if len(data['recommendations']) == 0:
                    print("✅ Properly handles limit=0")
                    test_results.append(True)
                else:
                    print("❌ Should return 0 recommendations for limit=0")
                    test_results.append(False)
            else:
                print("❌ Failed to handle limit=0")
                test_results.append(False)
            
            # Test 3: Very high limit
            response = requests.get(f"{BASE_URL}/users/1/recommendations?limit=100")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Handles high limit (returned {len(data['recommendations'])} recommendations)")
                test_results.append(True)
            else:
                print("❌ Failed to handle high limit")
                test_results.append(False)
            
            return all(test_results)
            
        except Exception as e:
            print(f"Error testing edge cases: {e}")
            return False
    
    def run_all_tests(self):
        """Run all recommendation tests"""
        print("🧪 COMPREHENSIVE RECOMMENDATION SYSTEM TEST")
        print("="*60)
        print(f"Testing API at: {BASE_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test("Server Health Check", self.test_server_health)
        self.test("Basic Recommendations", self.test_basic_recommendations)
        self.test("Restaurant Filter", self.test_recommendations_with_restaurant_filter)
        self.test("Multiple Users", self.test_multiple_users)
        self.test("Recommendation Quality", self.test_recommendation_quality)
        self.test("User Preferences Integration", self.test_user_preferences_integration)
        self.test("Edge Cases", self.test_edge_cases)
        
        # Summary
        print(f"\n{'='*60}")
        print("🎯 TEST SUMMARY")
        print('='*60)
        
        for result in self.results:
            print(result)
        
        success_rate = (self.passed_tests / self.total_tests) * 100
        print(f"\nTests passed: {self.passed_tests}/{self.total_tests}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 PERFECT! All recommendation tests passed!")
        elif success_rate >= 85:
            print("🎊 EXCELLENT! Recommendation system is working great!")
        elif success_rate >= 70:
            print("👍 GOOD! Most recommendation features are working.")
        else:
            print("⚠️  NEEDS WORK! Several recommendation issues detected.")
        
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 70

def main():
    """Main test function"""
    print("Starting recommendation system test...")
    print("Make sure your API server is running on http://localhost:8000")
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    tester = RecommendationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()