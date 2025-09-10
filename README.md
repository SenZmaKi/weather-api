# Weather API Service

A modern Weather API service built with FastAPI, featuring external API integration with OpenWeatherMap, search history tracking, and a clean, responsive web interface.

https://github.com/user-attachments/assets/eebd1b8a-5aaa-4549-91eb-433147f7d789

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
  - [Development Mode](#development-mode)
  - [Production Mode](#production-mode)
- [API Endpoints](#api-endpoints)
  - [Get Current Weather](#get-current-weather)
  - [Get Weather Forecast](#get-weather-forecast)
  - [Get Search History](#get-search-history)
  - [Clear Search History](#clear-search-history)
- [Environment Configuration](#environment-configuration)
- [Project Structure](#project-structure)
- [Features in Detail](#features-in-detail)
  - [Rate Limiting](#rate-limiting)
  - [Error Handling](#error-handling)
  - [Search History](#search-history)
  - [Type Safety](#type-safety)
- [Testing](#testing)
- [Browser Testing](#browser-testing)
- [API Documentation](#api-documentation)
- [Development](#development)
  - [Adding New Features](#adding-new-features)
  - [Database Migrations](#database-migrations)
- [Deployment Considerations](#deployment-considerations)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Current Weather Data**: Get real-time weather information by city name or geographic coordinates
- **Weather Forecast**: Retrieve 1-5 day weather forecasts with 3-hour intervals
- **Search History**: Automatic tracking of all weather searches with timestamps
- **Rate Limiting**: Built-in rate limiting to prevent API abuse (60 requests/minute by default)
- **Modern UI**: Clean, responsive web interface with tab-based navigation
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Type Safety**: Full type annotations throughout the Python codebase
- **Async Support**: Built on FastAPI with async/await for optimal performance

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Database**: SQLite with SQLAlchemy ORM (async)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Package Manager**: UV
- **API Integration**: OpenWeatherMap API
- **Rate Limiting**: SlowAPI
- **HTTP Client**: httpx

## Prerequisites

- Python 3.12 or higher
- UV package manager (`pip install uv`)
- OpenWeatherMap API key (free tier available at https://openweathermap.org/api)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/SenZmaKi/weather-api.git
cd weather-api
```

2. Install dependencies using UV:

```bash
uv sync
```

3. Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

4. Edit the `.env` file and add your [OpenWeatherMap API key](https://openweathermap.org/):

```env
OPENWEATHER_API_KEY=your_actual_api_key_here
```

## Running the Application

### Development Mode

Using UV:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or activate the virtual environment and run directly:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at:

- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Documentation: http://localhost:8000/redoc

## API Endpoints

### Get Current Weather

```
GET /weather?city={city}
GET /weather?lat={latitude}&lon={longitude}
```

**Parameters:**

- `city` (string): City name (e.g., "London", "New York")
- `lat` (float): Latitude (-90 to 90)
- `lon` (float): Longitude (-180 to 180)

**Response:** Current weather data including temperature, humidity, wind speed, etc.

### Get Weather Forecast

```
GET /weather/forecast?city={city}&days={days}
```

**Parameters:**

- `city` (string, required): City name
- `days` (integer, optional): Number of days (1-5, default: 5)

**Response:** Weather forecast with 3-hour intervals for the specified days

### Get Search History

```
GET /weather/history
```

**Parameters:**

- `limit` (integer, optional): Maximum records to return (default: 100)
- `offset` (integer, optional): Number of records to skip (default: 0)

**Response:** List of previous weather searches with timestamps

### Clear Search History

```
DELETE /weather/history
```

**Response:** Confirmation message with number of records deleted

## Environment Configuration

The application can be configured via environment variables in the `.env` file:

```env
# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY=your_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./weather.db

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

## Project Structure

```
weather-api/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py         # API route handlers
│   │   └── schemas.py           # Pydantic models for request/response
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # Database configuration
│   │   └── search_history.py    # SQLAlchemy models
│   ├── services/
│   │   ├── __init__.py
│   │   └── weather_service.py   # OpenWeatherMap API integration
│   ├── config.py                # Application configuration
│   └── main.py                  # FastAPI application entry point
├── static/
│   ├── css/
│   │   └── styles.css           # Application styles
│   ├── js/
│   │   └── app.js               # Frontend JavaScript
│   └── favicon.ico              # Site favicon
├── templates/
│   └── index.html               # Main HTML template
├── .env                         # Environment variables (create from .env.example)
├── .env.example                 # Example environment configuration
├── .gitignore                   # Git ignore file
├── pyproject.toml               # Project configuration and dependencies
├── README.md                    # This file
└── uv.lock                      # Locked dependencies
```

## Features in Detail


### Rate Limiting

- Default: 60 requests per minute per IP address
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable
- Returns 429 status code when limit exceeded

### Error Handling

- Comprehensive error responses with appropriate HTTP status codes
- 400: Bad Request (missing or invalid parameters)
- 404: Not Found (city or location not found)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error

### Search History

- Automatically stores all weather searches
- Includes search type, location, timestamp, and full response data
- Searchable and deletable via API endpoints
- Persisted in SQLite database

### Type Safety

- Full type annotations for all functions and methods
- Pydantic models for request/response validation
- Type hints for better IDE support and error prevention

## Testing

To run a quick test of the API endpoints:

```bash
# Test current weather by city
curl "http://localhost:8000/weather?city=London"

# Test current weather by coordinates
curl "http://localhost:8000/weather?lat=51.5074&lon=-0.1278"

# Test weather forecast
curl "http://localhost:8000/weather/forecast?city=London&days=3"

# Test search history
curl "http://localhost:8000/weather/history"

# Test health check
curl "http://localhost:8000/health"
```

## Browser Testing

1. Open http://localhost:8000 in your web browser
2. Use the tabbed interface to:
   - Search weather by city name
   - Search weather by coordinates
   - Get weather forecasts
3. View search history at the bottom of the page
4. Click on history items to repeat searches
5. Clear history using the "Clear History" button

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs

  - Interactive API testing interface
  - Try out endpoints directly from the browser
  - View request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Alternative documentation interface
  - Clean, readable API reference

## Development

### Adding New Features

1. Update models in `app/models/`
2. Add new endpoints in `app/api/endpoints.py`
3. Update schemas in `app/api/schemas.py`
4. Add service logic in `app/services/`
5. Update frontend in `static/` and `templates/`

### Database Migrations

The database schema is automatically created on application startup. To reset the database:

```bash
rm weather.db
uv run uvicorn app.main:app --reload
```

## Deployment Considerations

For production deployment:

1. Set `DEBUG=False` in the `.env` file
2. Use a production-grade database (PostgreSQL recommended)
3. Configure proper CORS origins (not "\*")
4. Use a reverse proxy (nginx, Apache)
5. Enable HTTPS
6. Consider using a process manager (systemd, supervisor)
7. Implement proper logging
8. Set up monitoring and alerting

## License

This project is created as a technical assessment submission.

## Acknowledgments

- OpenWeatherMap for providing the weather data API
- FastAPI for the excellent web framework
- UV for modern Python package management
