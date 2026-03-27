# API Documentation

This document provides detailed information about the Weather API endpoints, including request/response formats, examples, and error handling.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `http://91.98.38.42:8000`

## Authentication

No authentication is required for this API. Rate limiting is applied (60 requests per minute by default).

## Content Type

All API endpoints accept and return JSON data unless otherwise specified.

## Rate Limiting

- **Default Limit**: 60 requests per minute per IP address
- **Headers**: Rate limit information is included in response headers:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when rate limit window resets

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters or missing required fields
- `404 Not Found`: Resource not found (e.g., city not found)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Endpoints

### 1. Get Current Weather

Get current weather data for a specific location.

#### Endpoint

```http
GET /weather
```

#### Parameters

| Parameter | Type    | Required | Description                    | Constraints       |
|-----------|---------|----------|--------------------------------|-------------------|
| `city`    | string  | No*      | City name (e.g., "London")    | Min 2 characters  |
| `lat`     | float   | No*      | Latitude coordinate            | -90 to 90         |
| `lon`     | float   | No*      | Longitude coordinate           | -180 to 180       |

*Either `city` or both `lat` and `lon` must be provided.

#### Example Requests

**By City Name:**
```bash
curl "http://localhost:8000/weather?city=London"
```

**By Coordinates:**
```bash
curl "http://localhost:8000/weather?lat=51.5074&lon=-0.1278"
```

#### Example Response

```json
{
  "city": "London",
  "country": "GB",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "temperature": 15.6,
  "feels_like": 14.2,
  "temp_min": 13.1,
  "temp_max": 18.3,
  "pressure": 1013,
  "humidity": 72,
  "visibility": 10000,
  "wind_speed": 3.6,
  "wind_deg": 230,
  "clouds": 40,
  "weather": "Clouds",
  "weather_description": "scattered clouds",
  "weather_icon": "03d",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### Response Fields

| Field                | Type     | Description                                  |
|----------------------|----------|----------------------------------------------|
| `city`               | string   | City name (null for coordinate searches)    |
| `country`            | string   | Country code (ISO 3166)                     |
| `latitude`           | float    | Location latitude                            |
| `longitude`          | float    | Location longitude                           |
| `temperature`        | float    | Current temperature (°C)                     |
| `feels_like`         | float    | Perceived temperature (°C)                   |
| `temp_min`           | float    | Minimum temperature (°C)                     |
| `temp_max`           | float    | Maximum temperature (°C)                     |
| `pressure`           | integer  | Atmospheric pressure (hPa)                   |
| `humidity`           | integer  | Humidity percentage                          |
| `visibility`         | integer  | Visibility in meters                         |
| `wind_speed`         | float    | Wind speed (m/s)                            |
| `wind_deg`           | integer  | Wind direction (degrees)                     |
| `clouds`             | integer  | Cloudiness percentage                        |
| `weather`            | string   | Weather condition group                      |
| `weather_description`| string   | Detailed weather description                 |
| `weather_icon`       | string   | Weather icon ID                             |
| `timestamp`          | datetime | Data timestamp (ISO 8601)                   |

### 2. Get Weather Forecast

Get weather forecast for 1-5 days with 3-hour intervals.

#### Endpoint

```http
GET /weather/forecast
```

#### Parameters

| Parameter | Type    | Required | Description                    | Constraints |
|-----------|---------|----------|--------------------------------|-------------|
| `city`    | string  | Yes      | City name                      | Min 2 chars |
| `days`    | integer | No       | Number of forecast days        | 1-5 (default: 5) |

#### Example Request

```bash
curl "http://localhost:8000/weather/forecast?city=London&days=3"
```

#### Example Response

```json
{
  "city": "London",
  "country": "GB",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "days_requested": 3,
  "forecast": [
    {
      "datetime": "2024-01-01T15:00:00",
      "temperature": 16.2,
      "feels_like": 15.1,
      "temp_min": 14.8,
      "temp_max": 16.2,
      "pressure": 1015,
      "humidity": 68,
      "weather": "Clear",
      "weather_description": "clear sky",
      "weather_icon": "01d",
      "wind_speed": 2.8,
      "wind_deg": 210,
      "clouds": 5,
      "pop": 0.0
    }
  ]
}
```

#### Response Fields

**Root Level:**
| Field            | Type    | Description                |
|------------------|---------|----------------------------|
| `city`           | string  | City name                  |
| `country`        | string  | Country code               |
| `latitude`       | float   | Location latitude          |
| `longitude`      | float   | Location longitude         |
| `days_requested` | integer | Number of days requested   |
| `forecast`       | array   | Array of forecast items    |

**Forecast Item Fields:**
| Field                | Type     | Description                     |
|----------------------|----------|---------------------------------|
| `datetime`           | datetime | Forecast time (ISO 8601)        |
| `temperature`        | float    | Temperature (°C)                |
| `feels_like`         | float    | Perceived temperature (°C)      |
| `temp_min`           | float    | Minimum temperature (°C)        |
| `temp_max`           | float    | Maximum temperature (°C)        |
| `pressure`           | integer  | Atmospheric pressure (hPa)      |
| `humidity`           | integer  | Humidity percentage             |
| `weather`            | string   | Weather condition group         |
| `weather_description`| string   | Detailed weather description    |
| `weather_icon`       | string   | Weather icon ID                |
| `wind_speed`         | float    | Wind speed (m/s)               |
| `wind_deg`           | integer  | Wind direction (degrees)        |
| `clouds`             | integer  | Cloudiness percentage           |
| `pop`                | float    | Probability of precipitation    |

### 3. Get Search History

Retrieve weather search history with pagination.

#### Endpoint

```http
GET /weather/history
```

#### Parameters

| Parameter | Type    | Required | Description                    | Constraints |
|-----------|---------|----------|--------------------------------|-------------|
| `limit`   | integer | No       | Maximum records to return      | 1-1000 (default: 100) |
| `offset`  | integer | No       | Number of records to skip      | ≥0 (default: 0) |

#### Example Request

```bash
curl "http://localhost:8000/weather/history?limit=10&offset=0"
```

#### Example Response

```json
{
  "total": 25,
  "items": [
    {
      "id": 1,
      "search_type": "city",
      "city": "London",
      "latitude": 51.5074,
      "longitude": -0.1278,
      "forecast_days": null,
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "id": 2,
      "search_type": "coordinates",
      "city": null,
      "latitude": 40.7128,
      "longitude": -74.0060,
      "forecast_days": null,
      "timestamp": "2024-01-01T11:30:00"
    },
    {
      "id": 3,
      "search_type": "forecast",
      "city": "Paris",
      "latitude": 48.8566,
      "longitude": 2.3522,
      "forecast_days": 5,
      "timestamp": "2024-01-01T11:00:00"
    }
  ]
}
```

### 4. Clear Search History

Delete all weather search history.

#### Endpoint

```http
DELETE /weather/history
```

#### Parameters

None

#### Example Request

```bash
curl -X DELETE "http://localhost:8000/weather/history"
```

#### Example Response

```json
{
  "message": "Search history cleared successfully",
  "deleted_count": 25
}
```

### 5. Health Check

Check if the API service is running.

#### Endpoint

```http
GET /health
```

#### Example Request

```bash
curl "http://localhost:8000/health"
```

#### Example Response

```json
{
  "status": "healthy",
  "service": "Weather API"
}
```

## Interactive Documentation

The API provides interactive documentation through:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to:
- Explore all endpoints
- Test API calls directly in the browser
- View detailed request/response schemas
- Download OpenAPI specification

## SDKs and Libraries

### JavaScript/Node.js Example

```javascript
// Using fetch API
async function getCurrentWeather(city) {
  try {
    const response = await fetch(`http://localhost:8000/weather?city=${city}`);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch weather');
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching weather:', error);
    throw error;
  }
}

