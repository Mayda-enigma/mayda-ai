# Meal Recommendation System - Implementation Instructions

## Overview

Build a fast and simple recommendation system for meals that leverages:

- User's embedded preferences (`embeddedPref` field)
- Purchase history (orders and order items)
- LLM for intelligent recommendations
- Real-time dish popularity and availability

## System Architecture

### 1. Data Sources

- **User Preferences**: `embeddedPref` field (JSON containing user taste
  preferences)
- **Purchase History**: Orders → OrderItems → Dishes relationship
- **Dish Information**: Name, description, ingredients, price, popularity
- **User Reviews**: Ratings and sentiment analysis for dishes
- **Context**: Time of day, restaurant, user's special info

### 2. Recommendation Engine Components

#### A. User Profile Builder

- **Input**: User ID
- **Process**:
  - Extract embedded preferences from `embeddedPref` field
  - Analyze purchase history (frequently ordered dishes, categories, price
    range)
  - Calculate average rating given by user
  - Extract dietary restrictions from `specialinfo` JSON field
- **Output**: Comprehensive user profile JSON

#### B. Dish Feature Extractor

- **Input**: Dish ID or Restaurant ID
- **Process**:
  - Compile dish metadata (name, description, ingredients, price)
  - Calculate popularity score and recent order frequency
  - Extract cuisine type and dietary tags
  - Include availability status and preparation time
- **Output**: Structured dish feature set

#### C. LLM-Powered Recommendation Engine

- **Model**: Use OpenAI GPT-4 or similar LLM
- **Input**: User profile + Available dishes + Context (time, location)
- **Process**:
  - Generate personalized recommendations based on:
    - Taste preferences and dietary restrictions
    - Purchase history patterns
    - Similar users' preferences (collaborative filtering)
    - Seasonal and time-based preferences
    - Budget considerations
- **Output**: Ranked list of recommended dishes with explanations

### 3. Implementation Strategy

#### Phase 1: Core Recommendation Engine (Week 1)

1. **User Profile Service**

   - Extract and structure user preferences
   - Build purchase history analysis
   - Cache user profiles for performance

2. **Dish Indexing Service**

   - Create searchable dish database
   - Update popularity scores regularly
   - Handle availability status

3. **Basic LLM Integration**
   - Design prompt templates for recommendations
   - Implement API calls to LLM provider
   - Parse and rank recommendations

#### Phase 2: Advanced Features (Week 2)

1. **Context-Aware Recommendations**

   - Time-based suggestions (breakfast, lunch, dinner)
   - Weather-based recommendations
   - Special occasion suggestions

2. **Real-time Learning**

   - Update user preferences based on new orders
   - A/B testing for recommendation strategies
   - Feedback loop integration

3. **Performance Optimization**
   - Implement caching strategies
   - Batch processing for multiple users
   - Response time optimization

### 4. Technical Stack

#### Backend Framework

- **Python FastAPI** for REST API
- **Prisma Client** for database operations
- **Redis** for caching user profiles and recommendations
- **OpenAI API** or **Anthropic Claude** for LLM integration

#### Database Optimizations

- Index on frequently queried fields
- Materialized views for user statistics
- Cached aggregations for dish popularity

#### API Endpoints

```
GET /recommendations/{user_id}
POST /recommendations/batch
PUT /recommendations/feedback
GET /recommendations/similar-users/{user_id}
```

### 5. Recommendation Algorithm Flow

```
1. Receive recommendation request (user_id, restaurant_id?, context?)
2. Load user profile from cache or build fresh
3. Get available dishes (filtered by restaurant, availability)
4. Prepare LLM prompt with:
   - User preferences and history
   - Available dishes with features
   - Current context (time, weather, etc.)
5. Call LLM API for recommendations
6. Parse and rank results
7. Apply business rules (availability, promotions)
8. Return formatted recommendations
9. Log interaction for future learning
```

### 6. LLM Prompt Strategy

#### Prompt Template Example:

```
You are a meal recommendation expert. Based on the following user profile and available dishes, recommend 5 meals.

User Profile:
- Previous orders: [list of frequently ordered dishes]
- Dietary preferences: [extracted from embeddedPref]
- Budget range: [calculated from order history]
- Favorite cuisines: [derived from purchase patterns]
- Allergies/Restrictions: [from specialinfo]

Available Dishes:
[Structured list of dishes with descriptions, ingredients, price, popularity]

Context:
- Time: [current time]
- Restaurant: [restaurant name and cuisine type]
- Weather: [if available]

Instructions:
1. Recommend dishes that match user preferences
2. Consider variety (don't repeat similar dishes)
3. Balance familiar favorites with new discoveries
4. Respect dietary restrictions and budget
5. Explain why each dish is recommended

Format: Return JSON with dish_id, confidence_score, and explanation for each recommendation.
```

### 7. Performance Targets

- **Response Time**: < 500ms for cached recommendations
- **Fresh Recommendations**: < 2 seconds including LLM call
- **Accuracy**: > 70% user satisfaction (measured via feedback)
- **Coverage**: Handle dietary restrictions, budget constraints

### 8. Database Schema Enhancements (Optional)

Consider adding these tables for better recommendations:

```sql
-- User interaction tracking
CREATE TABLE user_interactions (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  dish_id INT REFERENCES dishes(id),
  interaction_type InteractionType,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Cached recommendations
CREATE TABLE recommendation_cache (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  restaurant_id INT REFERENCES restaurants(id),
  recommendations JSON,
  context_hash VARCHAR(255),
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 9. Success Metrics

- **Click-through rate** on recommendations
- **Conversion rate** (recommendations → orders)
- **User engagement** increase
- **Average order value** improvement
- **System response time** under targets

### 10. Implementation Timeline

- **Week 1**: Core engine + basic LLM integration
- **Week 2**: Context awareness + performance optimization
- **Week 3**: Testing, refinement, and deployment
- **Ongoing**: Monitoring, feedback integration, and improvements

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin with User Profile Service implementation
4. Integrate with existing database schema
5. Start with simple LLM prompts and iterate

## Tools and Libraries Needed

- `openai` or `anthropic` for LLM integration
- `fastapi` for web framework
- `prisma` for database operations
- `redis` for caching
- `pydantic` for data validation
- `numpy` for numerical computations
- `pytest` for testing

Would you like me to proceed with implementing this recommendation system based
on these instructions?
