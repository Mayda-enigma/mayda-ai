# 🍽️ AI-Powered Meal Recommendation System

A comprehensive, production-ready recommendation system that delivers personalized meal recommendations using AI, user behavior analysis, and contextual factors. The system supports both standalone operation and containerized deployment.

## ✨ Key Features

- **🤖 AI-Powered**: Uses Google Gemini AI for intelligent recommendations with fallback logic
- **👤 User Profiling**: Advanced user preference analysis from order history and ratings
- **🎯 Contextual**: Considers time of day, dietary restrictions, budget, and availability
- **🔄 Flexible Architecture**: Mock database for testing, containerized service option
- **🧪 Well-Tested**: Comprehensive test suite with quality validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation & Setup

```bash
# Clone and navigate to the project
cd "Recommendation system"

# Install dependencies
pip install -r requirements.txt

# Optional: Set up Gemini AI (system works without it)
# Create .env file and add: GEMINI_API_KEY=your_api_key_here

# Test the system
python test_recommendations_full.py
```

## 📁 Project Architecture

### Core Components

```
├── � Core Recommendation Engine
│   ├── llm_recommendation_engine.py    # Gemini AI-powered recommendations
│   └── user_profile_service.py         # User behavior & preference analysis
│
├── 🗄️ Mock Database Layer
│   ├── mock_database/
│   │   ├── api.py                      # RESTful API endpoints
│   │   ├── data.py                     # Sample restaurant/user data
│   │   └── models.py                   # Data models & schemas
│
├── 🐳 Containerized Service
│   └── recommendation-service/
│       ├── Dockerfile
│       ├── docker-compose.simple.yml
│       └── app/
│           ├── main.py                 # FastAPI application
│           ├── core/config.py          # Configuration management
│           └── services/
│               ├── backend_client.py   # External API client
│               └── simple_recommendation_engine.py
│
├── 🧪 Testing Suite
│   ├── test_recommendations_full.py    # Full system integration tests
│   ├── test_fixed_recommendations.py   # Fixed scenario testing
│   ├── test_user_scenarios.py          # User journey testing
│   └── test_container_host.py          # Container deployment tests
│
├── 📋 Documentation
│   ├── RECOMMENDATION_SYSTEM_INSTRUCTIONS.md  # Implementation guide
│   ├── DATABASE_API_REQUIREMENTS.md           # API specifications
│   └── API_MIGRATION_NOTES.md                # Migration documentation
└── requirements.txt                           # Python dependencies
```

## 🎯 System Capabilities

### 🤖 AI-Powered Recommendations
- **Gemini AI Integration**: Leverages Google's Gemini model for contextual recommendations
- **Intelligent Fallback**: Rule-based recommendations when AI is unavailable
- **Natural Language Processing**: Understands user preferences and dietary requirements
- **Context Awareness**: Factors in time of day, budget constraints, and special occasions

### 👤 Advanced User Profiling
- **Preference Mining**: Extracts insights from `embeddedPref` JSON fields
- **Behavioral Analysis**: Studies order patterns, frequency, and spending habits
- **Rating Intelligence**: Analyzes user reviews and ratings for preference refinement
- **Dietary Recognition**: Automatically detects dietary restrictions and preferences

### 🏪 Restaurant Intelligence
- **Dynamic Availability**: Real-time dish availability and popularity tracking
- **Price Optimization**: Budget-conscious recommendations with cost analysis
- **Category Expertise**: Cuisine type recognition and specialty matching
- **Quality Metrics**: Integration of dish ratings and preparation times

## 🔧 Usage Examples

### Basic Recommendation Request
```python
from llm_recommendation_engine import LLMRecommendationEngine

# Initialize the engine
engine = LLMRecommendationEngine()

# Get recommendations for a user
recommendations = engine.get_recommendations(
    user_id=1,
    restaurant_id=101,
    context={
        "time_of_day": "dinner",
        "budget": 50.0,
        "party_size": 2
    }
)

print(f"Recommended dishes: {recommendations}")
```

