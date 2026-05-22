"""
Simple Gemini-only LLM Recommendation Engine
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ Google Generative AI SDK available")
except ImportError as e:
    print(f"❌ Google Generative AI SDK not available: {e}")
    GEMINI_AVAILABLE = False
    genai = None

try:
    from mock_database.data import mock_db
except ImportError:
    # Handle import when running from different directory
    import sys
    sys.path.append('mock_database')
    from data import mock_db

class LLMRecommendationEngine:
    """Gemini-powered recommendation engine using direct Google Generative AI SDK"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Gemini recommendation engine
        
        Args:
            model_name: Specific Gemini model name (optional, uses gemini-2.0-flash)
        """
        self.provider = "gemini"
        self.model = None
        self.model_name = model_name or "gemini-2.0-flash"
        self.temperature = 0.3
        self.max_tokens = 1000
        
        # Initialize Gemini
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini using direct SDK"""
        try:
            if not GEMINI_AVAILABLE or not genai:
                print("❌ Google Generative AI SDK not available")
                self.model = None
                return
                
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment")
                self.model = None
                return
            
            # Configure Gemini with API key
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            print(f"✅ Initialized Gemini with model: {self.model_name}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            print("Will use fallback recommendations.")
            self.model = None

    def get_recommendations(self, user_profile: Dict[str, Any], available_dish_ids: List[int], 
                          context: Optional[Dict[str, Any]] = None, max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Get meal recommendations using Gemini
        
        Args:
            user_profile: Complete user profile from UserProfileService
            available_dish_ids: List of dish IDs to choose from
            context: Optional context (time_of_day, budget_limit, etc.)
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            # Get dish information for available dishes
            available_dishes = self._get_dish_details(available_dish_ids)
            
            if not available_dishes:
                raise ValueError("No valid dishes found in available_dish_ids")
            
            # Generate prompt for Gemini
            prompt = self._create_recommendation_prompt(user_profile, available_dishes, context, max_recommendations)
            
            # Call Gemini API
            if self.model:
                recommendations = self._call_gemini_api(prompt)
            else:
                raise Exception("Gemini model not available")
            
            # Validate and enrich recommendations
            validated_recommendations = self._validate_recommendations(recommendations, available_dishes)
            
            return validated_recommendations[:max_recommendations]
            
        except Exception as e:
            # Return fallback recommendations on error
            print(f"Gemini LLM recommendation failed: {e}")
            return self._fallback_recommendations(available_dish_ids, user_profile, max_recommendations)
    
    def _get_dish_details(self, dish_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information for the available dishes"""
        dishes = []
        
        for dish_id in dish_ids:
            dish = mock_db.dishes.get(dish_id)
            if dish and dish.isAvailable:
                # Get restaurant info
                category = mock_db.menu_categories.get(dish.categoryId)
                restaurant_name = "Unknown"
                if category:
                    menu = mock_db.menus.get(category.menuId)
                    if menu:
                        restaurant = mock_db.restaurants.get(menu.restaurantId)
                        if restaurant:
                            restaurant_name = restaurant.name
                
                dishes.append({
                    "dish_id": dish.id,
                    "name": dish.name,
                    "description": dish.description,
                    "price": dish.price,
                    "restaurant_name": restaurant_name,
                    "preparation_time": dish.preparationTime,
                    "popularity": dish.popularity,
                    "category": category.name if category else "Unknown"
                })
        
        return dishes
    
    def _create_recommendation_prompt(self, user_profile: Dict[str, Any], available_dishes: List[Dict[str, Any]], 
                                    context: Optional[Dict[str, Any]], max_recommendations: int) -> str:
        """Create optimized prompt for Gemini recommendations"""
        
        # Extract key profile information
        profile_summary = user_profile.get("profile_summary", "Limited profile information.")
        preferences = user_profile.get("preferences", {})
        
        # Context information
        context_str = ""
        if context:
            if context.get("time_of_day"):
                context_str += f"Time: {context['time_of_day']}. "
            if context.get("budget_limit"):
                context_str += f"Budget limit: ${context['budget_limit']/100:.0f}. "
        
        # Create dishes list for prompt
        dishes_text = ""
        for i, dish in enumerate(available_dishes, 1):
            dishes_text += f"{i}. {dish['name']} - ${dish['price']/100:.2f}\n"
            dishes_text += f"   Restaurant: {dish['restaurant_name']}\n"
            dishes_text += f"   Description: {dish['description']}\n"
            dishes_text += f"   Category: {dish['category']}, Prep time: {dish['preparation_time']} min\n\n"
        
        prompt = f"""You are an expert meal recommendation system. Recommend {max_recommendations} dishes for this user.

USER PROFILE:
{profile_summary}

PREFERENCES:
- Cuisine preferences: {preferences.get('cuisine_preferences', [])}
- Dietary restrictions: {preferences.get('dietary_restrictions', [])}
- Price range: ${preferences.get('price_range', {}).get('min', 0)/100:.0f} - ${preferences.get('price_range', {}).get('max', 100)/100:.0f}
- Favorite flavors: {preferences.get('favorite_flavors', [])}
- Spice level: {preferences.get('spice_level', 'mild')}

CONTEXT: {context_str}

AVAILABLE DISHES:
{dishes_text}

INSTRUCTIONS:
1. Recommend {max_recommendations} dishes that best match the user's preferences
2. Consider dietary restrictions carefully
3. Respect the budget range
4. Provide variety in your recommendations
5. Give confidence scores (0.0-1.0) based on preference matching

RETURN FORMAT (valid JSON only):
[
  {{
    "dish_id": 1,
    "confidence_score": 0.95,
    "explanation": "Perfect match because..."
  }},
  {{
    "dish_id": 2,
    "confidence_score": 0.82,
    "explanation": "Good choice for..."
  }}
]

Return only the JSON array, no additional text."""

        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_gemini_api(self, prompt: str) -> List[Dict[str, Any]]:
        """Call Gemini API directly"""
        if not self.model:
            raise Exception("Gemini model not initialized")
            
        try:
            # Generate content with Gemini
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Parse JSON response
            try:
                recommendations = json.loads(content)
                return recommendations if isinstance(recommendations, list) else []
            except json.JSONDecodeError:
                # Try to extract JSON from response if there's extra text
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end != 0:
                    json_part = content[start:end]
                    return json.loads(json_part)
                else:
                    raise ValueError("No valid JSON found in Gemini response")
                    
        except Exception as e:
            print(f"Gemini API Error: {e}")
            raise
    
    def _validate_recommendations(self, recommendations: List[Dict[str, Any]], available_dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate Gemini recommendations and enrich with dish details"""
        validated = []
        available_dish_ids = {dish["dish_id"] for dish in available_dishes}
        dish_lookup = {dish["dish_id"]: dish for dish in available_dishes}
        
        for rec in recommendations:
            if isinstance(rec, dict) and "dish_id" in rec:
                dish_id = rec["dish_id"]
                if dish_id in available_dish_ids:
                    dish_info = dish_lookup[dish_id]
                    
                    validated_rec = {
                        "dish_id": dish_id,
                        "dish_name": dish_info["name"],
                        "restaurant_name": dish_info["restaurant_name"],
                        "price": dish_info["price"],
                        "confidence_score": min(max(rec.get("confidence_score", 0.5), 0.0), 1.0),  # Clamp between 0-1
                        "explanation": rec.get("explanation", "Recommended based on your preferences"),
                        "estimated_prep_time": dish_info["preparation_time"],
                        "category": dish_info["category"]
                    }
                    validated.append(validated_rec)
        
        # Sort by confidence score
        validated.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return validated
    
    def _fallback_recommendations(self, available_dish_ids: List[int], user_profile: Dict[str, Any], max_recommendations: int) -> List[Dict[str, Any]]:
        """Provide fallback recommendations when Gemini fails"""
        print("Using fallback recommendation logic")
        
        available_dishes = self._get_dish_details(available_dish_ids)
        
        # Simple fallback: sort by popularity and price preference
        preferences = user_profile.get("preferences", {})
        price_range = preferences.get("price_range", {"min": 0, "max": 10000})
        
        # Filter by price range
        filtered_dishes = [
            dish for dish in available_dishes 
            if price_range["min"] <= dish["price"] <= price_range["max"]
        ]
        
        if not filtered_dishes:
            filtered_dishes = available_dishes  # Use all if none match price range
        
        # Sort by popularity
        filtered_dishes.sort(key=lambda x: x["popularity"], reverse=True)
        
        # Create fallback recommendations
        recommendations = []
        for dish in filtered_dishes[:max_recommendations]:
            recommendations.append({
                "dish_id": dish["dish_id"],
                "dish_name": dish["name"],
                "restaurant_name": dish["restaurant_name"],
                "price": dish["price"],
                "confidence_score": 0.6,  # Moderate confidence for fallback
                "explanation": f"Popular choice ({dish['popularity']}/10 rating) within your budget",
                "estimated_prep_time": dish["preparation_time"],
                "category": dish["category"]
            })
        
        return recommendations

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current Gemini provider"""
        return {
            "provider": self.provider,
            "model": self.model_name,
            "available": self.model is not None,
            "sdk": "google-generativeai" if GEMINI_AVAILABLE else "unavailable"
        }

# Global instance
llm_engine = LLMRecommendationEngine()