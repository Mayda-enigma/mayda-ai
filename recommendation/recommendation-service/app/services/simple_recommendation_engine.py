"""
Simplified recommendation engine that works without database
Only uses external API calls to get data and LLM for recommendations
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from app.core.config import settings
from app.services.backend_client import backend_client

# Import LLM clients
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger(__name__)

class SimplifiedRecommendationEngine:
    """Stateless recommendation engine that relies on external API only"""
    
    def __init__(self):
        self.model = None
        self.provider = "none"
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on available APIs"""
        if settings.GEMINI_API_KEY and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.LLM_MODEL)
                self.provider = "gemini"
                logger.info(f"✅ Initialized Gemini with model: {settings.LLM_MODEL}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {e}")
        
        elif settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            try:
                openai.api_key = settings.OPENAI_API_KEY
                self.provider = "openai"
                logger.info("✅ Initialized OpenAI")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
        
        if self.provider == "none":
            logger.warning("⚠️ No LLM provider available, using fallback recommendations")
    
    async def get_recommendations(self,
                                 user_id: int,
                                 context: Dict[str, Any] = None,
                                 restaurant_id: Optional[int] = None,
                                 limit: int = 5) -> Dict[str, Any]:
        """Get AI-powered recommendations for a user"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Getting recommendations for user {user_id}")
            
            # Get user profile from external API
            user_profile = await self._get_user_profile_from_api(user_id)
            if not user_profile:
                logger.error(f"❌ Could not get user profile for user {user_id}")
                return {"user_id": user_id, "recommendations": [], "error": "User not found"}
            
            logger.info(f"✅ Got user profile for {user_profile.get('name', 'Unknown')}")
            
            # Get available dishes from external API
            dishes = await self._get_dishes_from_api(restaurant_id)
            if not dishes:
                logger.error("❌ No dishes available from backend API")
                return {"user_id": user_id, "recommendations": [], "error": "No dishes available"}
            
            logger.info(f"✅ Got {len(dishes)} dishes from backend API")
            
            # Generate recommendations using LLM or fallback
            if self.provider != "none":
                recommendations = await self._generate_llm_recommendations(
                    user_profile, dishes, context, limit
                )
                logger.info(f"✅ Generated {len(recommendations)} LLM recommendations")
            else:
                recommendations = self._generate_fallback_recommendations(
                    user_profile, dishes, limit
                )
                logger.info(f"✅ Generated {len(recommendations)} fallback recommendations")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "user_id": user_id,
                "recommendations": recommendations,
                "context": context,
                "restaurant_id": restaurant_id,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.provider,
                "processing_time": processing_time,
                "total_available_dishes": len(dishes),
                "backend_api_url": settings.BACKEND_API_URL
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "recommendations": [],
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def _get_user_profile_from_api(self, user_id: int) -> Dict[str, Any]:
        """Get user profile from external backend API"""
        try:
            # Get basic user info
            user_response = await backend_client.get_user_profile(user_id)
            if not user_response:
                logger.error(f"❌ No user data from API for user {user_id}")
                return {}
            
            logger.info(f"✅ Retrieved user profile from API: {user_response.get('user', {}).get('firstName', 'Unknown')}")
            
            # Extract user preferences
            preferences = user_response.get('preferences', {})
            order_history = user_response.get('orderHistory', [])
            reviews = user_response.get('reviews', [])
            
            # Create comprehensive profile
            profile = {
                "user_id": user_id,
                "name": f"{user_response.get('user', {}).get('firstName', '')} {user_response.get('user', {}).get('lastName', '')}".strip(),
                "preferences": preferences,
                "order_history": order_history[-10:],  # Last 10 orders
                "reviews": reviews[-5:],  # Last 5 reviews
                "total_orders": len(order_history),
                "total_reviews": len(reviews),
                "loyalty_points": user_response.get('loyaltyPoints', 0)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error getting user profile from API: {e}")
            return {}
    
    async def _get_dishes_from_api(self, restaurant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get dishes from external backend API"""
        try:
            if restaurant_id:
                logger.info(f"🍽️ Getting dishes for restaurant {restaurant_id}")
                dishes = await backend_client.get_restaurant_dishes(restaurant_id)
            else:
                logger.info("🍽️ Getting all available dishes")
                dishes = await backend_client.get_dishes()
            
            # Filter for available dishes only
            available_dishes = [dish for dish in dishes if dish.get('isAvailable', True)]
            
            logger.info(f"✅ Got {len(available_dishes)} available dishes (out of {len(dishes)} total)")
            
            return available_dishes
            
        except Exception as e:
            logger.error(f"❌ Error getting dishes from API: {e}")
            return []
    
    async def _generate_llm_recommendations(self,
                                          user_profile: Dict[str, Any],
                                          dishes: List[Dict[str, Any]],
                                          context: Dict[str, Any],
                                          limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations using LLM"""
        try:
            # Build the prompt
            prompt = self._build_recommendation_prompt(user_profile, dishes, context, limit)
            
            logger.info(f"🤖 Querying {self.provider} for recommendations")
            
            # Get LLM response
            if self.provider == "gemini":
                response = await self._query_gemini(prompt)
            elif self.provider == "openai":
                response = await self._query_openai(prompt)
            else:
                return []
            
            if not response:
                logger.warning("⚠️ Empty response from LLM, using fallback")
                return self._generate_fallback_recommendations(user_profile, dishes, limit)
            
            # Parse the response
            recommendations = self._parse_llm_response(response, dishes)
            
            if not recommendations:
                logger.warning("⚠️ Failed to parse LLM response, using fallback")
                return self._generate_fallback_recommendations(user_profile, dishes, limit)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"❌ LLM recommendation generation failed: {e}")
            return self._generate_fallback_recommendations(user_profile, dishes, limit)
    
    def _build_recommendation_prompt(self,
                                   user_profile: Dict[str, Any],
                                   dishes: List[Dict[str, Any]],
                                   context: Dict[str, Any],
                                   limit: int) -> str:
        """Build prompt for LLM recommendation"""
        
        # Extract key user info
        preferences = user_profile.get('preferences', {})
        recent_orders = user_profile.get('order_history', [])
        reviews = user_profile.get('reviews', [])
        
        # Simplify dishes for the prompt (to avoid token limits)
        simplified_dishes = []
        for dish in dishes[:50]:  # Limit to 50 dishes to avoid token limits
            simplified_dishes.append({
                "id": dish.get("id"),
                "name": dish.get("name"),
                "description": dish.get("description", "")[:100],  # Truncate description
                "price": dish.get("price"),
                "popularity": dish.get("popularity", 0),
                "categoryId": dish.get("categoryId")
            })
        
        prompt = f"""
You are a restaurant recommendation expert. Recommend {limit} dishes for this user.

USER PROFILE:
- Name: {user_profile.get('name')}
- Preferences: {json.dumps(preferences)}
- Total Orders: {user_profile.get('total_orders', 0)}
- Recent Orders: {len(recent_orders)} recent orders
- Reviews Written: {len(reviews)}

CONTEXT: {json.dumps(context or {})}

AVAILABLE DISHES ({len(simplified_dishes)} dishes):
{json.dumps(simplified_dishes, indent=2)}

Respond ONLY with a JSON array of recommendations:
[
  {{
    "dish_id": 1,
    "confidence_score": 0.95,
    "explanation": "Perfect for your Italian preferences and past orders"
  }},
  ...
]

Consider user preferences, dietary restrictions, price range, and context.
"""
        
        return prompt
    
    async def _query_gemini(self, prompt: str) -> str:
        """Query Gemini model"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"❌ Gemini query failed: {e}")
            return ""
    
    async def _query_openai(self, prompt: str) -> str:
        """Query OpenAI model"""
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ OpenAI query failed: {e}")
            return ""
    
    def _parse_llm_response(self, response: str, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse LLM response into recommendation format"""
        try:
            # Try to extract JSON from the response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "[" in response and "]" in response:
                json_start = response.find("[")
                json_end = response.rfind("]") + 1
                json_str = response[json_start:json_end]
            else:
                json_str = response.strip()
            
            response_data = json.loads(json_str)
            if not isinstance(response_data, list):
                logger.error("❌ LLM response is not a list")
                return []
            
            # Create dish lookup
            dish_lookup = {dish["id"]: dish for dish in dishes}
            
            recommendations = []
            for item in response_data:
                dish_id = item.get("dish_id")
                if dish_id and dish_id in dish_lookup:
                    dish = dish_lookup[dish_id]
                    recommendations.append({
                        "dish": {
                            "id": dish["id"],
                            "name": dish["name"],
                            "description": dish.get("description", ""),
                            "price": dish["price"],
                            "popularity": dish.get("popularity", 0),
                            "isAvailable": dish.get("isAvailable", True),
                            "categoryId": dish.get("categoryId")
                        },
                        "confidence_score": min(max(float(item.get("confidence_score", 0.5)), 0), 1),
                        "explanation": item.get("explanation", "Recommended based on your preferences"),
                        "source": "llm"
                    })
            
            logger.info(f"✅ Parsed {len(recommendations)} recommendations from LLM response")
            return recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            return []
        except Exception as e:
            logger.error(f"❌ Error parsing LLM response: {e}")
            return []
    
    def _generate_fallback_recommendations(self,
                                         user_profile: Dict[str, Any],
                                         dishes: List[Dict[str, Any]],
                                         limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations using rule-based fallback"""
        try:
            logger.info("🔄 Using fallback recommendation algorithm")
            
            preferences = user_profile.get("preferences", {})
            price_range = preferences.get("price_range", {})
            max_price = price_range.get("max", float('inf'))
            min_price = price_range.get("min", 0)
            cuisine_prefs = preferences.get("cuisine_preferences", [])
            
            # Score dishes based on simple rules
            scored_dishes = []
            for dish in dishes:
                if not dish.get("isAvailable", True):
                    continue
                
                price = dish.get("price", 0)
                if price > max_price or price < min_price:
                    continue
                
                # Base score from popularity
                score = dish.get("popularity", 0) / 10.0
                
                # Boost score for price fit
                if min_price <= price <= max_price * 0.8:
                    score += 0.2
                
                # Boost for cuisine preferences (simple name matching)
                dish_name = dish.get("name", "").lower()
                dish_desc = dish.get("description", "").lower()
                for cuisine in cuisine_prefs:
                    if cuisine.lower() in dish_name or cuisine.lower() in dish_desc:
                        score += 0.3
                        break
                
                scored_dishes.append({
                    "dish": dish,
                    "score": min(score, 1.0)
                })
            
            # Sort by score and return top recommendations
            scored_dishes.sort(key=lambda x: x["score"], reverse=True)
            
            recommendations = []
            for item in scored_dishes[:limit]:
                dish = item["dish"]
                recommendations.append({
                    "dish": {
                        "id": dish["id"],
                        "name": dish["name"],
                        "description": dish.get("description", ""),
                        "price": dish["price"],
                        "popularity": dish.get("popularity", 0),
                        "isAvailable": dish.get("isAvailable", True),
                        "categoryId": dish.get("categoryId")
                    },
                    "confidence_score": item["score"],
                    "explanation": f"Popular choice (score: {item['score']:.2f}) matching your preferences",
                    "source": "fallback"
                })
            
            logger.info(f"✅ Generated {len(recommendations)} fallback recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Fallback recommendation generation failed: {e}")
            return []

# Global instance
recommendation_engine = SimplifiedRecommendationEngine()