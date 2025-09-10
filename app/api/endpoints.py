"""API endpoints for weather service."""

from typing import Optional, Dict, Any
import json
from datetime import datetime
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import get_db, SearchHistory
from app.services import WeatherService
from app.api.schemas import (
    WeatherResponse,
    ForecastResponse,
    ForecastItem,
    SearchHistoryResponse,
    SearchHistoryItem,
    ErrorResponse,
    DeleteHistoryResponse,
)

router = APIRouter(prefix="/weather", tags=["weather"])


def parse_weather_data(data: Dict[str, Any]) -> WeatherResponse:
    """Parse OpenWeatherMap data to WeatherResponse schema."""
    return WeatherResponse(
        city=data.get("name"),
        country=data.get("sys", {}).get("country"),
        latitude=data["coord"]["lat"],
        longitude=data["coord"]["lon"],
        temperature=data["main"]["temp"],
        feels_like=data["main"]["feels_like"],
        temp_min=data["main"]["temp_min"],
        temp_max=data["main"]["temp_max"],
        pressure=data["main"]["pressure"],
        humidity=data["main"]["humidity"],
        visibility=data.get("visibility"),
        wind_speed=data["wind"]["speed"],
        wind_deg=data["wind"]["deg"],
        clouds=data["clouds"]["all"],
        weather=data["weather"][0]["main"],
        weather_description=data["weather"][0]["description"],
        weather_icon=data["weather"][0]["icon"],
        timestamp=datetime.fromtimestamp(data["dt"]),
    )


def parse_forecast_data(data: Dict[str, Any], days: int) -> ForecastResponse:
    """Parse OpenWeatherMap forecast data to ForecastResponse schema."""
    forecast_items = []

    for item in data["list"]:
        forecast_items.append(
            ForecastItem(
                datetime=datetime.fromtimestamp(item["dt"]),
                temperature=item["main"]["temp"],
                feels_like=item["main"]["feels_like"],
                temp_min=item["main"]["temp_min"],
                temp_max=item["main"]["temp_max"],
                pressure=item["main"]["pressure"],
                humidity=item["main"]["humidity"],
                weather=item["weather"][0]["main"],
                weather_description=item["weather"][0]["description"],
                weather_icon=item["weather"][0]["icon"],
                wind_speed=item["wind"]["speed"],
                wind_deg=item["wind"]["deg"],
                clouds=item["clouds"]["all"],
                pop=item.get("pop", 0),
            )
        )

    return ForecastResponse(
        city=data["city"]["name"],
        country=data["city"]["country"],
        latitude=data["city"]["coord"]["lat"],
        longitude=data["city"]["coord"]["lon"],
        days_requested=days,
        forecast=forecast_items,
    )


@router.get(
    "",
    response_model=WeatherResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get current weather",
    description="Get current weather by city name or coordinates",
)
async def get_weather(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude", ge=-90, le=90),
    lon: Optional[float] = Query(None, description="Longitude", ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
) -> WeatherResponse:
    """
    Get current weather data.

    Either city or both lat and lon must be provided.
    """
    weather_service = WeatherService()

    try:
        if city:
            # Get weather by city
            data = await weather_service.get_current_weather_by_city(city)
            search_type = "city"
        elif lat is not None and lon is not None:
            # Get weather by coordinates
            data = await weather_service.get_current_weather_by_coordinates(lat, lon)
            search_type = "coordinates"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'city' or both 'lat' and 'lon' parameters are required",
            )

        # Parse response
        weather_response = parse_weather_data(data)

        # Save to search history
        history_entry = SearchHistory(
            search_type=search_type,
            city=city if city else weather_response.city,
            latitude=lat if lat is not None else weather_response.latitude,
            longitude=lon if lon is not None else weather_response.longitude,
            response_data=json.dumps(data),
        )
        db.add(history_entry)
        await db.commit()

        return weather_response

    except HTTPException:
        raise
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data not found for the specified location",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather data: {str(e)}",
        )


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get weather forecast",
    description="Get weather forecast for 1-5 days",
)
async def get_weather_forecast(
    city: str = Query(..., description="City name"),
    days: int = Query(5, description="Number of days (1-5)", ge=1, le=5),
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    """Get weather forecast for the specified city and number of days."""
    weather_service = WeatherService()

    try:
        data = await weather_service.get_weather_forecast(city, days)

        # Parse response
        forecast_response = parse_forecast_data(data, days)

        # Save to search history
        history_entry = SearchHistory(
            search_type="forecast",
            city=city,
            latitude=forecast_response.latitude,
            longitude=forecast_response.longitude,
            forecast_days=days,
            response_data=json.dumps(data),
        )
        db.add(history_entry)
        await db.commit()

        return forecast_response

    except Exception as e:
        if "404" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Weather forecast not found for city: {city}",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather forecast: {str(e)}",
        )


@router.get(
    "/history",
    response_model=SearchHistoryResponse,
    summary="Get search history",
    description="Retrieve all weather search history",
)
async def get_search_history(
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000),
    offset: int = Query(0, description="Number of records to skip", ge=0),
    db: AsyncSession = Depends(get_db),
) -> SearchHistoryResponse:
    """Get weather search history."""
    # Get total count
    count_result = await db.execute(select(SearchHistory).limit(1))
    total = len(count_result.all())

    # Get paginated results
    result = await db.execute(
        select(SearchHistory)
        .order_by(SearchHistory.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    history_items = result.scalars().all()

    return SearchHistoryResponse(
        total=total,
        items=[SearchHistoryItem.model_validate(item) for item in history_items],
    )


@router.delete(
    "/history",
    response_model=DeleteHistoryResponse,
    summary="Clear search history",
    description="Delete all weather search history",
)
async def clear_search_history(
    db: AsyncSession = Depends(get_db),
) -> DeleteHistoryResponse:
    """Clear all weather search history."""
    result = await db.execute(delete(SearchHistory))
    await db.commit()

    return DeleteHistoryResponse(
        message="Search history cleared successfully", deleted_count=result.rowcount
    )
