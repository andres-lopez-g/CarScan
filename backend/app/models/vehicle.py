"""
Database models for CarScan.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from geoalchemy2 import Geography
from app.db.session import Base


class VehicleListing(Base):
    """Vehicle listing model with geospatial support."""
    
    __tablename__ = "vehicle_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=False, index=True)
    year = Column(Integer, nullable=True, index=True)
    mileage = Column(Integer, nullable=True, index=True)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String(200), nullable=True, index=True)
    url = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Normalized scoring fields
    price_normalized = Column(Float, nullable=True)
    mileage_normalized = Column(Float, nullable=True)
    year_normalized = Column(Float, nullable=True)
    score = Column(Float, nullable=True, index=True)
    
    def __repr__(self):
        return f"<VehicleListing(id={self.id}, title='{self.title}', price={self.price})>"


class Search(Base):
    """Search query tracking model."""
    
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    user_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    user_lat = Column(Float, nullable=True)
    user_lon = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Search(id={self.id}, query='{self.query}')>"