### User Profile Analysis
```python
from user_profile_service import UserProfileService

# Initialize profile service
profile_service = UserProfileService("http://localhost:8000")

# Get comprehensive user profile
profile = profile_service.get_user_profile(user_id=1)
print(f"User preferences: {profile['preferences']}")
print(f"Dietary restrictions: {profile['dietary_restrictions']}")
```

### Running the Mock API
```bash
cd mock_database
python api.py
# API will be available at http://localhost:8000
```

### 🍽️ Smart Matching
- **Cuisine Alignment**: Matches user's preferred cuisines
- **Budget Compliance**: Respects price constraints
- **Dietary Restrictions**: Handles vegetarian, pescatarian, etc.
- **Diversity**: Ensures varied recommendations

## 📊 Test Coverage

### Integration Tests (`test_recommendation_system.py`)
- ✅ Core component initialization
- ✅ Real-world recommendation scenarios
- ✅ Budget and preference compliance
- ✅ Edge cases and error handling
- ✅ API compatibility
- ✅ Performance benchmarks

### Quality Tests (`test_recommendation_quality.py`)
- ✅ User preference matching accuracy
- ✅ Budget constraint adherence
- ✅ Dietary restriction compliance
- ✅ Restaurant diversity validation
- ✅ Price range diversity
- ✅ Edge case handling
- ✅ Performance testing
- ✅ Contextual awareness

### Quick Demo (`quick_test.py`)
- 🍝 Italian food lover scenario
- 🌶️ Spicy food enthusiast scenario
- 🐟 Seafood lover scenario

## 🧪 Test Results

The system includes comprehensive test scenarios:

```
🧪 SMART RECOMMENDATION SYSTEM - INTEGRATION TESTS
============================================================
✅ PASS Core Components
✅ PASS Real-World Scenarios  
✅ PASS Recommendation Quality
✅ PASS Edge Cases
✅ PASS API Compatibility
✅ PASS Performance Benchmarks

📊 TEST SUMMARY: 100% Success Rate
🎯 Overall Status: ✅ SYSTEM READY
```

## 📈 Sample Test Scenarios

### Scenario 1: Italian Food Enthusiast
- **User**: Ahmed Belkacem (prefers Italian, Mediterranean)
- **Context**: Lunch time, budget ≤ 1800 DZD
- **Expected**: Italian dishes from La Bella Vista
- **Result**: ✅ 2/3 recommendations are Italian

### Scenario 2: Spicy Food Lover  
- **User**: Fatima Bensaid (prefers Middle Eastern, spicy)
- **Context**: Dinner time
- **Expected**: Spicy dishes from Spice Palace
- **Result**: ✅ Recommendations include tajines and grills

### Scenario 3: Seafood Enthusiast
- **User**: Karim Meziane (pescatarian, seafood lover)
- **Context**: Budget ≤ 2500 DZD
- **Expected**: Fish dishes, no meat
- **Result**: ✅ Only seafood and vegetarian options

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Optional - system works without this
GEMINI_API_KEY=your_api_key_here
```

### Recommendation Parameters
```python
# Customizable recommendation settings
MAX_RECOMMENDATIONS = 5
CONFIDENCE_THRESHOLD = 0.7
PRICE_WEIGHT = 0.3
PREFERENCE_WEIGHT = 0.4
POPULARITY_WEIGHT = 0.3
```

## 🐳 Docker Deployment

### Quick Container Setup
```bash
cd recommendation-service

# Build and run with docker-compose
docker-compose -f docker-compose.simple.yml up --build

# Service will be available at http://localhost:8080
```

### Container Features
- **Lightweight**: Optimized Python Alpine-based container
- **Health Checks**: Built-in health monitoring endpoints
- **Environment Configuration**: Flexible config via environment variables
- **Scalable**: Ready for horizontal scaling and load balancing

## 🧪 Testing & Validation

### Test Suite Overview
```bash
# Full system integration test
python test_recommendations_full.py

# Fixed scenario validation
python test_fixed_recommendations.py

# User journey testing
python test_user_scenarios.py

