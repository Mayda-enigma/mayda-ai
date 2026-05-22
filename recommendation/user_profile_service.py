"""
User Profile Service - Extracts and analyzes user preferences and history
"""
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter

class UserProfileService:
    """Service to analyze user preferences and history using API calls"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize with API base URL"""
        self.api_base_url = api_base_url.rstrip('/')
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request and handle errors"""
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API request failed: {str(e)}")
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user profile for recommendations
        
        Args:
            user_id: The user ID to analyze
            
        Returns:
            Dict containing user preferences, history, and analysis
        """
        try:
            # Get user data from API
            user_data = self._make_api_request(f"/users/{user_id}")
            
            # Get user's complete profile from API
            profile_data = self._make_api_request(f"/users/{user_id}/profile")
            
            # Extract embedded preferences
            preferences = self._extract_preferences(user_data.get("embeddedPref"))
            
            # Analyze order history using API data
            order_analysis = self._analyze_order_history_from_api(user_id, profile_data.get("orderHistory", []))
            
            # Get review patterns using API data
            review_analysis = self._analyze_reviews_from_api(profile_data.get("reviews", []))
            
            # Combine into comprehensive profile
            profile = {
                "user_id": user_id,
                "basic_info": {
                    "name": f"{user_data['firstName']} {user_data['lastName']}",
                    "role": user_data['role'],
                    "special_info": user_data.get('specialinfo', {})
                },
                "preferences": preferences,
                "order_history": order_analysis,
                "review_patterns": review_analysis,
                "profile_summary": self._generate_profile_summary(preferences, order_analysis, review_analysis)
            }
            
            return profile
            
        except Exception as e:
            raise ValueError(f"Error getting user profile: {str(e)}")
    
    def _extract_preferences(self, embedded_pref: Optional[str]) -> Dict[str, Any]:
        """Extract preferences from embeddedPref JSON field"""
        if not embedded_pref:
            return {"error": "No embedded preferences found"}
        
        try:
            preferences = json.loads(embedded_pref)
            return {
                "cuisine_preferences": preferences.get("cuisine_preferences", []),
                "dietary_restrictions": preferences.get("dietary_restrictions", []),
                "price_range": preferences.get("price_range", {"min": 0, "max": 10000}),
                "favorite_flavors": preferences.get("favorite_flavors", []),
                "spice_level": preferences.get("spice_level", "mild"),
                "meal_times": preferences.get("meal_times", ["lunch", "dinner"]),
                "cooking_methods": preferences.get("cooking_methods", []),
                "allergens_to_avoid": preferences.get("allergens_to_avoid", [])
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in embedded preferences"}
    
    def _analyze_order_history_from_api(self, user_id: int, order_history: List[Dict]) -> Dict[str, Any]:
        """Analyze user's order history from API data for patterns"""
        if not order_history:
            return {"error": "No order history found"}
        
        # Process order data from API response
        total_spent = sum(order["totalAmount"] for order in order_history)
        avg_order_value = total_spent / len(order_history) if order_history else 0
        
        # Count restaurant preferences
        restaurant_preferences = Counter(order["restaurantId"] for order in order_history)
        
        # Get order items for all orders to analyze dish preferences
        ordered_dishes_data = []
        order_frequencies = Counter()
        
        for order in order_history:
            try:
                # Get order items from API
                order_items = self._make_api_request(f"/orders/{order['id']}/items")
                
                for item in order_items:
                    # Get dish details from API
                    try:
                        dish = self._make_api_request(f"/dishes/{item['dishId']}")
                        ordered_dishes_data.append(dish)
                        order_frequencies[dish['id']] += item['quantity']
                    except:
                        continue  # Skip if dish not found
            except:
                continue  # Skip if order items not found
        
        # Analyze patterns
        favorite_dishes = order_frequencies.most_common(5)
        favorite_restaurants = restaurant_preferences.most_common(3)
        
        # Analyze cuisine preferences from ordered dishes
        cuisine_from_orders = self._extract_cuisine_from_api_dishes(ordered_dishes_data)
        
        return {
            "total_orders": len(order_history),
            "total_spent": round(total_spent, 2),
            "avg_order_value": round(avg_order_value, 2),
            "favorite_dishes": [{"dish_id": dish_id, "orders": count} for dish_id, count in favorite_dishes],
            "favorite_restaurants": [{"restaurant_id": rest_id, "orders": count} for rest_id, count in favorite_restaurants],
            "cuisine_preferences_from_orders": cuisine_from_orders,
            "last_order_date": max([order["orderTime"] for order in order_history]) if order_history else None
        }
    
    def _analyze_order_history(self, user_id: int) -> Dict[str, Any]:
        """Legacy method - kept for backwards compatibility but will use API"""
        try:
            # Get user orders from API
            user_orders = self._make_api_request(f"/users/{user_id}/orders")
            return self._analyze_order_history_from_api(user_id, user_orders)
        except Exception as e:
            return {"error": f"Could not analyze order history: {str(e)}"}
    
    def _analyze_reviews_from_api(self, user_reviews: List[Dict]) -> Dict[str, Any]:
        """Analyze user's review patterns from API data"""
        if not user_reviews:
            return {"error": "No reviews found"}
        
        ratings = [review["rating"] for review in user_reviews]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Analyze sentiment
        positive_reviews = [r for r in user_reviews if r.get("sentiment") == "positive"]
        
        return {
            "total_reviews": len(user_reviews),
            "avg_rating_given": round(avg_rating, 2),
            "positive_review_rate": len(positive_reviews) / len(user_reviews) if user_reviews else 0,
            "review_frequency": "active" if len(user_reviews) > 5 else "moderate" if len(user_reviews) > 2 else "rare"
        }
    
    def _analyze_reviews(self, user_id: int) -> Dict[str, Any]:
        """Legacy method - analyze user's review patterns using API"""
        try:
            # Get user reviews from API
            user_reviews = self._make_api_request("/reviews", params={"user_id": user_id})
            return self._analyze_reviews_from_api(user_reviews)
        except Exception as e:
            return {"error": f"Could not analyze reviews: {str(e)}"}
    
    def _extract_cuisine_from_api_dishes(self, dishes: List[Dict]) -> List[str]:
        """Extract cuisine types from ordered dishes using API data"""
        cuisines = []
        
        for dish in dishes:
            try:
                # Get restaurant info through the dish's category and menu structure
                # This is a simplified approach - in a real system we might need more API calls
                # For now, we'll use a simple mapping based on dish names and any available restaurant data
                
                dish_name = dish.get("name", "").lower()
                dish_description = dish.get("description", "").lower()
                
                # Simple cuisine detection based on dish names and descriptions
                if any(word in dish_name + " " + dish_description for word in ["pasta", "pizza", "risotto", "italian", "marinara", "parmesan"]):
                    cuisines.append("Italian")
                elif any(word in dish_name + " " + dish_description for word in ["curry", "tandoor", "biryani", "masala", "indian", "naan"]):
                    cuisines.append("Indian")
                elif any(word in dish_name + " " + dish_description for word in ["sushi", "ramen", "tempura", "teriyaki", "japanese", "miso"]):
                    cuisines.append("Japanese")
                elif any(word in dish_name + " " + dish_description for word in ["tacos", "burrito", "quesadilla", "mexican", "salsa", "guacamole"]):
                    cuisines.append("Mexican")
                elif any(word in dish_name + " " + dish_description for word in ["seafood", "fish", "salmon", "shrimp", "lobster", "crab"]):
                    cuisines.append("Seafood")
                elif any(word in dish_name + " " + dish_description for word in ["kebab", "hummus", "falafel", "middle eastern", "shawarma"]):
                    cuisines.append("Middle Eastern")
                elif any(word in dish_name + " " + dish_description for word in ["stir fry", "wok", "dim sum", "chinese", "szechuan"]):
                    cuisines.append("Chinese")
                else:
                    cuisines.append("International")
                    
            except Exception:
                continue  # Skip dishes with missing data
        
        return list(set(cuisines))  # Remove duplicates
    
    def _extract_cuisine_from_dishes(self, dishes: List) -> List[str]:
        """Legacy method - extract cuisine types from dishes using mock_db"""
        # This method is kept for backwards compatibility but should not be used
        # since we're moving to API-based approach
        return self._extract_cuisine_from_api_dishes([])  # Return empty for now
    
    def _generate_profile_summary(self, preferences: Dict, order_analysis: Dict, review_analysis: Dict) -> str:
        """Generate a human-readable profile summary for LLM"""
        summary_parts = []
        
        # Cuisine preferences
        if "cuisine_preferences" in preferences:
            cuisines = preferences["cuisine_preferences"]
            if cuisines:
                summary_parts.append(f"Prefers {', '.join(cuisines)} cuisine")
        
        # Dietary restrictions
        if "dietary_restrictions" in preferences:
            dietary = preferences["dietary_restrictions"]
            if dietary:
                summary_parts.append(f"Dietary needs: {', '.join(dietary)}")
        
        # Price range
        if "price_range" in preferences:
            price_range = preferences["price_range"]
            summary_parts.append(f"Budget range: ${price_range.get('min', 0)/100:.0f}-${price_range.get('max', 10000)/100:.0f}")
        
        # Order patterns
        if "total_orders" in order_analysis and order_analysis["total_orders"] > 0:
            summary_parts.append(f"Has {order_analysis['total_orders']} previous orders")
            
            if "avg_order_value" in order_analysis:
                avg_value = order_analysis["avg_order_value"]
                summary_parts.append(f"Average order value: ${avg_value/100:.0f}")
        
        # Review patterns
        if "avg_rating_given" in review_analysis:
            avg_rating = review_analysis["avg_rating_given"]
            if avg_rating > 4:
                summary_parts.append("Generally rates dishes highly")
            elif avg_rating > 3:
                summary_parts.append("Gives moderate ratings")
        
        return ". ".join(summary_parts) + "." if summary_parts else "Limited profile information available."

# Create global instance with default API URL
user_profile_service = UserProfileService()