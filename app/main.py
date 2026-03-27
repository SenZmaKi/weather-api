"""Main FastAPI application module.

This module sets up the FastAPI application with all necessary middleware,
routers, and configuration. It serves as the entry point for the Weather API service.

Features:
    - FastAPI application with async support
    - CORS middleware for cross-origin requests
    - Rate limiting to prevent API abuse
    - Static file serving for the web interface
    - Automatic API documentation generation
    - Database initialization on startup
    - Health check endpoint

Example:
    Run the application:
        $ uvicorn app.main:app --host 0.0.0.0 --port 8000

    Or use UV:
        $ uv run uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.models import init_db
from app.api.endpoints import router as weather_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles application startup and shutdown events:
    - Startup: Initialize database schema
    - Shutdown: Clean up resources and log shutdown
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Control to the application during its lifetime
    """
    # Startup
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Application shutting down")


# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)

# Create FastAPI app
app = FastAPI(
    title="Weather API Service",
    description="A Weather API service with external API integration and search history",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(weather_router)


@app.get("/", response_class=FileResponse)
async def root() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse("templates/index.html")


@app.get("/favicon.ico", response_class=FileResponse)
async def favicon() -> FileResponse:
    """Serve the favicon from the root path."""
    favicon_path = os.path.join("static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    # Return a 204 No Content if favicon doesn't exist
    return FileResponse(status_code=204)


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Provides a simple health check to verify the service is running.
    This endpoint is not rate-limited and can be used by load balancers
    and monitoring systems.
    
    Returns:
        dict: Health status information containing:
            - status: "healthy" if service is running
            - service: Service name identifier
    
    Example:
        >>> response = requests.get("http://localhost:8000/health")
        >>> print(response.json())
        {"status": "healthy", "service": "Weather API"}
    """
    return {"status": "healthy", "service": "Weather API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
