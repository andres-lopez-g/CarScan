"""
API package initialization.
"""
from fastapi import APIRouter
from .vehicles import router as vehicles_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(vehicles_router)

__all__ = ["api_router"]
