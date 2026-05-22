from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import random

# Enums from your Prisma schema
class UserRole(str, Enum):
    CLIENT = "CLIENT"
    WAITER = "WAITER"
    CHEF = "CHEF"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class OrderType(str, Enum):
    DINE_IN = "DINE_IN"
    TAKEAWAY = "TAKEAWAY"
    DELIVERY = "DELIVERY"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentMethod(str, Enum):
    CASH = "CASH"
    CIB = "CIB"
    EDAHABIA = "EDAHABIA"
    PAYPAL = "PAYPAL"
    STRIPE = "STRIPE"
    GUIDINI_PAY = "GUIDINI_PAY"

class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

class PromotionType(str, Enum):
    DISCOUNT = "DISCOUNT"
    BOGO = "BOGO"
    FREE_DELIVERY = "FREE_DELIVERY"
    HAPPY_HOUR = "HAPPY_HOUR"
    SEASONAL = "SEASONAL"

class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

class InteractionType(str, Enum):
    VIEW = "VIEW"
    LIKE = "LIKE"
    SHARE = "SHARE"
    ORDER = "ORDER"
    REVIEW = "REVIEW"
    SEARCH = "SEARCH"

# Data Models
class User:
    def __init__(self, id: int, email: str = None, phone: int = None, 
                 firstName: str = "", lastName: str = "", role: UserRole = UserRole.CLIENT,
                 isActive: bool = True, password: str = "", embeddedPref: str = None,
                 specialinfo: Dict = None, restaurantId: int = None):
        self.id = id
        self.email = email
        self.phone = phone
        self.firstName = firstName
        self.lastName = lastName
        self.role = role
        self.isActive = isActive
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 365))
        self.updatedAt = datetime.now()
        self.password = password
        self.embeddedPref = embeddedPref
        self.specialinfo = specialinfo or {}
        self.restaurantId = restaurantId

class Address:
    def __init__(self, id: int, userId: int = None, restaurantId: int = None,
                 street: str = "", city: str = "", latitude: float = None,
                 longitude: float = None, isDefault: bool = False):
        self.id = id
        self.userId = userId
        self.restaurantId = restaurantId
        self.street = street
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.isDefault = isDefault
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 100))
        self.updatedAt = datetime.now()

class Restaurant:
    def __init__(self, id: int, name: str, description: str = None, phone: str = "",
                 email: str = None, website: str = None, isActive: bool = True,
                 operatingHours: Dict = None, logo: str = None, coverImage: str = None,
                 gallery: List[str] = None):
        self.id = id
        self.name = name
        self.description = description
        self.phone = phone
        self.email = email
        self.website = website
        self.isActive = isActive
        self.operatingHours = operatingHours or {}
        self.logo = logo
        self.coverImage = coverImage
        self.gallery = gallery or []
        self.createdAt = datetime.now() - timedelta(days=random.randint(30, 365))
        self.updatedAt = datetime.now()

class Menu:
    def __init__(self, id: int, restaurantId: int, name: str, description: str = None,
                 isActive: bool = True, displayOrder: int = 0):
        self.id = id
        self.restaurantId = restaurantId
        self.name = name
        self.description = description
        self.isActive = isActive
        self.displayOrder = displayOrder
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 180))
        self.updatedAt = datetime.now()

class MenuCategory:
    def __init__(self, id: int, menuId: int, name: str, description: str = None,
                 image: str = None, isActive: bool = True, displayOrder: int = 0):
        self.id = id
        self.menuId = menuId
        self.name = name
        self.description = description
        self.image = image
        self.isActive = isActive
        self.displayOrder = displayOrder
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 90))
        self.updatedAt = datetime.now()

class Dish:
    def __init__(self, id: int, categoryId: int, name: str, description: str,
                 price: float, image: str = None, gallery: List[str] = None,
                 isAvailable: bool = True, quantity: int = 100, 
                 preparationTime: int = 15, popularity: float = 0.0, 
                 displayOrder: int = 0):
        self.id = id
        self.categoryId = categoryId
        self.name = name
        self.description = description
        self.price = price
        self.image = image
        self.gallery = gallery or []
        self.isAvailable = isAvailable
        self.quantity = quantity
        self.preparationTime = preparationTime
        self.popularity = popularity
        self.displayOrder = displayOrder
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 90))
        self.updatedAt = datetime.now()

class Order:
    def __init__(self, id: int, orderNumber: str, userId: int = None, 
                 restaurantId: int = 1, tableId: int = None, type: OrderType = OrderType.DINE_IN,
                 status: OrderStatus = OrderStatus.PENDING, subtotal: float = 0.0,
                 deliveryFee: float = 0.0, discount: float = 0.0, totalAmount: float = 0.0,
                 deliveryAddressId: int = None, estimatedDeliveryTime: datetime = None,
                 actualDeliveryTime: datetime = None, paymentStatus: PaymentStatus = PaymentStatus.PENDING,
                 paymentMethod: str = None, notes: str = None):
        self.id = id
        self.orderNumber = orderNumber
        self.userId = userId
        self.restaurantId = restaurantId
        self.tableId = tableId
        self.type = type
        self.status = status
        self.subtotal = subtotal
        self.deliveryFee = deliveryFee
        self.discount = discount
        self.totalAmount = totalAmount
        self.deliveryAddressId = deliveryAddressId
        self.estimatedDeliveryTime = estimatedDeliveryTime
        self.actualDeliveryTime = actualDeliveryTime
        self.paymentStatus = paymentStatus
        self.paymentMethod = paymentMethod
        self.notes = notes
        self.orderTime = datetime.now() - timedelta(days=random.randint(0, 30))
        self.confirmedAt = None
        self.preparedAt = None
        self.readyAt = None
        self.completedAt = None
        self.createdAt = self.orderTime
        self.updatedAt = datetime.now()

class OrderItem:
    def __init__(self, id: int, orderId: int, dishId: int, quantity: int, 
                 unitPrice: float, totalPrice: float, notes: str = None):
        self.id = id
        self.orderId = orderId
        self.dishId = dishId
        self.quantity = quantity
        self.unitPrice = unitPrice
        self.totalPrice = totalPrice
        self.notes = notes
        self.createdAt = datetime.now() - timedelta(days=random.randint(0, 30))

class Review:
    def __init__(self, id: int, userId: int, restaurantId: int, dishId: int = None,
                 rating: int = 5, comment: str = None, sentiment: str = None,
                 sentimentScore: float = None, isVerified: bool = False):
        self.id = id
        self.userId = userId
        self.restaurantId = restaurantId
        self.dishId = dishId
        self.rating = rating
        self.comment = comment
        self.sentiment = sentiment
        self.sentimentScore = sentimentScore
        self.isVerified = isVerified
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 60))
        self.updatedAt = datetime.now()

class Ingredient:
    def __init__(self, id: int, dishId: int, quantity: float):
        self.id = id
        self.dishId = dishId
        self.quantity = quantity

class LoyaltyCard:
    def __init__(self, id: int, userId: int, points: int = 0):
        self.id = id
        self.userId = userId
        self.points = points
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 200))
        self.updatedAt = datetime.now()

class LoyaltyTransaction:
    def __init__(self, id: int, loyaltyCardId: int, restaurantId: int, 
                 points: int, type: str, description: str):
        self.id = id
        self.loyaltyCardId = loyaltyCardId
        self.restaurantId = restaurantId
        self.points = points
        self.type = type
        self.description = description
        self.createdAt = datetime.now() - timedelta(days=random.randint(1, 100))