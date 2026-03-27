"""API request and response schemas.

This module defines Pydantic models for request validation and response
serialization. All API endpoints use these schemas to ensure type safety
and generate accurate OpenAPI documentation.

Features:
    - Request parameter validation with constraints
    - Response model serialization with proper types
    - Automatic OpenAPI schema generation
    - Custom JSON encoders for datetime objects
    - Error response standardization

Example:
    Using a response schema:
        weather_data = WeatherResponse(
            city="London",
            temperature=15.5,
            timestamp=datetime.utcnow()
        )
        return weather_data  # Automatically serialized to JSON

Models:
    - WeatherResponse: Current weather data response
    - ForecastResponse: Weather forecast response with multiple items
    - ForecastItem: Individual forecast entry (3-hour interval)
    - SearchHistoryResponse: Search history with pagination
    - ErrorResponse: Standardized error information
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    """Schema for weather response data."""

    city: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    visibility: Optional[int] = None
    wind_speed: float
    wind_deg: int
    clouds: int
    weather: str
    weather_description: str
    weather_icon: str
    timestamp: datetime

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ForecastItem(BaseModel):
    """Schema for a single forecast item."""

    datetime: datetime
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    weather: str
    weather_description: str
    weather_icon: str
    wind_speed: float
    wind_deg: int
    clouds: int
    pop: float  # Probability of precipitation

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ForecastResponse(BaseModel):
    """Schema for weather forecast response."""

    city: str
    country: str
    latitude: float
    longitude: float
    days_requested: int
    forecast: List[ForecastItem]

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchHistoryItem(BaseModel):
    """Schema for search history item."""

    id: int
    search_type: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    forecast_days: Optional[int] = None
    timestamp: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchHistoryResponse(BaseModel):
    """Schema for search history response."""

    total: int
    items: List[SearchHistoryItem]


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class DeleteHistoryResponse(BaseModel):
    """Schema for delete history response."""

    message: str
    deleted_count: int
