"""
API Client to communicate with external backend
"""
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class BackendAPIClient:
    """Client to communicate with the main backend API"""
    
    def __init__(self):
        self.base_url = settings.BACKEND_API_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        # No authentication needed for mock API
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to backend API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Backend API error: {response.status} - {await response.text()}")
                        return {}
        except Exception as e:
            logger.error(f"Failed to connect to backend API: {e}")
            return {}
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile from backend"""
        return await self._make_request("GET", f"/users/{user_id}/profile")
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences"""
        profile = await self.get_user_profile(user_id)
        return profile.get("preferences", {})
    
    async def get_user_order_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's recent order history"""
        profile = await self.get_user_profile(user_id)
        orders = profile.get("orderHistory", [])
        return orders[-limit:] if orders else []
    
    async def get_dishes(self, 
                        restaurant_id: Optional[int] = None,
                        category_id: Optional[int] = None,
                        available_only: bool = True) -> List[Dict[str, Any]]:
        """Get dishes from backend"""
        params = {}
        if restaurant_id:
            params["restaurant_id"] = restaurant_id
        if category_id:
            params["category_id"] = category_id
        if available_only:
            params["available_only"] = "true"
        
        return await self._make_request("GET", "/dishes", params=params) or []
    
    async def get_dish_by_id(self, dish_id: int) -> Dict[str, Any]:
        """Get specific dish information"""
        return await self._make_request("GET", f"/dishes/{dish_id}")
    
    async def get_restaurants(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get restaurants from backend"""
        params = {"active_only": "true"} if active_only else {}
        return await self._make_request("GET", "/restaurants", params=params) or []
    
    async def get_restaurant_by_id(self, restaurant_id: int) -> Dict[str, Any]:
        """Get specific restaurant information"""
        return await self._make_request("GET", f"/restaurants/{restaurant_id}")
    
    async def get_restaurant_dishes(self, restaurant_id: int) -> List[Dict[str, Any]]:
        """Get all dishes for a specific restaurant"""
        return await self._make_request("GET", f"/restaurants/{restaurant_id}/dishes") or []
    
    async def get_user_reviews(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's reviews"""
        profile = await self.get_user_profile(user_id)
        return profile.get("reviews", [])
    
    async def log_recommendation_interaction(self, user_id: int, dish_id: int, 
                                           interaction_type: str, context: Dict[str, Any] = None):
        """Log user interaction with recommendations back to main system"""
        data = {
            "user_id": user_id,
            "dish_id": dish_id,
            "interaction_type": interaction_type,
            "context": context or {},
            "source": "recommendation_service"
        }
        return await self._make_request("POST", "/analytics/interactions", json=data)

# Global instance
backend_client = BackendAPIClient()