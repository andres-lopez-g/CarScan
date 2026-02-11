"""
Vehicle API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.vehicle import SearchRequest, SearchResponse, VehicleListingResponse
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/search", response_model=SearchResponse)
async def search_vehicles(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for vehicle listings across all marketplaces.
    
    This endpoint:
    1. Triggers scraping of configured marketplaces
    2. Normalizes and stores results
    3. Applies filters (price, year, mileage, location)
    4. Calculates best offer scores
    5. Returns ranked results
    
    Args:
        search_request: Search parameters including query, location, and filters
        db: Database session
        
    Returns:
        SearchResponse with ranked vehicle listings
    """
    service = VehicleService(db)
    
    try:
        listings, total = await service.search_vehicles(search_request)
        
        # Convert to response models
        listing_responses = [
            VehicleListingResponse(
                id=listing.id,
                source=listing.source,
                title=listing.title,
                price=listing.price,
                year=listing.year,
                mileage=listing.mileage,
                latitude=listing.latitude,
                longitude=listing.longitude,
                city=listing.city,
                url=listing.url,
                created_at=listing.created_at,
                updated_at=listing.updated_at,
                score=listing.score,
                distance_km=getattr(listing, 'distance_km', None),
            )
            for listing in listings
        ]
        
        return SearchResponse(
            query=search_request.query,
            total_results=total,
            listings=listing_responses,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching vehicles: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CarScan API"}
