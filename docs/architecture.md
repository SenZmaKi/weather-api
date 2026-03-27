# Architecture Documentation

This document describes the system architecture, design decisions, and technical implementation of the Weather API service.

## Overview

The Weather API is a modern, asynchronous web service built with FastAPI that provides weather information by integrating with the OpenWeatherMap API. It features a clean architecture, comprehensive error handling, rate limiting, and a responsive web interface.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   API Clients   │    │   Mobile Apps   │
│   (Frontend)    │    │   (External)    │    │   (Future)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └─────────────┬────────┴──────────────────────┘
                        │ HTTP/HTTPS
                        │
    ┌──────────────────┴───────────────────┐
    │           Load Balancer              │ (Production)
    │         (nginx/Apache)               │
    └──────────────────┬───────────────────┘
                        │
    ┌──────────────────┴───────────────────┐
    │         FastAPI Application          │
    │         ┌─────────────────┐          │
    │         │   Rate Limiter  │          │
    │         └─────────────────┘          │
    │         ┌─────────────────┐          │
    │         │ CORS Middleware │          │
    │         └─────────────────┘          │
    │         ┌─────────────────┐          │
    │         │  API Endpoints  │          │
    │         └─────────────────┘          │
    └──────────────────┬───────────────────┘
                        │
    ┌─────────────────┴────────────────────┐
    │           Service Layer              │
    │   ┌───────────────┐ ┌─────────────┐  │
    │   │ Weather       │ │ Database    │  │
    │   │ Service       │ │ Service     │  │
    │   └───────┬───────┘ └─────────────┘  │
    └───────────┼────────────────────────────┘
                │                    │
    ┌───────────┴───────────┐   ┌────┴──────┐
    │  OpenWeatherMap API   │   │ SQLite/   │
    │  (External Service)   │   │PostgreSQL │
    └───────────────────────┘   └───────────┘
```

## Core Components

### 1. FastAPI Application (`app/main.py`)

The main application module that:
- Configures FastAPI with metadata and documentation
- Sets up middleware for CORS and rate limiting
- Includes API routers
- Manages application lifecycle
- Serves static files and templates

**Key Features:**
- Automatic OpenAPI documentation generation
- Built-in request validation
- Asynchronous request handling
- Type safety with Pydantic models

### 2. API Layer (`app/api/`)

#### Endpoints (`app/api/endpoints.py`)
Handles HTTP requests and responses:
- Route definitions with OpenAPI metadata
- Request parameter validation
- Response model serialization
- HTTP exception handling
- Integration with service layer

#### Schemas (`app/api/schemas.py`)
Pydantic models for data validation:
- Request parameter validation
- Response serialization
- Type safety enforcement
- API documentation generation

### 3. Service Layer (`app/services/`)

Business logic layer that:
- Integrates with external APIs
- Implements business rules
- Transforms data between layers
- Handles external service errors

#### Weather Service (`app/services/weather_service.py`)
- OpenWeatherMap API integration
- HTTP client management
- Error handling and retries
- Data transformation

### 4. Data Layer (`app/models/`)

#### Database Configuration (`app/models/database.py`)
- SQLAlchemy async engine setup
- Database connection management
- Session handling
- Database initialization

#### Models (`app/models/search_history.py`)
- SQLAlchemy ORM models
- Database schema definition
- Relationship management

### 5. Configuration (`app/config.py`)

Centralized configuration management:
- Environment variable loading
- Settings validation
- Default value management
- Environment-specific configurations

## Design Patterns

### 1. Repository Pattern
Although not explicitly implemented, the service layer abstracts data access, making it easy to swap data sources.

### 2. Dependency Injection
FastAPI's dependency system is used for:
- Database session management
- Configuration injection
- Service instantiation

### 3. Factory Pattern
Settings factory with caching:
```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 4. Adapter Pattern
The weather service acts as an adapter between the internal API and OpenWeatherMap API.

## Data Flow

