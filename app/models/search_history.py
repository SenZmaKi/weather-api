"""Search history model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from .database import Base


class SearchHistory(Base):
    """Model for storing weather search history."""
    
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    search_type = Column(String(50), nullable=False)  # 'city', 'coordinates', 'forecast'
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    forecast_days = Column(Integer, nullable=True)
    response_data = Column(Text, nullable=False)  # JSON string of the response
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of SearchHistory."""
        return f"<SearchHistory(id={self.id}, type={self.search_type}, timestamp={self.timestamp})>"