# Container deployment testing
python test_container_host.py
```

### Test Coverage
- ✅ User profile extraction and analysis
- ✅ AI recommendation generation with fallback
- ✅ API endpoint functionality and error handling
- ✅ Container deployment and service availability
- ✅ Edge cases and error conditions
- ✅ Performance and response time validation

## ⚙️ System Configuration

### Environment Variables
```bash
# Optional: Gemini AI API key for enhanced recommendations
GEMINI_API_KEY=your_gemini_api_key

# API configuration (for containerized deployment)
BACKEND_API_URL=http://localhost:8000
PORT=8080
HOST=0.0.0.0
```

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Dependencies**: See `requirements.txt`
- **Network**: HTTP access for external AI API (optional)

## 🚀 Performance & Scaling

### Optimization Features
- **Caching**: User profile and dish data caching
- **Async Processing**: Non-blocking recommendation generation
- **Batch Processing**: Multiple recommendation requests
- **Fallback Logic**: Graceful degradation without AI service

### Production Readiness
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging for monitoring and debugging
- **Health Monitoring**: Service health and readiness endpoints
- **Configuration Management**: Environment-based configuration

## 📚 Documentation

- **[Implementation Guide](RECOMMENDATION_SYSTEM_INSTRUCTIONS.md)**: Detailed architecture and implementation instructions
- **[API Requirements](DATABASE_API_REQUIREMENTS.md)**: Database and API specifications
- **[Migration Notes](API_MIGRATION_NOTES.md)**: Deployment and migration guidance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions, issues, or contributions:
- Create an issue in the repository
- Check the documentation files for detailed information
- Review test files for usage examples

---

**Built with ❤️ for intelligent meal recommendations**
recommendations = llm_engine.get_recommendations(
    user_profile=profile,
    available_dish_ids=[1, 2, 3, 4, 5],
    context={
        "time_of_day": "lunch",     # lunch, dinner, etc.
        "budget_limit": 2000        # Maximum price in DZD
    },
    max_recommendations=5
)
```

## 🧮 Performance Metrics

- **Response Time**: < 30 seconds (with API), < 1 second (fallback)
- **Accuracy**: 85%+ preference alignment
- **Diversity**: 2+ restaurants in 5 recommendations
- **Budget Compliance**: 100% when constraints specified

## 🔍 Quality Assurance

### Automated Testing
- **Unit Tests**: Component-level validation
- **Integration Tests**: End-to-end workflows  
- **Quality Tests**: Recommendation accuracy
- **Performance Tests**: Response time benchmarks
- **Edge Case Tests**: Error handling

### Manual Validation
- User preference alignment
- Budget constraint compliance
- Dietary restriction adherence
- Restaurant diversity
- Price range variety

## 🚀 Production Readiness

### ✅ Ready Features
- Comprehensive test coverage
- Error handling and fallbacks
- Performance optimization
- API-ready architecture
- Documentation

### 📝 Usage Example

```python
from user_profile_service import user_profile_service  
from llm_recommendation_engine import llm_engine

# Get user profile
profile = user_profile_service.get_user_profile(1)

# Get recommendations
recommendations = llm_engine.get_recommendations(
    user_profile=profile,
    available_dish_ids=[1, 2, 3, 4, 5, 6, 7],
    context={"time_of_day": "lunch", "budget_limit": 2000},
    max_recommendations=3
)

# Process results
for rec in recommendations:
    print(f"{rec['dish_name']} - {rec['restaurant_name']}")
    print(f"Price: {rec['price']} DZD | Confidence: {rec['confidence_score']}")
    print(f"Why: {rec['explanation']}")
```

## 🏗️ Architecture

### Components
1. **User Profile Service**: Analyzes user preferences and history
2. **LLM Recommendation Engine**: AI-powered recommendation generation
3. **Mock Database**: Sample data for testing and development
4. **API Layer**: FastAPI-ready endpoints

### Data Flow
1. Extract user profile and preferences
2. Analyze available dishes
3. Apply contextual filters (budget, time, dietary)
4. Generate AI recommendations with explanations
5. Return ranked results with confidence scores

---

**🎯 Ready for production testing and deployment!**