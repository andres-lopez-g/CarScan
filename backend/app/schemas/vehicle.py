"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class VehicleListingBase(BaseModel):
    """Base schema for vehicle listing."""
    
    source: str = Field(..., description="Source marketplace (e.g., MercadoLibre, OLX)")
    title: str = Field(..., description="Vehicle listing title")
    price: float = Field(..., ge=0, description="Vehicle price in COP")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Vehicle year")
    mileage: Optional[int] = Field(None, ge=0, description="Vehicle mileage in km")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    city: Optional[str] = Field(None, description="City name")
    url: str = Field(..., description="Original listing URL")


class VehicleListingCreate(VehicleListingBase):
    """Schema for creating a vehicle listing."""
    pass


class VehicleListingResponse(VehicleListingBase):
    """Schema for vehicle listing API response."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    score: Optional[float] = Field(None, description="Best offer score (lower is better)")
    distance_km: Optional[float] = Field(None, description="Distance from user location in km")
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Schema for vehicle search request."""
    
    query: str = Field(..., description="Search query (e.g., 'Toyota Corolla 2015')")
    user_lat: Optional[float] = Field(None, ge=-90, le=90, description="User latitude")
    user_lon: Optional[float] = Field(None, ge=-180, le=180, description="User longitude")
    max_distance_km: Optional[int] = Field(50, ge=1, le=500, description="Max search radius in km")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    min_year: Optional[int] = Field(None, ge=1900, description="Minimum year filter")
    max_year: Optional[int] = Field(None, le=2030, description="Maximum year filter")
    max_mileage: Optional[int] = Field(None, ge=0, description="Maximum mileage filter")
    city: Optional[str] = Field(None, description="City filter")


class SearchResponse(BaseModel):
    """Schema for search API response."""
    
    query: str
    total_results: int
    listings: list[VehicleListingResponse]
    
    class Config:
        from_attributes = True
