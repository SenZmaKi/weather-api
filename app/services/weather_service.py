"""Weather service for OpenWeatherMap API integration."""

from typing import Dict, Any
import httpx
from app.config import get_settings


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""

    def __init__(self) -> None:
        """Initialize weather service with configuration."""
        self.settings = get_settings()
        self.base_url = self.settings.openweather_base_url
        self.api_key = self.settings.openweather_api_key

    async def get_current_weather_by_city(self, city: str) -> Dict[str, Any]:
        """
        Get current weather data by city name.

        Args:
            city: Name of the city

        Returns:
            Weather data dictionary

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={"q": city, "appid": self.api_key, "units": "metric"},
            )
            response.raise_for_status()
            return response.json()

    async def get_current_weather_by_coordinates(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        Get current weather data by coordinates.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Weather data dictionary

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.api_key,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_weather_forecast(self, city: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for specified days.

        Args:
            city: Name of the city
            days: Number of days for forecast (1-5)

        Returns:
            Weather forecast data dictionary

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        # OpenWeatherMap free tier provides 5-day forecast with 3-hour intervals
        # We'll use the forecast endpoint and limit the results based on days
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/forecast",
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": days * 8,  # 8 intervals per day (3-hour intervals)
                },
            )
            response.raise_for_status()
            return response.json()
