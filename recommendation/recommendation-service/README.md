# Restaurant Recommendation Service

A dockerized, AI-powered recommendation microservice that provides personalized
meal recommendations using LLM technology and machine learning algorithms.

## 🚀 Features

- **AI-Powered Recommendations**: Uses Gemini or OpenAI for intelligent meal
  suggestions
- **Real Database**: PostgreSQL with proper caching and analytics
- **External API Integration**: Connects to your main backend for user data
- **Docker Ready**: Complete containerization with production setup
- **Caching**: Redis integration for performance optimization
- **Analytics**: Track recommendation performance and user interactions
- **Health Monitoring**: Built-in health checks and monitoring
- **Production Ready**: Gunicorn, proper logging, and security features

## 📁 Project Structure

```
recommendation-service/
├── app/
│   ├── api/                    # API endpoints
│   │   └── recommendations.py  # Recommendation routes
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration settings
│   │   └── database.py        # Database setup
│   ├── models/                 # Database models
│   │   └── recommendation_models.py
│   ├── services/              # Business logic
│   │   ├── recommendation_engine.py  # AI recommendation logic
│   │   └── backend_client.py         # External API client
│   └── main.py                # FastAPI application
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🛠️ Quick Start

### Prerequisites

- Docker & Docker Compose
- Your main backend API running (for user data)
- Gemini API key (or OpenAI API key)

### 1. Clone and Setup

```bash
cd recommendation-service
cp .env.example .env
```

Edit `.env` file with your configuration:

```bash
# Required: Your main backend API
BACKEND_API_URL=http://localhost:8001/api
BACKEND_API_TOKEN=your_api_token_here

# Required: LLM provider
GEMINI_API_KEY=your_gemini_api_key_here
# OR
# OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Start Services (Windows)

```bash
start.bat
```

### 3. Start Services (Linux/Mac)

```bash
chmod +x start.sh
./start.sh
```

### 4. Manual Start

```bash
docker-compose up -d
```

## 🌐 API Endpoints

Once running, access your service at `http://localhost:8000`

### Core Endpoints

| Endpoint  | Method | Description                   |
| --------- | ------ | ----------------------------- |
| `/`       | GET    | Service information           |
| `/health` | GET    | Health check                  |
| `/docs`   | GET    | Interactive API documentation |

### Recommendation Endpoints

| Endpoint                                      | Method | Description                           |
| --------------------------------------------- | ------ | ------------------------------------- |
| `/api/v1/recommendations`                     | GET    | Get personalized recommendations      |
| `/api/v1/smart-recommendations`               | POST   | Advanced recommendations with context |
| `/api/v1/recommendations/user/{user_id}`      | GET    | User-specific recommendations         |
| `/api/v1/recommendations/feedback`            | POST   | Record user interactions              |
| `/api/v1/recommendations/analytics/{user_id}` | GET    | User recommendation analytics         |

## 📊 Usage Examples

### Basic Recommendations

```bash
curl "http://localhost:8000/api/v1/recommendations?user_id=1&limit=5"
```

### Restaurant-Specific Recommendations

```bash
curl "http://localhost:8000/api/v1/recommendations?user_id=1&restaurant_id=2&limit=3"
```

### Smart Recommendations with Context

```bash
curl -X POST "http://localhost:8000/api/v1/smart-recommendations" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "available_dish_ids": [1, 2, 3, 4, 5],
       "context": {
         "time_of_day": "dinner",
         "budget_limit": 2000,
         "weather": "rainy",
         "group_size": 2
       },
       "max_recommendations": 5
     }'
```

### Record User Interaction

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/feedback?user_id=1&dish_id=3&interaction_type=order"
```

## 🔧 Configuration

### Environment Variables

| Variable            | Description                  | Default                                                               |
| ------------------- | ---------------------------- | --------------------------------------------------------------------- |
| `DATABASE_URL`      | PostgreSQL connection string | `postgresql://rec_user:rec_password@localhost:5432/recommendation_db` |
| `BACKEND_API_URL`   | Your main backend API URL    | `http://localhost:8001/api`                                           |
| `BACKEND_API_TOKEN` | API token for backend auth   | None                                                                  |
| `GEMINI_API_KEY`    | Google Gemini API key        | None                                                                  |
| `OPENAI_API_KEY`    | OpenAI API key               | None                                                                  |
| `LLM_MODEL`         | LLM model to use             | `gemini-2.0-flash`                                                    |
| `REDIS_URL`         | Redis connection string      | `redis://localhost:6379/0`                                            |
| `CACHE_EXPIRE_TIME` | Cache expiration in seconds  | `3600`                                                                |
| `DEBUG`             | Enable debug mode            | `false`                                                               |

