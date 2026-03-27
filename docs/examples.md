# Examples and Usage Patterns

This document provides practical examples and usage patterns for the Weather API service.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Client Libraries](#client-libraries)
- [Frontend Integration](#frontend-integration)
- [Mobile App Integration](#mobile-app-integration)
- [Batch Processing](#batch-processing)
- [Real-world Applications](#real-world-applications)
- [Testing Examples](#testing-examples)

## Basic Usage

### Getting Current Weather

**By City Name:**
```bash
# Simple city lookup
curl "http://localhost:8000/weather?city=London"

# City with spaces (URL encoded)
curl "http://localhost:8000/weather?city=New%20York"

# International cities
curl "http://localhost:8000/weather?city=Tokyo"
curl "http://localhost:8000/weather?city=São%20Paulo"
```

**By Coordinates:**
```bash
# Major cities
curl "http://localhost:8000/weather?lat=51.5074&lon=-0.1278"  # London
curl "http://localhost:8000/weather?lat=40.7128&lon=-74.0060" # New York
curl "http://localhost:8000/weather?lat=35.6762&lon=139.6503" # Tokyo

# Precise locations
curl "http://localhost:8000/weather?lat=37.7749&lon=-122.4194" # San Francisco
```

**Example Response:**
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
  "timestamp": "2024-01-01T15:30:00"
}
```

### Getting Weather Forecast

**Basic Forecast:**
```bash
# 5-day forecast (default)
curl "http://localhost:8000/weather/forecast?city=London"

# 3-day forecast
curl "http://localhost:8000/weather/forecast?city=London&days=3"

# 1-day detailed forecast
curl "http://localhost:8000/weather/forecast?city=London&days=1"
```

### Managing Search History

**View History:**
```bash
# Get recent searches
curl "http://localhost:8000/weather/history"

# Get limited results
curl "http://localhost:8000/weather/history?limit=10"

# Paginated results
curl "http://localhost:8000/weather/history?limit=10&offset=20"
```

**Clear History:**
```bash
curl -X DELETE "http://localhost:8000/weather/history"
```

## Client Libraries

### Python Client

**Simple Client:**
```python
import asyncio
import httpx
from typing import Dict, Any, List, Optional

class WeatherAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(30.0)
    
    async def get_current_weather(
        self, 
        city: Optional[str] = None, 
        lat: Optional[float] = None, 
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get current weather data."""
        params = {}
        if city:
            params['city'] = city
        elif lat is not None and lon is not None:
            params['lat'] = lat
            params['lon'] = lon
        else:
            raise ValueError("Either city or lat/lon must be provided")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/weather", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_forecast(self, city: str, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast."""
        params = {"city": city, "days": days}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/weather/forecast", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_history(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get search history."""
        params = {"limit": limit, "offset": offset}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/weather/history", params=params)
            response.raise_for_status()
            return response.json()
    
    async def clear_history(self) -> Dict[str, Any]:
        """Clear search history."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(f"{self.base_url}/weather/history")
            response.raise_for_status()
            return response.json()

# Usage example
async def main():
    client = WeatherAPIClient()
    
    # Get current weather
    weather = await client.get_current_weather(city="London")
    print(f"Temperature in London: {weather['temperature']}°C")
    
    # Get forecast
    forecast = await client.get_forecast(city="London", days=3)
    print(f"3-day forecast has {len(forecast['forecast'])} entries")
    
    # Get history
    history = await client.get_history(limit=5)
    print(f"Recent searches: {history['total']} total")

if __name__ == "__main__":
    asyncio.run(main())
```

**Advanced Client with Error Handling:**
```python
import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherAPIError(Exception):
    """Custom exception for Weather API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class AdvancedWeatherClient:
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        retry_attempts: int = 3,
        cache_duration: int = 300  # 5 minutes
    ):
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)
        self.retry_attempts = retry_attempts
        self.cache_duration = cache_duration
        self._cache = {}
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for request."""
        sorted_params = sorted(params.items())
        return f"{endpoint}:{json.dumps(sorted_params, sort_keys=True)}"
    
    def _is_cached_valid(self, timestamp: datetime) -> bool:
        """Check if cached data is still valid."""
        return datetime.utcnow() - timestamp < timedelta(seconds=self.cache_duration)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and caching."""
        if use_cache and method == "GET" and params:
            cache_key = self._get_cache_key(endpoint, params)
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if self._is_cached_valid(timestamp):
                    logger.debug(f"Using cached data for {endpoint}")
                    return cached_data
        
        last_exception = None
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}", params=params)
                    elif method == "DELETE":
                        response = await client.delete(f"{self.base_url}{endpoint}")
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    if response.status_code == 429:  # Rate limited
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Cache successful GET requests
                    if use_cache and method == "GET" and params:
                        cache_key = self._get_cache_key(endpoint, params)
                        self._cache[cache_key] = (data, datetime.utcnow())
                    
                    return data
                    
            except httpx.HTTPStatusError as e:
                error_detail = "Unknown error"
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", str(e))
                except:
                    error_detail = str(e)
                
                if e.response.status_code in [404, 400]:  # Don't retry client errors
                    raise WeatherAPIError(error_detail, e.response.status_code)
                
                last_exception = WeatherAPIError(error_detail, e.response.status_code)
                
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_exception = WeatherAPIError(f"Request timeout: {str(e)}")
                
            except Exception as e:
                last_exception = WeatherAPIError(f"Unexpected error: {str(e)}")
            
            if attempt < self.retry_attempts - 1:
                wait_time = (2 ** attempt) * 1
                logger.warning(f"Request failed, retrying in {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
        
        raise last_exception or WeatherAPIError("Max retry attempts exceeded")
    
    async def get_current_weather(
        self, 
        city: Optional[str] = None, 
        lat: Optional[float] = None, 
        lon: Optional[float] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get current weather with error handling and caching."""
        params = {}
        if city:
            params['city'] = city
        elif lat is not None and lon is not None:
            params['lat'] = lat
            params['lon'] = lon
        else:
            raise ValueError("Either city or lat/lon must be provided")
        
        return await self._make_request("GET", "/weather", params, use_cache)
    
    async def get_forecast(self, city: str, days: int = 5, use_cache: bool = True) -> Dict[str, Any]:
        """Get weather forecast with error handling and caching."""
        params = {"city": city, "days": days}
        return await self._make_request("GET", "/weather/forecast", params, use_cache)
    
    async def get_multiple_cities_weather(self, cities: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get weather for multiple cities concurrently."""
        tasks = []
        for city in cities:
            task = asyncio.create_task(
                self.get_current_weather(city=city),
                name=f"weather-{city}"
            )
            tasks.append((city, task))
        
        results = {}
        for city, task in tasks:
            try:
                results[city] = await task
            except WeatherAPIError as e:
                logger.error(f"Failed to get weather for {city}: {e}")
                results[city] = {"error": str(e), "status_code": getattr(e, 'status_code', None)}
        
        return results
    
    def clear_cache(self):
        """Clear the request cache."""
        self._cache.clear()

# Usage example
async def advanced_example():
    client = AdvancedWeatherClient(cache_duration=600)  # 10-minute cache
    
    try:
        # Get weather for multiple cities
        cities = ["London", "Paris", "Tokyo", "New York", "Sydney"]
        weather_data = await client.get_multiple_cities_weather(cities)
        
        for city, data in weather_data.items():
            if "error" in data:
                print(f"Error for {city}: {data['error']}")
            else:
                print(f"{city}: {data['temperature']}°C, {data['weather_description']}")
        
        # Get forecast with caching
        forecast = await client.get_forecast("London", days=3)
        print(f"London forecast: {len(forecast['forecast'])} entries")
        
        # Second call will use cache
        cached_forecast = await client.get_forecast("London", days=3)
        print("Retrieved from cache (should be instant)")
        
    except WeatherAPIError as e:
        print(f"API Error: {e} (Status: {e.status_code})")

if __name__ == "__main__":
    asyncio.run(advanced_example())
```

### JavaScript/Node.js Client

**Simple Client:**
```javascript
const axios = require('axios');

class WeatherAPIClient {
    constructor(baseURL = 'http://localhost:8000', timeout = 30000) {
        this.client = axios.create({
            baseURL,
            timeout,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async getCurrentWeather(params) {
        const { city, lat, lon } = params;
        
        if (!city && !(lat && lon)) {
            throw new Error('Either city or lat/lon must be provided');
        }

        const queryParams = city ? { city } : { lat, lon };
        
        try {
            const response = await this.client.get('/weather', { params: queryParams });
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    async getForecast(city, days = 5) {
        try {
            const response = await this.client.get('/weather/forecast', {
                params: { city, days }
            });
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    async getHistory(limit = 100, offset = 0) {
        try {
            const response = await this.client.get('/weather/history', {
                params: { limit, offset }
            });
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    async clearHistory() {
        try {
            const response = await this.client.delete('/weather/history');
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    handleError(error) {
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;
            throw new Error(`API Error ${status}: ${data.message || data.error || 'Unknown error'}`);
        } else if (error.request) {
            // Request was made but no response received
            throw new Error('Network error: No response from server');
        } else {
            // Something else happened
            throw new Error(`Request error: ${error.message}`);
        }
    }
}

// Usage example
async function main() {
    const client = new WeatherAPIClient();

    try {
        // Get current weather
        const weather = await client.getCurrentWeather({ city: 'London' });
        console.log(`Temperature in London: ${weather.temperature}°C`);

        // Get forecast
        const forecast = await client.getForecast('London', 3);
        console.log(`3-day forecast has ${forecast.forecast.length} entries`);

        // Get weather by coordinates
        const coordWeather = await client.getCurrentWeather({
            lat: 51.5074,
            lon: -0.1278
        });
        console.log(`Weather at coordinates: ${coordWeather.temperature}°C`);

    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

**Browser Client (ES6 Modules):**
```javascript
class BrowserWeatherClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error('Network error: Could not connect to API');
            }
            throw error;
        }
    }

    async getCurrentWeather(params) {
        const { city, lat, lon } = params;
        const queryParams = new URLSearchParams();

        if (city) {
            queryParams.append('city', city);
        } else if (lat && lon) {
            queryParams.append('lat', lat.toString());
            queryParams.append('lon', lon.toString());
        } else {
            throw new Error('Either city or lat/lon must be provided');
        }

        return await this.request(`/weather?${queryParams}`);
    }

    async getForecast(city, days = 5) {
        const queryParams = new URLSearchParams({
            city,
            days: days.toString()
        });
        
        return await this.request(`/weather/forecast?${queryParams}`);
    }

    async getHistory(limit = 100, offset = 0) {
        const queryParams = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString()
        });
        
        return await this.request(`/weather/history?${queryParams}`);
    }

    async clearHistory() {
        return await this.request('/weather/history', { method: 'DELETE' });
    }
}

// Usage in browser
const weatherClient = new BrowserWeatherClient();

// Example with async/await
async function displayWeather() {
    try {
        const weather = await weatherClient.getCurrentWeather({ city: 'London' });
        document.getElementById('temperature').textContent = `${weather.temperature}°C`;
        document.getElementById('description').textContent = weather.weather_description;
    } catch (error) {
        console.error('Weather fetch failed:', error.message);
        document.getElementById('error').textContent = `Error: ${error.message}`;
    }
}

// Example with Promise chains
weatherClient.getCurrentWeather({ city: 'Paris' })
    .then(weather => {
        console.log('Paris weather:', weather);
    })
    .catch(error => {
        console.error('Error:', error.message);
    });
```

## Frontend Integration

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const WeatherComponent = () => {
    const [weather, setWeather] = useState(null);
    const [forecast, setForecast] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [city, setCity] = useState('London');

    const weatherAPI = axios.create({
        baseURL: 'http://localhost:8000',
        timeout: 10000
    });

    const fetchWeather = async (cityName) => {
        setLoading(true);
        setError(null);
        
        try {
            const [weatherResponse, forecastResponse] = await Promise.all([
                weatherAPI.get('/weather', { params: { city: cityName } }),
                weatherAPI.get('/weather/forecast', { params: { city: cityName, days: 3 } })
            ]);
            
            setWeather(weatherResponse.data);
            setForecast(forecastResponse.data);
        } catch (err) {
            setError(err.response?.data?.message || err.message || 'Failed to fetch weather');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWeather(city);
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (city.trim()) {
            fetchWeather(city.trim());
        }
    };

    return (
        <div className="weather-container">
            <form onSubmit={handleSubmit} className="search-form">
                <input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="Enter city name"
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !city.trim()}>
                    {loading ? 'Loading...' : 'Get Weather'}
                </button>
            </form>

            {error && <div className="error">Error: {error}</div>}

            {weather && (
                <div className="current-weather">
                    <h2>{weather.city}, {weather.country}</h2>
                    <div className="temperature">{Math.round(weather.temperature)}°C</div>
                    <div className="description">{weather.weather_description}</div>
                    <div className="details">
                        <span>Feels like: {Math.round(weather.feels_like)}°C</span>
                        <span>Humidity: {weather.humidity}%</span>
                        <span>Wind: {weather.wind_speed} m/s</span>
                    </div>
                </div>
            )}

            {forecast && (
                <div className="forecast">
                    <h3>3-Day Forecast</h3>
                    <div className="forecast-items">
                        {forecast.forecast.slice(0, 8).map((item, index) => (
                            <div key={index} className="forecast-item">
                                <div className="time">
                                    {new Date(item.datetime).toLocaleString('en-US', {
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </div>
                                <div className="temp">{Math.round(item.temperature)}°C</div>
                                <div className="desc">{item.weather_description}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default WeatherComponent;
```

### Vue.js Component Example

```vue
<template>
  <div class="weather-app">
    <form @submit.prevent="fetchWeather" class="search-form">
      <input
        v-model="city"
        type="text"
        placeholder="Enter city name"
        :disabled="loading"
        required
      />
      <button type="submit" :disabled="loading || !city.trim()">
        {{ loading ? 'Loading...' : 'Get Weather' }}
      </button>
    </form>

    <div v-if="error" class="error">
      Error: {{ error }}
    </div>

    <div v-if="weather" class="weather-display">
      <h2>{{ weather.city }}, {{ weather.country }}</h2>
      
      <div class="current-weather">
        <div class="temperature">{{ Math.round(weather.temperature) }}°C</div>
        <div class="description">{{ weather.weather_description }}</div>
        
        <div class="weather-details">
          <div class="detail-item">
            <span class="label">Feels like:</span>
            <span class="value">{{ Math.round(weather.feels_like) }}°C</span>
          </div>
          <div class="detail-item">
            <span class="label">Humidity:</span>
            <span class="value">{{ weather.humidity }}%</span>
          </div>
          <div class="detail-item">
            <span class="label">Wind Speed:</span>
            <span class="value">{{ weather.wind_speed }} m/s</span>
          </div>
          <div class="detail-item">
            <span class="label">Pressure:</span>
            <span class="value">{{ weather.pressure }} hPa</span>
          </div>
        </div>
      </div>

      <div v-if="forecast" class="forecast-section">
        <h3>{{ forecast.days_requested }}-Day Forecast</h3>
        <div class="forecast-grid">
          <div
            v-for="(item, index) in forecast.forecast.slice(0, 8)"
            :key="index"
            class="forecast-card"
          >
            <div class="forecast-time">
              {{ formatDate(item.datetime) }}
            </div>
            <div class="forecast-temp">{{ Math.round(item.temperature) }}°C</div>
            <div class="forecast-desc">{{ item.weather_description }}</div>
            <div class="forecast-details">
              <small>💧 {{ item.pop * 100 }}%</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'WeatherApp',
  data() {
    return {
      city: 'London',
      weather: null,
      forecast: null,
      loading: false,
      error: null,
      weatherAPI: axios.create({
        baseURL: 'http://localhost:8000',
        timeout: 10000
      })
    };
  },
  mounted() {
    this.fetchWeather();
  },
  methods: {
    async fetchWeather() {
      if (!this.city.trim()) return;
      
      this.loading = true;
      this.error = null;
      
      try {
        const [weatherResponse, forecastResponse] = await Promise.all([
          this.weatherAPI.get('/weather', { 
            params: { city: this.city.trim() } 
          }),
          this.weatherAPI.get('/weather/forecast', { 
            params: { city: this.city.trim(), days: 3 } 
          })
        ]);
        
        this.weather = weatherResponse.data;
        this.forecast = forecastResponse.data;
      } catch (error) {
        this.error = error.response?.data?.message || 
                   error.message || 
                   'Failed to fetch weather data';
      } finally {
        this.loading = false;
      }
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};
</script>

<style scoped>
.weather-app {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-form input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-form button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  background: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.current-weather {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.temperature {
  font-size: 3rem;
  font-weight: bold;
  text-align: center;
}

.description {
  font-size: 1.2rem;
  text-align: center;
  margin-bottom: 20px;
  text-transform: capitalize;
}

.weather-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
}

.forecast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.forecast-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.forecast-time {
  font-weight: bold;
  margin-bottom: 5px;
}

.forecast-temp {
  font-size: 1.5rem;
  color: #007bff;
}

.forecast-desc {
  font-size: 0.9rem;
  color: #666;
  text-transform: capitalize;
}
</style>
```

## Mobile App Integration

### React Native Example

```jsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const WeatherApp = () => {
  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [city, setCity] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const API_BASE = 'https://your-domain.com'; // Replace with your API URL

  useEffect(() => {
    loadSavedCity();
    loadSearchHistory();
  }, []);

  const loadSavedCity = async () => {
    try {
      const savedCity = await AsyncStorage.getItem('lastCity');
      if (savedCity) {
        setCity(savedCity);
        fetchWeather(savedCity);
      }
    } catch (error) {
      console.error('Error loading saved city:', error);
    }
  };

  const loadSearchHistory = async () => {
    try {
      const savedHistory = await AsyncStorage.getItem('searchHistory');
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory));
      }
    } catch (error) {
      console.error('Error loading search history:', error);
    }
  };

  const saveSearchHistory = async (newCity) => {
    try {
      const updatedHistory = [newCity, ...history.filter(c => c !== newCity)].slice(0, 5);
      setHistory(updatedHistory);
      await AsyncStorage.setItem('searchHistory', JSON.stringify(updatedHistory));
      await AsyncStorage.setItem('lastCity', newCity);
    } catch (error) {
      console.error('Error saving search history:', error);
    }
  };

  const fetchWeather = async (cityName) => {
    if (!cityName.trim()) {
      Alert.alert('Error', 'Please enter a city name');
      return;
    }

    setLoading(true);
    
    try {
      const [weatherResponse, forecastResponse] = await Promise.all([
        fetch(`${API_BASE}/weather?city=${encodeURIComponent(cityName)}`),
        fetch(`${API_BASE}/weather/forecast?city=${encodeURIComponent(cityName)}&days=3`)
      ]);

      if (!weatherResponse.ok || !forecastResponse.ok) {
        const errorData = await weatherResponse.json().catch(() => ({}));
        throw new Error(errorData.message || 'Failed to fetch weather data');
      }

      const weatherData = await weatherResponse.json();
      const forecastData = await forecastResponse.json();

      setWeather(weatherData);
      setForecast(forecastData);
      saveSearchHistory(cityName);
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to fetch weather data');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchWeather(city);
  };

  const selectHistoryItem = (historyCity) => {
    setCity(historyCity);
    fetchWeather(historyCity);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.input}
          value={city}
          onChangeText={setCity}
          placeholder="Enter city name"
          onSubmitEditing={handleSearch}
          editable={!loading}
        />
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleSearch}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>Search</Text>
          )}
        </TouchableOpacity>
      </View>

      {history.length > 0 && (
        <View style={styles.historyContainer}>
          <Text style={styles.historyTitle}>Recent Searches:</Text>
          <View style={styles.historyItems}>
            {history.map((historyCity, index) => (
              <TouchableOpacity
                key={index}
                style={styles.historyItem}
                onPress={() => selectHistoryItem(historyCity)}
              >
                <Text style={styles.historyItemText}>{historyCity}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {weather && (
        <View style={styles.weatherContainer}>
          <Text style={styles.cityName}>{weather.city}, {weather.country}</Text>
          <Text style={styles.temperature}>{Math.round(weather.temperature)}°C</Text>
          <Text style={styles.description}>{weather.weather_description}</Text>
          
          <View style={styles.detailsContainer}>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Feels like</Text>
              <Text style={styles.detailValue}>{Math.round(weather.feels_like)}°C</Text>
            </View>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Humidity</Text>
              <Text style={styles.detailValue}>{weather.humidity}%</Text>
            </View>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Wind Speed</Text>
              <Text style={styles.detailValue}>{weather.wind_speed} m/s</Text>
            </View>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Pressure</Text>
              <Text style={styles.detailValue}>{weather.pressure} hPa</Text>
            </View>
          </View>
        </View>
      )}

      {forecast && (
        <View style={styles.forecastContainer}>
          <Text style={styles.forecastTitle}>3-Day Forecast</Text>
          {forecast.forecast.slice(0, 8).map((item, index) => (
            <View key={index} style={styles.forecastItem}>
              <Text style={styles.forecastTime}>
                {new Date(item.datetime).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </Text>
              <Text style={styles.forecastTemp}>{Math.round(item.temperature)}°C</Text>
              <Text style={styles.forecastDesc}>{item.weather_description}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  searchContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  input: {
    flex: 1,
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    marginRight: 10,
  },
  button: {
    backgroundColor: '#007bff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  historyContainer: {
    marginBottom: 20,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  historyItems: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  historyItem: {
    backgroundColor: '#e9ecef',
    padding: 8,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  historyItemText: {
    fontSize: 14,
  },
  weatherContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    alignItems: 'center',
  },
  cityName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  temperature: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: 10,
  },
  description: {
    fontSize: 18,
    color: '#666',
    textTransform: 'capitalize',
    marginBottom: 20,
  },
  detailsContainer: {
    width: '100%',
  },
  detailItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  detailLabel: {
    fontSize: 16,
    color: '#666',
  },
  detailValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  forecastContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
  },
  forecastTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  forecastItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  forecastTime: {
    flex: 2,
    fontSize: 14,
    fontWeight: '500',
  },
  forecastTemp: {
    flex: 1,
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007bff',
    textAlign: 'center',
  },
  forecastDesc: {
    flex: 2,
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
    textAlign: 'right',
  },
});

export default WeatherApp;
```

## Batch Processing

### Processing Multiple Cities

```python
import asyncio
import csv
from typing import List, Dict, Any
from datetime import datetime
import json

async def process_cities_batch(cities: List[str], output_file: str = None):
    """Process weather data for multiple cities in batch."""
    from examples import AdvancedWeatherClient  # Assuming previous example
    
    client = AdvancedWeatherClient()
    results = []
    
    print(f"Processing weather data for {len(cities)} cities...")
    
    # Process in batches to avoid overwhelming the API
    batch_size = 10
    for i in range(0, len(cities), batch_size):
        batch = cities[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}: {', '.join(batch)}")
        
        batch_results = await client.get_multiple_cities_weather(batch)
        
        for city, data in batch_results.items():
            result = {
                'city': city,
                'timestamp': datetime.utcnow().isoformat(),
                'success': 'error' not in data
            }
            
            if 'error' not in data:
                result.update({
                    'temperature': data['temperature'],
                    'feels_like': data['feels_like'],
                    'humidity': data['humidity'],
                    'wind_speed': data['wind_speed'],
                    'weather': data['weather'],
                    'weather_description': data['weather_description'],
                    'country': data['country'],
                    'latitude': data['latitude'],
                    'longitude': data['longitude']
                })
            else:
                result['error'] = data['error']
            
            results.append(result)
        
        # Small delay between batches to be respectful to the API
        if i + batch_size < len(cities):
            await asyncio.sleep(2)
    
    # Save results
    if output_file:
        if output_file.endswith('.json'):
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        elif output_file.endswith('.csv'):
            fieldnames = ['city', 'timestamp', 'success', 'temperature', 'feels_like', 
                         'humidity', 'wind_speed', 'weather', 'weather_description', 
                         'country', 'latitude', 'longitude', 'error']
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\nBatch processing complete:")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    
    if output_file:
        print(f"Results saved to: {output_file}")
    
    return results

# Example usage
async def main():
    # Major world cities
    cities = [
        'London', 'Paris', 'Tokyo', 'New York', 'Sydney',
        'Mumbai', 'Cairo', 'São Paulo', 'Moscow', 'Beijing',
        'Los Angeles', 'Toronto', 'Berlin', 'Madrid', 'Rome',
        'Bangkok', 'Seoul', 'Mexico City', 'Buenos Aires', 'Lagos'
    ]
    
    results = await process_cities_batch(cities, 'weather_batch_results.csv')
    
    # Find hottest and coldest cities
    successful_results = [r for r in results if r['success']]
    if successful_results:
        hottest = max(successful_results, key=lambda x: x['temperature'])
        coldest = min(successful_results, key=lambda x: x['temperature'])
        
        print(f"\n🌡️ Temperature extremes:")
        print(f"Hottest: {hottest['city']} - {hottest['temperature']}°C")
        print(f"Coldest: {coldest['city']} - {coldest['temperature']}°C")

if __name__ == "__main__":
    asyncio.run(main())
```

### Scheduled Weather Monitoring

```python
import asyncio
import schedule
import time
from datetime import datetime, timedelta
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_monitor.log'),
        logging.StreamHandler()
    ]
)

class WeatherMonitor:
    def __init__(self, db_path: str = 'weather_monitor.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize monitoring database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                temperature REAL,
                humidity INTEGER,
                weather_description TEXT,
                wind_speed REAL,
                pressure INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_city_timestamp 
            ON weather_snapshots(city, timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    async def collect_weather_data(self, cities: List[str]):
        """Collect current weather data for specified cities."""
        from examples import AdvancedWeatherClient
        
        client = AdvancedWeatherClient()
        timestamp = datetime.utcnow()
        
        logging.info(f"Collecting weather data for {len(cities)} cities")
        
        weather_data = await client.get_multiple_cities_weather(cities)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        successful = 0
        for city, data in weather_data.items():
            if 'error' not in data:
                cursor.execute('''
                    INSERT INTO weather_snapshots 
                    (city, timestamp, temperature, humidity, weather_description, wind_speed, pressure)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    city, timestamp, data['temperature'], data['humidity'],
                    data['weather_description'], data['wind_speed'], data['pressure']
                ))
                successful += 1
            else:
                logging.error(f"Failed to get weather for {city}: {data['error']}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully collected data for {successful}/{len(cities)} cities")
    
    def get_temperature_alerts(self, threshold_hot: float = 35.0, threshold_cold: float = -10.0):
        """Check for extreme temperature alerts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest data for each city
        cursor.execute('''
            SELECT city, temperature, timestamp, weather_description
            FROM weather_snapshots w1
            WHERE timestamp = (
                SELECT MAX(timestamp) 
                FROM weather_snapshots w2 
                WHERE w2.city = w1.city
            )
            AND (temperature > ? OR temperature < ?)
            ORDER BY temperature DESC
        ''', (threshold_hot, threshold_cold))
        
        alerts = cursor.fetchall()
        conn.close()
        
        if alerts:
            logging.warning(f"Temperature alerts: {len(alerts)} cities with extreme temperatures")
            for city, temp, timestamp, description in alerts:
                alert_type = "HOT" if temp > threshold_hot else "COLD"
                logging.warning(f"  {alert_type}: {city} - {temp}°C ({description})")
        
        return alerts
    
    def generate_daily_report(self):
        """Generate daily weather summary report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        cursor.execute('''
            SELECT 
                city,
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(humidity) as avg_humidity,
                COUNT(*) as readings
            FROM weather_snapshots
            WHERE timestamp >= ?
            GROUP BY city
            ORDER BY avg_temp DESC
        ''', (yesterday,))
        
        report_data = cursor.fetchall()
        conn.close()
        
        if report_data:
            logging.info("=== DAILY WEATHER REPORT ===")
            logging.info(f"Period: {yesterday.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}")
            logging.info(f"Cities monitored: {len(report_data)}")
            
            for city, avg_temp, min_temp, max_temp, avg_humidity, readings in report_data:
                logging.info(f"{city:15s} | Avg: {avg_temp:5.1f}°C | Range: {min_temp:4.1f}°C - {max_temp:4.1f}°C | Humidity: {avg_humidity:4.1f}% | Readings: {readings}")
        
        return report_data

# Usage example
async def run_weather_monitoring():
    monitor = WeatherMonitor()
    
    # Cities to monitor
    cities = ['London', 'New York', 'Tokyo', 'Sydney', 'Mumbai']
    
    # Collect data
    await monitor.collect_weather_data(cities)
    
    # Check for alerts
    monitor.get_temperature_alerts(threshold_hot=30.0, threshold_cold=0.0)

def schedule_monitoring():
    """Set up scheduled monitoring tasks."""
    # Collect weather data every 30 minutes
    schedule.every(30).minutes.do(lambda: asyncio.run(run_weather_monitoring()))
    
    # Generate daily report at 9 AM
    schedule.every().day.at("09:00").do(lambda: WeatherMonitor().generate_daily_report())
    
    logging.info("Weather monitoring scheduled:")
    logging.info("  - Data collection: Every 30 minutes")
    logging.info("  - Daily report: 09:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    schedule_monitoring()
```

This comprehensive examples documentation provides practical, real-world usage patterns for the Weather API service, from simple API calls to complex batch processing and monitoring systems.