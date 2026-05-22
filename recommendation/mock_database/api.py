from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our mock database
from data import mock_db, UserRole, OrderStatus, OrderType

# Import recommendation system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from user_profile_service import user_profile_service
from llm_recommendation_engine import llm_engine

app = FastAPI(title="Restaurant Recommendation System Mock API", version="1.0.0")

# Pydantic models for API responses
class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    phone: Optional[int]
    firstName: str
    lastName: str
    role: str
    isActive: bool
    embeddedPref: Optional[str]
    specialinfo: Optional[Dict[str, Any]]
    createdAt: datetime
    updatedAt: datetime

class DishResponse(BaseModel):
    id: int
    categoryId: int
    name: str
    description: str
    price: float
    image: Optional[str]
    gallery: Optional[List[str]]
    isAvailable: bool
    quantity: int
    preparationTime: int
    popularity: float
    displayOrder: int
    createdAt: datetime
    updatedAt: datetime

class RestaurantResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    phone: str
    email: Optional[str]
    website: Optional[str]
    isActive: bool
    operatingHours: Dict[str, Any]
    logo: Optional[str]
    coverImage: Optional[str]
    gallery: Optional[List[str]]
    createdAt: datetime
    updatedAt: datetime

class OrderResponse(BaseModel):
    id: int
    orderNumber: str
    userId: Optional[int]
    restaurantId: int
    type: str
    status: str
    subtotal: float
    deliveryFee: float
    discount: float
    totalAmount: float
    paymentStatus: str
    orderTime: datetime
    createdAt: datetime
    updatedAt: datetime

class OrderItemResponse(BaseModel):
    id: int
    orderId: int
    dishId: int
    quantity: int
    unitPrice: float
    totalPrice: float
    notes: Optional[str]
    createdAt: datetime

class ReviewResponse(BaseModel):
    id: int
    userId: int
    restaurantId: int
    dishId: Optional[int]
    rating: int
    comment: Optional[str]
    sentiment: Optional[str]
    sentimentScore: Optional[float]
    isVerified: bool
    createdAt: datetime
    updatedAt: datetime

class UserProfileResponse(BaseModel):
    user: UserResponse
    preferences: Optional[Dict[str, Any]]
    orderHistory: List[OrderResponse]
    reviews: List[ReviewResponse]
    loyaltyPoints: Optional[int]

# New models for smart recommendations
class SmartRecommendationRequest(BaseModel):
    user_id: int
    available_dish_ids: List[int]
    context: Optional[Dict[str, Any]] = None
    max_recommendations: int = 5

class SmartRecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[Dict[str, Any]]
    context_used: Optional[str]
    generated_at: str
    total_available_dishes: int

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Restaurant Recommendation System Mock API", 
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "restaurants": "/restaurants", 
            "dishes": "/dishes",
            "orders": "/orders",
            "reviews": "/reviews",
            "user_profile": "/users/{user_id}/profile",
            "restaurant_dishes": "/restaurants/{restaurant_id}/dishes",
            "user_orders": "/users/{user_id}/orders",
            "recommendations": "/users/{user_id}/recommendations"
        }
    }