### Backend API Requirements

Your main backend should provide these endpoints:

- `GET /users/{user_id}/profile` - User profile with preferences
- `GET /dishes` - Available dishes
- `GET /restaurants` - Restaurant list
- `POST /analytics/interactions` - Log user interactions (optional)

## 🚀 Production Deployment

### Using Docker Compose

```bash
# Copy production compose file
cp docker-compose.prod.yml docker-compose.yml

# Set production environment variables
export DB_HOST=your-db-host
export DB_PASSWORD=your-secure-password
export BACKEND_API_URL=https://your-backend-api.com/api
export BACKEND_API_TOKEN=your-production-token
export GEMINI_API_KEY=your-gemini-key

# Deploy
docker-compose up -d
```

### Using Kubernetes

```yaml
# k8s-deployment.yaml example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recommendation-service
  template:
    metadata:
      labels:
        app: recommendation-service
    spec:
      containers:
        - name: recommendation-service
          image: your-registry/recommendation-service:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: rec-secrets
                  key: database-url
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: rec-secrets
                  key: gemini-key
```

## 📊 Monitoring & Analytics

### Health Checks

```bash
curl http://localhost:8000/health
```

### User Analytics

```bash
curl http://localhost:8000/api/v1/recommendations/analytics/1
```

### Logs

```bash
# View service logs
docker-compose logs -f recommendation-service

# View database logs
docker-compose logs -f postgres
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Manual Testing

```bash
# Test health
curl http://localhost:8000/health

# Test recommendations
curl "http://localhost:8000/api/v1/recommendations?user_id=1"
```

## 🔒 Security

### API Authentication

Add authentication to your endpoints by implementing:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement your token verification
    if not verify_jwt_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Database Security

- Use strong passwords
- Enable SSL connections
- Implement database connection pooling
- Regular security updates

## 📈 Performance Optimization

### Caching Strategy

- User profiles cached for 1 hour
- Recommendations cached for 30 minutes
- Dish data cached for 15 minutes

### Database Optimization

- Proper indexing on user_id, dish_id
- Connection pooling
- Query optimization

### Scaling

- Horizontal scaling with multiple containers
- Load balancing
- Database read replicas
- CDN for static assets

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**

   ```bash
   # Check database is running
   docker-compose ps postgres

   # Check logs
   docker-compose logs postgres
   ```

2. **LLM API Errors**

   ```bash
   # Verify API key
   echo $GEMINI_API_KEY

   # Check service logs
   docker-compose logs recommendation-service
   ```

3. **Backend API Not Accessible**

   ```bash
   # Test backend connectivity
   curl http://localhost:8001/api/health

   # Check network connectivity
   docker network ls
   ```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
docker-compose up -d
```

## 🤝 Integration Guide

### Integrating with Your Backend

1. **Update Backend API URL**:

   ```bash
   BACKEND_API_URL=http://your-backend:8001/api
   ```

2. **Implement Required Endpoints** in your backend:

   ```python
   @app.get("/users/{user_id}/profile")
   async def get_user_profile(user_id: int):
       return {
           "user": user_data,
           "preferences": user_preferences,
           "orderHistory": recent_orders,
           "reviews": user_reviews
       }
   ```

3. **Call Recommendation Service** from your frontend:
   ```javascript
   const recommendations = await fetch(
     "http://localhost:8000/api/v1/recommendations?user_id=1"
   );
   ```

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:

- Check the logs: `docker-compose logs -f`
- Review health endpoint: `/health`
- Check API docs: `/docs`

---

**Ready to get personalized recommendations! 🍽️✨**