### 1. Current Weather Request
```
1. Client → GET /weather?city=London
2. FastAPI → Validate request parameters
3. FastAPI → Route to get_weather() endpoint
4. Endpoint → Create WeatherService instance
5. Service → HTTP GET to OpenWeatherMap API
6. Service → Return raw API response
7. Endpoint → Parse response with parse_weather_data()
8. Endpoint → Save to database (SearchHistory)
9. Endpoint → Return WeatherResponse
10. FastAPI → Serialize response to JSON
11. Client ← JSON response
```

### 2. Error Handling Flow
```
1. Service → HTTP request fails
2. Service → httpx raises HTTPStatusError
3. Endpoint → Catch exception
4. Endpoint → Check error type (404, 500, etc.)
5. Endpoint → Raise appropriate HTTPException
6. FastAPI → Serialize error to JSON
7. Client ← Error response with proper HTTP status
```

## Database Design

### Schema

```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_type VARCHAR(50) NOT NULL,
    city VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    forecast_days INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    response_data TEXT
);

-- Indexes
CREATE INDEX idx_search_history_timestamp ON search_history(timestamp);
CREATE INDEX idx_search_history_city ON search_history(city);
CREATE INDEX idx_search_history_type ON search_history(search_type);
```

### Data Model

```python
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    search_type = Column(String(50), nullable=False, index=True)  # 'city', 'coordinates', 'forecast'
    city = Column(String(255), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    forecast_days = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    response_data = Column(Text, nullable=True)  # Store full API response
```

## External Integrations

### OpenWeatherMap API

**Base URL:** `https://api.openweathermap.org/data/2.5`

**Endpoints Used:**
- `/weather` - Current weather data
- `/forecast` - 5-day forecast with 3-hour intervals

**Authentication:** API key in query parameter
**Rate Limits:** 60 calls/minute (free tier)

**Error Handling:**
- 401: Invalid API key
- 404: Location not found  
- 429: Rate limit exceeded
- 500: Service unavailable

## Security Considerations

### 1. API Key Management
- API keys stored in environment variables
- Never committed to version control
- Separate keys for development/production

### 2. Rate Limiting
- IP-based rate limiting (60 requests/minute)
- Configurable limits via environment variables
- HTTP 429 responses when limits exceeded

### 3. Input Validation
- All input parameters validated by Pydantic
- SQL injection prevention through SQLAlchemy ORM
- XSS prevention through proper output encoding

### 4. CORS Configuration
- Configurable allowed origins
- Restricts cross-origin requests in production
- Development allows localhost origins

### 5. Error Information Disclosure
- Generic error messages to prevent information leakage
- Detailed errors only in debug mode
- No sensitive data in error responses

## Performance Considerations

### 1. Asynchronous Processing
- FastAPI with async/await throughout
- Non-blocking I/O operations
- Concurrent request handling

### 2. Database Optimization
- Indexed search columns
- Connection pooling (SQLAlchemy)
- Async database operations

### 3. HTTP Client Optimization
- Connection pooling with httpx
- Automatic connection reuse
- Timeout configuration

### 4. Caching Strategy
- No caching implemented (data freshness priority)
- Future considerations:
  - Redis for API response caching
  - CDN for static assets
  - Application-level caching

### 5. Response Size Optimization
- Minimal response payloads
- JSON serialization optimizations
- Gzip compression (server level)

## Scalability Architecture

### Current State (Single Instance)
```
Client → FastAPI App → SQLite → External API
```

### Horizontal Scaling
```
         Load Balancer
              │
    ┌─────────┼─────────┐
    │         │         │
FastAPI   FastAPI   FastAPI
Instance  Instance  Instance
    │         │         │
    └─────────┼─────────┘
              │
        PostgreSQL
              │
       Connection Pool
```

### Microservices (Future)
```
API Gateway
    │
    ├── Weather Service
    ├── History Service  
    ├── Authentication Service
    └── Notification Service
```

## Monitoring and Observability

### Current Implementation
- Basic health check endpoint (`/health`)
- FastAPI automatic request logging
- Exception tracking in endpoints

