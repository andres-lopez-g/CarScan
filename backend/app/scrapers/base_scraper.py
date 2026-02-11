"""
Base scraper class for all marketplace scrapers.
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.core.config import settings


class BaseScraper(ABC):
    """
    Abstract base class for marketplace scrapers.
    
    All scrapers must implement the scrape method and return normalized data.
    """
    
    def __init__(self):
        self.delay_min = settings.scraping_delay_min
        self.delay_max = settings.scraping_delay_max
    
    @abstractmethod
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from the marketplace.
        
        Args:
            query: Search query (e.g., "Toyota Corolla 2015")
            city: City to search in (default: Medellín)
            
        Returns:
            List of normalized vehicle listing dictionaries
        """
        pass
    
    def normalize_listing(self, raw_data: Dict) -> Dict:
        """
        Normalize raw listing data to standard format.
        
        Args:
            raw_data: Raw data from marketplace
            
        Returns:
            Normalized dictionary with standard fields
        """
        return {
            "source": self.get_source_name(),
            "title": raw_data.get("title", ""),
            "price": self._parse_price(raw_data.get("price")),
            "year": self._parse_year(raw_data.get("year")),
            "mileage": self._parse_mileage(raw_data.get("mileage")),
            "latitude": raw_data.get("latitude"),
            "longitude": raw_data.get("longitude"),
            "city": raw_data.get("city"),
            "url": raw_data.get("url", ""),
        }
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of the marketplace source."""
        pass
    
    async def delay(self):
        """Add random delay between requests to be respectful."""
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """Parse price string to float."""
        if not price_str:
            return None
        try:
            # Remove currency symbols and separators
            clean = str(price_str).replace("$", "").replace(".", "").replace(",", "").strip()
            return float(clean)
        except (ValueError, AttributeError):
            return None
    
    def _parse_year(self, year_str: Optional[str]) -> Optional[int]:
        """Parse year string to int."""
        if not year_str:
            return None
        try:
            year = int(str(year_str).strip())
            if 1900 <= year <= 2030:
                return year
        except (ValueError, AttributeError):
            pass
        return None
    
    def _parse_mileage(self, mileage_str: Optional[str]) -> Optional[int]:
        """Parse mileage string to int."""
        if not mileage_str:
            return None
        try:
            # Remove units and separators
            clean = str(mileage_str).replace("km", "").replace(".", "").replace(",", "").strip()
            return int(clean)
        except (ValueError, AttributeError):
            return None
