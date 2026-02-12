"""
Vehicle service for business logic and data operations.
"""
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint
from geoalchemy2.elements import WKTElement

from app.models.vehicle import VehicleListing, Search
from app.schemas.vehicle import VehicleListingCreate, SearchRequest
from app.scrapers import MercadoLibreScraper, TuCarroScraper, BodegasYLocalesScraper, FincaRaizScraper, VendeTuNaveScraper
import asyncio


class VehicleService:
    """Service for managing vehicle listings and searches."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scrapers = [
            MercadoLibreScraper(),
            TuCarroScraper(),
            BodegasYLocalesScraper(),
            FincaRaizScraper(),
            VendeTuNaveScraper(),
        ]
    
    async def search_vehicles(
        self,
        search_request: SearchRequest
    ) -> tuple[List[VehicleListing], int]:
        """
        Search for vehicles across all marketplaces.
        
        Args:
            search_request: Search parameters
            
        Returns:
            Tuple of (listings, total_count)
        """
        # First, trigger scraping for new listings
        await self._scrape_all_sources(search_request.query, search_request.city)
        
        # Build query filters
        query = select(VehicleListing)
        filters = []
        
        # Price filters
        if search_request.min_price:
            filters.append(VehicleListing.price >= search_request.min_price)
        if search_request.max_price:
            filters.append(VehicleListing.price <= search_request.max_price)
        
        # Year filters
        if search_request.min_year:
            filters.append(VehicleListing.year >= search_request.min_year)
        if search_request.max_year:
            filters.append(VehicleListing.year <= search_request.max_year)
        
        # Mileage filter
        if search_request.max_mileage:
            filters.append(VehicleListing.mileage <= search_request.max_mileage)
        
        # City filter
        if search_request.city:
            filters.append(VehicleListing.city.ilike(f"%{search_request.city}%"))
        
        # Location-based filtering
        if search_request.user_lat and search_request.user_lon:
            # Create user location point
            user_point = WKTElement(
                f'POINT({search_request.user_lon} {search_request.user_lat})',
                srid=4326
            )
            
            # Filter by distance
            distance_meters = search_request.max_distance_km * 1000
            filters.append(
                ST_DWithin(
                    VehicleListing.location,
                    user_point,
                    distance_meters
                )
            )
        
        # Apply filters
        if filters:
            query = query.where(and_(*filters))
        
        # Order by score (best offers first)
        query = query.order_by(VehicleListing.score.asc().nullslast())
        
        # Execute query
        result = await self.db.execute(query)
        listings = result.scalars().all()
        
        # Calculate distances if user location provided
        if search_request.user_lat and search_request.user_lon:
            await self._calculate_distances(
                listings,
                search_request.user_lat,
                search_request.user_lon
            )
        
        # Record search
        await self._record_search(search_request)
        
        return listings, len(listings)
    
    async def _scrape_all_sources(self, query: str, city: Optional[str] = None):
        """
        Scrape all configured marketplace sources.
        
        Args:
            query: Search query
            city: City to search in
        """
        city = city or "Medellín"
        
        # Run all scrapers concurrently
        tasks = [scraper.scrape(query, city) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process and save listings
        for listings in results:
            if isinstance(listings, list):
                for listing_data in listings:
                    await self._save_listing(listing_data)
    
    async def _save_listing(self, listing_data: dict):
        """
        Save or update a vehicle listing.
        
        Args:
            listing_data: Normalized listing data
        """
        try:
            # Check if listing already exists (by URL)
            result = await self.db.execute(
                select(VehicleListing).where(VehicleListing.url == listing_data.get("url"))
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing listing
                for key, value in listing_data.items():
                    if key != "url":
                        setattr(existing, key, value)
            else:
                # Create new listing
                listing = VehicleListing(**listing_data)
                
                # Create geography point if coordinates available
                if listing_data.get("latitude") and listing_data.get("longitude"):
                    listing.location = WKTElement(
                        f'POINT({listing_data["longitude"]} {listing_data["latitude"]})',
                        srid=4326
                    )
                
                self.db.add(listing)
            
            await self.db.commit()
            
            # Calculate score after saving
            if not existing:
                await self._calculate_score(listing)
            else:
                await self._calculate_score(existing)
                
        except Exception as e:
            await self.db.rollback()
    
    async def _calculate_score(self, listing: VehicleListing):
        """
        Calculate best offer score for a listing.
        
        Lower score = better offer
        """
        try:
            # Get min/max values for normalization
            result = await self.db.execute(
                select(
                    func.min(VehicleListing.price).label('min_price'),
                    func.max(VehicleListing.price).label('max_price'),
                    func.min(VehicleListing.mileage).label('min_mileage'),
                    func.max(VehicleListing.mileage).label('max_mileage'),
                    func.min(VehicleListing.year).label('min_year'),
                    func.max(VehicleListing.year).label('max_year'),
                )
            )
            stats = result.one()
            
            # Normalize values (0-1 scale)
            if stats.min_price and stats.max_price and stats.max_price > stats.min_price:
                listing.price_normalized = (
                    (listing.price - stats.min_price) / (stats.max_price - stats.min_price)
                )
            
            if listing.mileage and stats.min_mileage and stats.max_mileage and stats.max_mileage > stats.min_mileage:
                listing.mileage_normalized = (
                    (listing.mileage - stats.min_mileage) / (stats.max_mileage - stats.min_mileage)
                )
            
            if listing.year and stats.min_year and stats.max_year and stats.max_year > stats.min_year:
                # For year, newer is better, so invert
                listing.year_normalized = 1 - (
                    (listing.year - stats.min_year) / (stats.max_year - stats.min_year)
                )
            
            # Calculate weighted score
            score = 0
            weight_sum = 0
            
            if listing.price_normalized is not None:
                score += listing.price_normalized * 0.5
                weight_sum += 0.5
            
            if listing.mileage_normalized is not None:
                score += listing.mileage_normalized * 0.3
                weight_sum += 0.3
            
            if listing.year_normalized is not None:
                score += listing.year_normalized * 0.2
                weight_sum += 0.2
            
            if weight_sum > 0:
                listing.score = score / weight_sum
            
            await self.db.commit()
            
        except Exception:
            await self.db.rollback()
    
    async def _calculate_distances(
        self,
        listings: List[VehicleListing],
        user_lat: float,
        user_lon: float
    ):
        """Calculate distance from user to each listing."""
        for listing in listings:
            if listing.latitude and listing.longitude:
                # Simple haversine distance calculation
                from math import radians, sin, cos, sqrt, atan2
                
                R = 6371  # Earth radius in km
                
                lat1 = radians(user_lat)
                lon1 = radians(user_lon)
                lat2 = radians(listing.latitude)
                lon2 = radians(listing.longitude)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                
                listing.distance_km = R * c
    
    async def _record_search(self, search_request: SearchRequest):
        """Record search query for analytics."""
        try:
            search = Search(
                query=search_request.query,
                user_lat=search_request.user_lat,
                user_lon=search_request.user_lon,
            )
            
            if search_request.user_lat and search_request.user_lon:
                search.user_location = WKTElement(
                    f'POINT({search_request.user_lon} {search_request.user_lat})',
                    srid=4326
                )
            
            self.db.add(search)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
