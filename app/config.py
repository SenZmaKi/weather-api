"""Configuration module for the Weather API application."""

from typing import Optional
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