@app.get("/users", response_model=List[UserResponse])
async def get_users():
    """Get all users"""
    users = []
    for user in mock_db.users.values():
        users.append(UserResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
            firstName=user.firstName,
            lastName=user.lastName,
            role=user.role.value,
            isActive=user.isActive,
            embeddedPref=user.embeddedPref,
            specialinfo=user.specialinfo,
            createdAt=user.createdAt,
            updatedAt=user.updatedAt
        ))
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a specific user by ID"""
    if user_id not in mock_db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = mock_db.users[user_id]
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        firstName=user.firstName,
        lastName=user.lastName,
        role=user.role.value,
        isActive=user.isActive,
        embeddedPref=user.embeddedPref,
        specialinfo=user.specialinfo,
        createdAt=user.createdAt,
        updatedAt=user.updatedAt
    )

@app.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: int):
    """Get comprehensive user profile with preferences, history, and loyalty points"""
    if user_id not in mock_db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = mock_db.users[user_id]
    
    # Parse embedded preferences
    preferences = None
    if user.embeddedPref:
        try:
            preferences = json.loads(user.embeddedPref)
        except json.JSONDecodeError:
            preferences = None
    
    # Get user's orders
    user_orders = [
        OrderResponse(
            id=order.id,
            orderNumber=order.orderNumber,
            userId=order.userId,
            restaurantId=order.restaurantId,
            type=order.type.value,
            status=order.status.value,
            subtotal=order.subtotal,
            deliveryFee=order.deliveryFee,
            discount=order.discount,
            totalAmount=order.totalAmount,
            paymentStatus=order.paymentStatus.value,
            orderTime=order.orderTime,
            createdAt=order.createdAt,
            updatedAt=order.updatedAt
        )
        for order in mock_db.orders.values() if order.userId == user_id
    ]
    
    # Get user's reviews
    user_reviews = [
        ReviewResponse(
            id=review.id,
            userId=review.userId,
            restaurantId=review.restaurantId,
            dishId=review.dishId,
            rating=review.rating,
            comment=review.comment,
            sentiment=review.sentiment,
            sentimentScore=review.sentimentScore,
            isVerified=review.isVerified,
            createdAt=review.createdAt,
            updatedAt=review.updatedAt
        )
        for review in mock_db.reviews.values() if review.userId == user_id
    ]
    
    # Get loyalty points
    loyalty_points = None
    if user_id in mock_db.loyalty_cards:
        loyalty_points = mock_db.loyalty_cards[user_id].points
    
    return UserProfileResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
            firstName=user.firstName,
            lastName=user.lastName,
            role=user.role.value,
            isActive=user.isActive,
            embeddedPref=user.embeddedPref,
            specialinfo=user.specialinfo,
            createdAt=user.createdAt,
            updatedAt=user.updatedAt
        ),
        preferences=preferences,
        orderHistory=user_orders,
        reviews=user_reviews,
        loyaltyPoints=loyalty_points
    )

@app.get("/restaurants", response_model=List[RestaurantResponse])
async def get_restaurants(active_only: bool = Query(True, description="Filter by active restaurants only")):
    """Get all restaurants"""
    restaurants = []
    for restaurant in mock_db.restaurants.values():
        if not active_only or restaurant.isActive:
            restaurants.append(RestaurantResponse(
                id=restaurant.id,
                name=restaurant.name,
                description=restaurant.description,
                phone=restaurant.phone,
                email=restaurant.email,
                website=restaurant.website,
                isActive=restaurant.isActive,
                operatingHours=restaurant.operatingHours,
                logo=restaurant.logo,
                coverImage=restaurant.coverImage,
                gallery=restaurant.gallery,
                createdAt=restaurant.createdAt,
                updatedAt=restaurant.updatedAt
            ))
    return restaurants

@app.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: int):
    """Get a specific restaurant by ID"""
    if restaurant_id not in mock_db.restaurants:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    restaurant = mock_db.restaurants[restaurant_id]
    return RestaurantResponse(
        id=restaurant.id,
        name=restaurant.name,
        description=restaurant.description,
        phone=restaurant.phone,
        email=restaurant.email,
        website=restaurant.website,
        isActive=restaurant.isActive,
        operatingHours=restaurant.operatingHours,
        logo=restaurant.logo,
        coverImage=restaurant.coverImage,
        gallery=restaurant.gallery,
        createdAt=restaurant.createdAt,
        updatedAt=restaurant.updatedAt
    )

@app.get("/dishes", response_model=List[DishResponse])
async def get_dishes(
    restaurant_id: Optional[int] = Query(None, description="Filter dishes by restaurant"),
    available_only: bool = Query(True, description="Filter by available dishes only"),
    category_id: Optional[int] = Query(None, description="Filter by menu category")
):
    """Get all dishes with optional filters"""
    dishes = []
    
    for dish in mock_db.dishes.values():
        # Apply filters
        if available_only and not dish.isAvailable:
            continue
            
        if category_id and dish.categoryId != category_id:
            continue
            
        if restaurant_id:
            # Find the category and menu to check restaurant
            category = mock_db.menu_categories.get(dish.categoryId)
            if not category:
                continue
            menu = mock_db.menus.get(category.menuId)
            if not menu or menu.restaurantId != restaurant_id:
                continue
        
        dishes.append(DishResponse(
            id=dish.id,
            categoryId=dish.categoryId,
            name=dish.name,
            description=dish.description,
            price=dish.price,
            image=dish.image,
            gallery=dish.gallery,
            isAvailable=dish.isAvailable,
            quantity=dish.quantity,
            preparationTime=dish.preparationTime,
            popularity=dish.popularity,
            displayOrder=dish.displayOrder,
            createdAt=dish.createdAt,
            updatedAt=dish.updatedAt
        ))
    
    return dishes

@app.get("/restaurants/{restaurant_id}/dishes", response_model=List[DishResponse])
async def get_restaurant_dishes(restaurant_id: int, available_only: bool = Query(True)):
    """Get all dishes for a specific restaurant"""
    if restaurant_id not in mock_db.restaurants:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return await get_dishes(restaurant_id=restaurant_id, available_only=available_only)

@app.get("/dishes/{dish_id}", response_model=DishResponse)
async def get_dish(dish_id: int):
    """Get a specific dish by ID"""
    if dish_id not in mock_db.dishes:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    dish = mock_db.dishes[dish_id]
    return DishResponse(
        id=dish.id,
        categoryId=dish.categoryId,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        image=dish.image,
        gallery=dish.gallery,
        isAvailable=dish.isAvailable,
        quantity=dish.quantity,
        preparationTime=dish.preparationTime,
        popularity=dish.popularity,
        displayOrder=dish.displayOrder,
        createdAt=dish.createdAt,
        updatedAt=dish.updatedAt
    )

@app.get("/orders", response_model=List[OrderResponse])
async def get_orders(user_id: Optional[int] = Query(None, description="Filter orders by user")):
    """Get all orders with optional user filter"""
    orders = []
    for order in mock_db.orders.values():
        if user_id and order.userId != user_id:
            continue
            
        orders.append(OrderResponse(
            id=order.id,
            orderNumber=order.orderNumber,
            userId=order.userId,
            restaurantId=order.restaurantId,
            type=order.type.value,
            status=order.status.value,
            subtotal=order.subtotal,
            deliveryFee=order.deliveryFee,
            discount=order.discount,
            totalAmount=order.totalAmount,
            paymentStatus=order.paymentStatus.value,
            orderTime=order.orderTime,
            createdAt=order.createdAt,
            updatedAt=order.updatedAt
        ))
    return orders

@app.get("/users/{user_id}/orders", response_model=List[OrderResponse])
async def get_user_orders(user_id: int):
    """Get all orders for a specific user"""
    if user_id not in mock_db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await get_orders(user_id=user_id)

@app.get("/orders/{order_id}/items", response_model=List[OrderItemResponse])
async def get_order_items(order_id: int):
    """Get all items for a specific order"""
    if order_id not in mock_db.orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = [
        OrderItemResponse(
            id=item.id,
            orderId=item.orderId,
            dishId=item.dishId,
            quantity=item.quantity,
            unitPrice=item.unitPrice,
            totalPrice=item.totalPrice,
            notes=item.notes,
            createdAt=item.createdAt
        )
        for item in mock_db.order_items.values() if item.orderId == order_id
    ]
    return items

@app.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    user_id: Optional[int] = Query(None, description="Filter reviews by user"),
    restaurant_id: Optional[int] = Query(None, description="Filter reviews by restaurant"),
    dish_id: Optional[int] = Query(None, description="Filter reviews by dish")
):
    """Get all reviews with optional filters"""
    reviews = []
    for review in mock_db.reviews.values():
        if user_id and review.userId != user_id:
            continue
        if restaurant_id and review.restaurantId != restaurant_id:
            continue
        if dish_id and review.dishId != dish_id:
            continue
            
        reviews.append(ReviewResponse(
            id=review.id,
            userId=review.userId,
            restaurantId=review.restaurantId,
            dishId=review.dishId,
            rating=review.rating,
            comment=review.comment,
            sentiment=review.sentiment,
            sentimentScore=review.sentimentScore,
            isVerified=review.isVerified,
            createdAt=review.createdAt,
            updatedAt=review.updatedAt
        ))
    return reviews

def _get_filtered_dishes(restaurant_id: Optional[int] = None, available_only: bool = True, category_id: Optional[int] = None):
    """Helper function to get filtered dishes"""
    dishes = []
    
    for dish in mock_db.dishes.values():
        # Apply filters
        if available_only and not dish.isAvailable:
            continue
            
        if category_id and dish.categoryId != category_id:
            continue
            
        if restaurant_id:
            # Find the category and menu to check restaurant
            category = mock_db.menu_categories.get(dish.categoryId)
            if not category:
                continue
            menu = mock_db.menus.get(category.menuId)
            if not menu or menu.restaurantId != restaurant_id:
                continue
        
        dishes.append(dish)
    
    return dishes

@app.get("/users/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: int,
    restaurant_id: Optional[int] = Query(None, description="Filter recommendations by restaurant"),
    limit: int = Query(5, description="Number of recommendations to return")
):
    """Get meal recommendations for a user (placeholder for actual recommendation engine)"""
    if user_id not in mock_db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # This is a placeholder - in the real system, this would call the LLM recommendation engine
    # For now, return popular dishes that match user preferences
    
    user = mock_db.users[user_id]
    preferences = {}
    if user.embeddedPref:
        try:
            preferences = json.loads(user.embeddedPref)
        except json.JSONDecodeError:
            preferences = {}
    
    # Get dishes (filtered by restaurant if specified)
    dishes = _get_filtered_dishes(restaurant_id=restaurant_id, available_only=True)
    
    # Simple recommendation logic: sort by popularity and return top dishes
    # In real implementation, this would use LLM with user preferences
    recommended_dishes = sorted(dishes, key=lambda x: x.popularity, reverse=True)[:limit]
    
    return {
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "user_preferences": preferences,
        "recommendations": [
            {
                "dish": {
                    "id": dish.id,
                    "name": dish.name,
                    "description": dish.description,
                    "price": dish.price,
                    "popularity": dish.popularity,
                    "preparationTime": dish.preparationTime,
                    "isAvailable": dish.isAvailable
                },
                "confidence_score": min(dish.popularity / 10, 1.0),
                "explanation": f"Recommended based on high popularity ({dish.popularity}/10) and your preferences"
            }
            for dish in recommended_dishes
        ],
        "generated_at": datetime.now().isoformat()
    }

@app.post("/smart-recommendations", response_model=SmartRecommendationResponse)
async def get_smart_recommendations(request: SmartRecommendationRequest):
    """
    Get intelligent meal recommendations using LLM
    
    Body:
    {
        "user_id": 1,
        "available_dish_ids": [1, 2, 3, 4, 5],
        "context": {
            "time_of_day": "lunch",
            "budget_limit": 2000
        },
        "max_recommendations": 5
    }
    """
    try:
        # Validate user exists
        if request.user_id not in mock_db.users:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate dish IDs exist
        valid_dish_ids = [dish_id for dish_id in request.available_dish_ids if dish_id in mock_db.dishes]
        if not valid_dish_ids:
            raise HTTPException(status_code=400, detail="No valid dish IDs provided")
        
        # Get user profile
        try:
            user_profile = user_profile_service.get_user_profile(request.user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing user profile: {str(e)}")
        
        # Get LLM recommendations
        try:
            recommendations = llm_engine.get_recommendations(
                user_profile=user_profile,
                available_dish_ids=valid_dish_ids,
                context=request.context,
                max_recommendations=request.max_recommendations
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")
        
        # Prepare context description
        context_desc = "General recommendations"
        if request.context:
            context_parts = []
            if request.context.get("time_of_day"):
                context_parts.append(f"{request.context['time_of_day']} time")
            if request.context.get("budget_limit"):
                context_parts.append(f"budget under ${request.context['budget_limit']/100:.0f}")
            if context_parts:
                context_desc = f"Recommendations for {', '.join(context_parts)}"
        
        return SmartRecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            context_used=context_desc,
            generated_at=datetime.now().isoformat(),
            total_available_dishes=len(valid_dish_ids)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/users/{user_id}/smart-recommendations")
async def get_user_smart_recommendations(
    user_id: int,
    available_dish_ids: str = Query(..., description="Comma-separated list of dish IDs"),
    time_of_day: Optional[str] = Query(None, description="breakfast, lunch, or dinner"),
    budget_limit: Optional[int] = Query(None, description="Maximum budget in cents"),
    max_recommendations: int = Query(5, description="Maximum number of recommendations")
):
    """
    GET endpoint for smart recommendations
    Example: /users/1/smart-recommendations?available_dish_ids=1,2,3,4,5&time_of_day=lunch&budget_limit=2000
    """
    try:
        # Parse dish IDs
        dish_ids = [int(x.strip()) for x in available_dish_ids.split(",") if x.strip().isdigit()]
        if not dish_ids:
            raise HTTPException(status_code=400, detail="No valid dish IDs provided")
        
        # Build context
        context = {}
        if time_of_day:
            context["time_of_day"] = time_of_day
        if budget_limit:
            context["budget_limit"] = budget_limit
        
        # Create request object
        request = SmartRecommendationRequest(
            user_id=user_id,
            available_dish_ids=dish_ids,
            context=context if context else None,
            max_recommendations=max_recommendations
        )
        
        return await get_smart_recommendations(request)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dish IDs format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_summary": {
            "users": len(mock_db.users),
            "restaurants": len(mock_db.restaurants),
            "dishes": len(mock_db.dishes),
            "orders": len(mock_db.orders),
            "reviews": len(mock_db.reviews)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)