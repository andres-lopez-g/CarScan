"""
Core configuration settings for CarScan application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # App Info
    app_name: str = "CarScan"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://carscan:carscan@db:5432/carscan"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # API
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Scraping
    scraping_delay_min: int = 2
    scraping_delay_max: int = 5
    max_concurrent_scrapers: int = 2
    
    # Geospatial
    default_search_radius_km: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
