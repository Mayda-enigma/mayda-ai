# 🗄️ Database API Endpoints Required for Recommendation System

## 📋 **REQUIRED DATABASE API ENDPOINTS**

Your backend developer needs to implement these REST API endpoints to replace
the mock database:

---

## 🔍 **1. USER PROFILE ENDPOINTS**

### **GET /users/{user_id}**

**Usage**: Get user basic information and embedded preferences

```json
{
  "id": 1,
  "email": "ahmed.belkacem@email.com",
  "phone": 213555001,
  "firstName": "Ahmed",
  "lastName": "Belkacem",
  "role": "CLIENT",
  "isActive": true,
  "embeddedPref": "{\"cuisine_preferences\": [\"Italian\", \"Mediterranean\"], \"dietary_restrictions\": [\"vegetarian_friendly\"], \"price_range\": {\"min\": 800, \"max\": 2000}}",
  "specialinfo": { "age": 28, "occupation": "Engineer" },
  "createdAt": "2024-12-01T10:00:00",
  "updatedAt": "2024-12-01T10:00:00"
}
```

### **GET /users/{user_id}/orders**

**Usage**: Get user's order history for pattern analysis

```json
[
  {
    "id": 1,
    "orderNumber": "ORD000001",
    "userId": 1,
    "restaurantId": 1,
    "type": "DINE_IN",
    "status": "COMPLETED",
    "subtotal": 2500.0,
    "totalAmount": 2500.0,
    "orderTime": "2024-11-15T12:30:00",
    "paymentStatus": "PAID"
  }
]
```

### **GET /orders/{order_id}/items**

**Usage**: Get items within specific orders

```json
[
  {
    "id": 1,
    "orderId": 1,
    "dishId": 6,
    "quantity": 2,
    "unitPrice": 1100.0,
    "totalPrice": 2200.0,
    "createdAt": "2024-11-15T12:30:00"
  }
]
```

### **GET /users/{user_id}/reviews**

**Usage**: Get user's review patterns and ratings

```json
[
  {
    "id": 1,
    "userId": 1,
    "restaurantId": 1,
    "dishId": 6,
    "rating": 5,
    "comment": "Excellent pizza!",
    "sentiment": "positive",
    "sentimentScore": 0.95,
    "isVerified": true,
    "createdAt": "2024-11-16T14:00:00"
  }
]
```

---

## 🍽️ **2. DISH & MENU ENDPOINTS**

### **GET /dishes/{dish_id}**

**Usage**: Get dish details for recommendations

```json
{
  "id": 6,
  "categoryId": 3,
  "name": "Margherita Pizza",
  "description": "Classic pizza with tomato, mozzarella, and basil",
  "price": 1100.0,
  "image": "https://example.com/pizza.jpg",
  "isAvailable": true,
  "preparationTime": 25,
  "popularity": 9.5,
  "createdAt": "2024-10-01T00:00:00"
}
```

### **POST /dishes/batch**

**Usage**: Get multiple dishes at once (performance optimization)

```json
{
  "dish_ids": [1, 6, 12, 22]
}
```

**Response**: Array of dish objects

### **GET /menu-categories/{category_id}**

**Usage**: Get category info to determine cuisine type

```json
{
  "id": 3,
  "menuId": 1,
  "name": "Pizza",
  "description": "Wood-fired pizzas",
  "isActive": true
}
```

### **GET /menus/{menu_id}**

**Usage**: Get menu info to find restaurant

```json
{
  "id": 1,
  "restaurantId": 1,
  "name": "Main Menu",
  "description": "Our signature dishes",
  "isActive": true
}
```

---

## 🏪 **3. RESTAURANT ENDPOINTS**

### **GET /restaurants/{restaurant_id}**

**Usage**: Get restaurant info for recommendations

```json
{
  "id": 1,
  "name": "La Bella Vista",
  "description": "Authentic Italian cuisine",
  "phone": "+213-555-0101",
  "email": "info@labellavista.dz",
  "isActive": true,
  "operatingHours": {
    "monday": { "open": "11:00", "close": "23:00" }
  }
}
```

---

## 🔗 **4. OPTIMIZED COMBINED ENDPOINTS**

### **GET /users/{user_id}/profile-complete**

**Usage**: Get everything needed for recommendations in one call

```json
{
  "user": {
    "id": 1,
    "firstName": "Ahmed",
    "lastName": "Belkacem",
    "embeddedPref": "...",
    "specialinfo": {...}
  },
  "orders": [
    {
      "id": 1,
      "restaurantId": 1,
      "totalAmount": 2500.0,
      "orderTime": "2024-11-15T12:30:00",
      "items": [
        {
          "dishId": 6,
          "quantity": 2,
          "unitPrice": 1100.0
        }
      ]
    }
  ],
  "reviews": [
    {
      "id": 1,
      "restaurantId": 1,
      "rating": 5,
      "sentiment": "positive"
    }
  ]
}
```

### **POST /dishes/details-batch**

**Usage**: Get full dish details with restaurant info

```json
{
  "dish_ids": [1, 6, 12, 22]
}
```

**Response**:

```json
[
  {
    "dish": {
      "id": 6,
      "name": "Margherita Pizza",
      "description": "Classic pizza...",
      "price": 1100.0,
      "preparationTime": 25,
      "popularity": 9.5
    },
    "category": {
      "id": 3,
      "name": "Pizza"
    },
    "restaurant": {
      "id": 1,
      "name": "La Bella Vista"
    }
  }
]
```

---

## ⚡ **5. PERFORMANCE REQUIREMENTS**

### **Response Times**

- **Single record endpoints**: < 100ms
- **Batch endpoints**: < 500ms
- **Complete profile**: < 1000ms

### **Caching Strategy**

- **Dishes**: Cache for 1 hour (prices may change)
- **Users**: Cache for 15 minutes
- **Orders/Reviews**: No caching (real-time data)

### **Pagination**

- **Orders**: Limit to last 50 orders per user
- **Reviews**: Limit to last 20 reviews per user

---

## 🔧 **6. ERROR HANDLING**

### **Standard Error Response**

```json
{
  "error": true,
  "message": "User not found",
  "code": "USER_NOT_FOUND",
  "timestamp": "2024-12-01T10:00:00Z"
}
```

### **Required HTTP Status Codes**

- **200**: Success
- **404**: Not Found (user, dish, etc.)
- **400**: Bad Request (invalid parameters)
- **500**: Server Error

---

## 📊 **7. DATABASE TABLES NEEDED**

Based on the mock database structure:

```sql
-- Core tables the recommendation system accesses:
users (id, email, firstName, lastName, embeddedPref, specialinfo, ...)
orders (id, userId, restaurantId, totalAmount, orderTime, status, ...)
order_items (id, orderId, dishId, quantity, unitPrice, ...)
dishes (id, name, description, price, categoryId, preparationTime, popularity, ...)
menu_categories (id, menuId, name, ...)
menus (id, restaurantId, name, ...)
restaurants (id, name, description, ...)
reviews (id, userId, restaurantId, dishId, rating, comment, sentiment, ...)
```

---

## 🎯 **SUMMARY FOR BACKEND DEVELOPER**

**Required**:

- Implement the 10+ endpoints above
- Handle user profiles, orders, dishes, and reviews
- Support batch operations for performance
- Proper error handling and HTTP status codes

**Optional Optimizations**:

- Combined endpoints for fewer API calls
- Caching strategy for better performance
- Pagination for large datasets

**Testing**: Use the existing mock database as reference for data structure and
API behavior!
