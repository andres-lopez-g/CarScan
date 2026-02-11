"""
MercadoLibre Colombia scraper.
"""
from typing import List, Dict
import httpx
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class MercadoLibreScraper(BaseScraper):
    """Scraper for MercadoLibre Colombia marketplace."""
    
    BASE_URL = "https://listado.mercadolibre.com.co"
    
    def get_source_name(self) -> str:
        return "MercadoLibre"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from MercadoLibre.
        
        Args:
            query: Search query
            city: City to search in
            
        Returns:
            List of normalized vehicle listings
        """
        listings = []
        
        try:
            # Build search URL
            search_query = query.replace(" ", "-")
            url = f"{self.BASE_URL}/{search_query}"
            
            # Make request with proper headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                
                if response.status_code != 200:
                    return listings
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find listing items (this is a simplified example)
                # In production, you'd need to inspect actual MercadoLibre HTML structure
                items = soup.find_all('li', class_='ui-search-layout__item')
                
                for item in items[:20]:  # Limit to 20 results for MVP
                    try:
                        listing = self._parse_listing(item, city)
                        if listing:
                            listings.append(self.normalize_listing(listing))
                    except Exception as e:
                        # Skip problematic listings
                        continue
                    
                    # Rate limiting delay
                    await self.delay()
                    
        except Exception as e:
            # Log error in production
            pass
        
        return listings
    
    def _parse_listing(self, item, city: str) -> Dict:
        """
        Parse individual listing from BeautifulSoup element.
        
        Note: This is a simplified parser. Actual implementation would need
        to match current MercadoLibre HTML structure.
        """
        try:
            # Extract title
            title_elem = item.find('h2', class_='ui-search-item__title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract price
            price_elem = item.find('span', class_='price-tag-amount')
            price = price_elem.get_text(strip=True) if price_elem else None
            
            # Extract URL
            link_elem = item.find('a', class_='ui-search-link')
            url = link_elem.get('href') if link_elem else ""
            
            return {
                "title": title,
                "price": price,
                "year": None,  # Would need to parse from title or description
                "mileage": None,  # Would need to parse from attributes
                "latitude": None,  # Would need geocoding
                "longitude": None,
                "city": city,
                "url": url,
            }
        except Exception:
            return None