### Production Recommendations
- **Metrics**: Prometheus + Grafana
- **Logging**: Structured logging with ELK stack
- **Tracing**: OpenTelemetry for distributed tracing
- **Alerting**: Alert on error rates, response times
- **Health Checks**: Deep health checks for dependencies

### Key Metrics to Monitor
- Request rate (requests/second)
- Response times (p50, p95, p99)
- Error rates by endpoint
- External API response times
- Database connection pool usage
- Memory and CPU usage

## Deployment Architecture

### Development
```
Developer Machine
├── FastAPI (localhost:8000)
├── SQLite (local file)
└── Static files (local)
```

### Production Options

#### Option 1: Single Server
```
Server
├── nginx (reverse proxy)
├── FastAPI (systemd service)
├── PostgreSQL
└── SSL/TLS certificates
```

#### Option 2: Container Orchestration
```yaml
# docker-compose.yml
services:
  app:
    image: weather-api:latest
    ports:
      - "8000:8000"
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: weatherapi
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
```

#### Option 3: Cloud Deployment
- **AWS**: ECS/Fargate + RDS + CloudFront
- **Google Cloud**: Cloud Run + Cloud SQL
- **Azure**: Container Instances + PostgreSQL

## Technology Stack Rationale

### FastAPI
**Chosen for:**
- Modern Python async framework
- Automatic API documentation
- Built-in validation with Pydantic
- High performance
- Type safety support

**Alternatives considered:**
- Flask: Less built-in functionality
- Django: Overkill for API-only service
- Starlette: Lower level, more setup required

### SQLAlchemy + SQLite/PostgreSQL
**Chosen for:**
- Mature ORM with async support
- Database agnostic (easy to switch)
- Type safety with models
- Migration support

**Alternatives considered:**
- Raw SQL: More prone to errors
- NoSQL: Relational data fits SQL better

### httpx
**Chosen for:**
- Modern async HTTP client
- Excellent performance
- Clean API similar to requests
- Built-in timeout and retry support

**Alternatives considered:**
- aiohttp: More complex API
- requests: Synchronous only

### UV Package Manager
**Chosen for:**
- Faster than pip
- Built-in virtual environment management
- Lock file support
- Modern Python tooling

**Alternatives considered:**
- pip + virtualenv: Slower, more setup
- Poetry: Good alternative, similar features

## Security Architecture

### Authentication (Future Enhancement)
```
Client → API Gateway → JWT Validation → FastAPI App
                            │
                     Auth Service
```

### Data Encryption
- **In Transit**: HTTPS/TLS 1.3
- **At Rest**: Database encryption (production)
- **API Keys**: Environment variables only

### Access Control
- IP-based rate limiting
- CORS origin restrictions
- Input validation at API boundary

## Error Handling Strategy

### Error Hierarchy
```
1. Network/Infrastructure Errors
   ├── Connection failures
   ├── Timeouts  
   └── DNS resolution failures

2. External Service Errors
   ├── API key issues (401)
   ├── Rate limits (429)
   ├── Service unavailable (503)
   └── Data not found (404)

3. Application Errors
   ├── Validation errors (400)
   ├── Database errors (500)
   └── Unexpected errors (500)
```

### Error Response Format
```json
{
  "error": "ValidationError",
  "message": "City parameter is required",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z",
  "details": {
    "field": "city",
    "constraint": "required"
  }
}
```

## Future Architecture Enhancements

### Phase 1: Enhanced Reliability
- Redis caching layer
- Circuit breaker pattern
- Retry mechanisms with exponential backoff
- Health check improvements

### Phase 2: Advanced Features
- User authentication and API keys
- Webhook notifications
- Data analytics and insights
- Mobile push notifications

### Phase 3: Microservices
- Service decomposition
- Event-driven architecture
- Distributed tracing
- Service mesh (Istio/Linkerd)

This architecture documentation provides a comprehensive overview of the system design, making it easier for developers to understand the codebase and make informed decisions about future enhancements.