// Usage
getCurrentWeather('London')
  .then(weather => console.log(weather))
  .catch(error => console.error(error));
```

### Python Example

```python
import httpx
import asyncio

class WeatherClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def get_current_weather(self, city=None, lat=None, lon=None):
        params = {}
        if city:
            params['city'] = city
        elif lat is not None and lon is not None:
            params['lat'] = lat
            params['lon'] = lon
        else:
            raise ValueError("Either city or lat/lon must be provided")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/weather", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_forecast(self, city, days=5):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather/forecast",
                params={"city": city, "days": days}
            )
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    client = WeatherClient()
    
    # Get current weather
    weather = await client.get_current_weather(city="London")
    print(weather)
    
    # Get forecast
    forecast = await client.get_forecast(city="London", days=3)
    print(forecast)

if __name__ == "__main__":
    asyncio.run(main())
```

### cURL Examples

**Get weather with error handling:**
```bash
#!/bin/bash

# Function to get weather with error handling
get_weather() {
    local city="$1"
    local response
    
    response=$(curl -s -w "HTTP_STATUS:%{http_code}" \
        "http://localhost:8000/weather?city=${city}")
    
    local body=$(echo "$response" | sed -E 's/HTTP_STATUS:[0-9]+$//')
    local status=$(echo "$response" | sed -E 's/.*HTTP_STATUS:([0-9]+)$/\1/')
    
    if [ "$status" -eq 200 ]; then
        echo "$body" | jq .
    else
        echo "Error: HTTP $status"
        echo "$body" | jq .
        return 1
    fi
}

# Usage
get_weather "London"
get_weather "InvalidCity"
```

## Webhooks and Real-time Updates

The current API version does not support webhooks or real-time updates. For live weather updates, you'll need to poll the endpoints at your desired interval.

**Recommended polling intervals:**
- Current weather: Every 10-30 minutes
- Forecast data: Every 1-3 hours
- Search history: As needed

## Rate Limiting Best Practices

1. **Implement exponential backoff** when receiving 429 errors
2. **Cache responses** to reduce API calls
3. **Batch requests** when possible
4. **Monitor rate limit headers** to avoid hitting limits
5. **Use appropriate polling intervals**

Example with retry logic:

```python
import asyncio
import httpx
from typing import Dict, Any

async def get_weather_with_retry(city: str, max_retries: int = 3) -> Dict[str, Any]:
    """Get weather with automatic retry and exponential backoff."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/weather",
                    params={"city": city}
                )
                
                if response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    
    raise Exception(f"Failed to get weather after {max_retries} attempts")
```