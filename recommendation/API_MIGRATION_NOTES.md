# User Profile Service - API Migration

## Overview

The `UserProfileService` has been updated to use HTTP API calls instead of
directly accessing the mock database. This change provides better separation of
concerns and makes the service more suitable for distributed systems.

## Changes Made

### 1. Import Changes

- Removed direct import of `mock_db`
- Added `requests` library for HTTP API calls

### 2. Class Structure Updates

- Added `api_base_url` parameter to constructor (defaults to
  `http://localhost:8000`)
- Added `_make_api_request()` helper method for consistent API interactions
- Added error handling for API request failures

### 3. Method Updates

- `get_user_profile()`: Now uses `/users/{user_id}` and
  `/users/{user_id}/profile` API endpoints
- `_analyze_order_history()`: Uses `/users/{user_id}/orders` and
  `/orders/{order_id}/items` endpoints
- `_analyze_reviews()`: Uses `/reviews?user_id={user_id}` endpoint
- `_extract_cuisine_from_dishes()`: Updated to work with API dish data
  structures

### 4. New Methods

- `_make_api_request()`: Centralized API request handling with error management
- `_analyze_order_history_from_api()`: Processes order data from API responses
- `_analyze_reviews_from_api()`: Processes review data from API responses
- `_extract_cuisine_from_api_dishes()`: Intelligent cuisine detection from dish
  names/descriptions

## API Endpoints Used

| Method | Endpoint                     | Purpose                                           |
| ------ | ---------------------------- | ------------------------------------------------- |
| GET    | `/users/{user_id}`           | Get basic user information                        |
| GET    | `/users/{user_id}/profile`   | Get complete user profile with orders and reviews |
| GET    | `/users/{user_id}/orders`    | Get user's order history                          |
| GET    | `/orders/{order_id}/items`   | Get items for a specific order                    |
| GET    | `/reviews?user_id={user_id}` | Get user's reviews                                |
| GET    | `/dishes/{dish_id}`          | Get dish details                                  |

## Usage

### Basic Usage

```python
from user_profile_service import UserProfileService

# Use default API URL (http://localhost:8000)
service = UserProfileService()

# Or specify custom API URL
service = UserProfileService("http://api.example.com:8080")

# Get user profile
profile = service.get_user_profile(user_id=1)
```

### Profile Structure

The returned profile includes:

- `user_id`: The requested user ID
- `basic_info`: Name, role, and special information
- `preferences`: Parsed embedded preferences (cuisine, dietary restrictions,
  etc.)
- `order_history`: Analysis of ordering patterns and favorite dishes/restaurants
- `review_patterns`: Review frequency and rating tendencies
- `profile_summary`: Human-readable summary for LLM consumption

## Error Handling

The service now includes comprehensive error handling:

- API connection failures
- Invalid user IDs (404 responses)
- Malformed JSON in embedded preferences
- Missing order/review data

## Dependencies

Added `requests>=2.28.0` to requirements.txt for HTTP API calls.

## Testing

Run the test script to verify functionality:

```bash
python test_api_user_profile.py
```

**Note**: The API server must be running for the service to work:

```bash
python mock_database/api.py
```

## Migration Benefits

1. **Separation of Concerns**: Service no longer directly accesses database
   structures
2. **Network Ready**: Can work across different services and containers
3. **Error Isolation**: API failures don't crash the entire application
4. **Consistency**: Uses same endpoints as other API consumers
5. **Scalability**: Supports load balancing and API versioning
