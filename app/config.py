"""Configuration module for the Weather API application.

This module handles all application configuration using Pydantic Settings.
Configuration values are loaded from environment variables with sensible
defaults provided for development environments.

Features:
    - Environment variable-based configuration
    - Type validation and conversion
    - Default values for development
    - Cached settings instance to avoid reloading
    - Support for .env file loading

Configuration Categories:
    - OpenWeatherMap API: API key and base URL
    - Database: Connection URL and settings  
    - Application: Host, port, and debug mode
    - Rate Limiting: Request limits per minute
    - CORS: Allowed origins for cross-origin requests

Example:
    Using configuration in your code:
        settings = get_settings()
        api_key = settings.openweather_api_key
        debug_mode = settings.debug

Environment Variables:
    Required:
        - OPENWEATHER_API_KEY: Your OpenWeatherMap API key
    
    Optional (with defaults):
        - APP_HOST: Application host (default: "0.0.0.0")
        - APP_PORT: Application port (default: 8000)
        - DEBUG: Debug mode (default: False)
        - DATABASE_URL: Database connection string
        - RATE_LIMIT_PER_MINUTE: Rate limit (default: 60)
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenWeatherMap API Configuration
    openweather_api_key: str
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./weather.db"

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # CORS Configuration
    cors_origins: list[str] = ["*"]

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
