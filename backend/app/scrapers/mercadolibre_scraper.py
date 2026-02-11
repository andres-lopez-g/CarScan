"""
MercadoLibre Colombia scraper using Playwright for JavaScript rendering.
"""
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)


class MercadoLibreScraper(BaseScraper):
    """Scraper for MercadoLibre Colombia marketplace using Playwright."""
    
    BASE_URL = "https://carros.mercadolibre.com.co"
    
    def get_source_name(self) -> str:
        return "MercadoLibre"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from MercadoLibre using Playwright.
        
        This implementation uses Playwright to handle JavaScript-rendered content
        with stealth techniques to avoid 403 Forbidden errors.
        
        Args:
            query: Search query
            city: City to search in
            
        Returns:
            List of normalized vehicle listings
        """
        listings = []
        
        try:
            async with async_playwright() as p:
                # Launch browser with anti-detection flags
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )
                
                # Create context with realistic user agent and headers
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale='es-CO',
                    timezone_id='America/Bogota',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                # Remove webdriver property to avoid detection
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                page = await context.new_page()
                
                try:
                    # Build search URL
                    search_query = query.replace(" ", "-").lower()
                    url = f"{self.BASE_URL}/{search_query}_NoIndex_True"
                    
                    # Navigate to search page with error handling
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Check response status
                    if response.status == 403:
                        # 403 Forbidden - Bot detected
                        print(f"⚠️  MercadoLibre returned 403 Forbidden for query: {query}")
                        print(f"   URL: {url}")
                        print(f"   Try: Increase SCRAPING_DELAY_MIN/MAX or use proxy rotation")
                        await browser.close()
                        return listings
                    
                    if response.status != 200:
                        print(f"⚠️  MercadoLibre returned status {response.status} for query: {query}")
                        await browser.close()
                        return listings
                    
                    # Wait for listings to load (adjust selector based on actual site)
                    try:
                        await page.wait_for_selector(".ui-search-result", timeout=10000)
                    except PlaywrightTimeout:
                        # No results found or different structure
                        print(f"⚠️  No results found for query: {query} (timeout waiting for .ui-search-result)")
                        await browser.close()
                        return listings
                    
                    # Extract listings using JavaScript evaluation
                    # This is more reliable than parsing HTML
                    items_data = await page.evaluate("""
                        () => {
                            const items = [];
                            const listings = document.querySelectorAll('.ui-search-result');
                            
                            listings.forEach((listing, index) => {
                                if (index >= 20) return; // Limit to 20
                                
                                try {
                                    // Extract title
                                    const titleElem = listing.querySelector('h2.ui-search-item__title, .ui-search-item__title');
                                    const title = titleElem ? titleElem.innerText : '';
                                    
                                    // Extract price
                                    const priceElem = listing.querySelector('.andes-money-amount__fraction, .price-tag-fraction');
                                    const price = priceElem ? priceElem.innerText : null;
                                    
                                    // Extract URL
                                    const linkElem = listing.querySelector('a.ui-search-link, a.ui-search-item__group__element');
                                    const url = linkElem ? linkElem.href : '';
                                    
                                    // Extract location if available
                                    const locationElem = listing.querySelector('.ui-search-item__group--location, .ui-search-item__location');
                                    const location = locationElem ? locationElem.innerText : '';
                                    
                                    // Try to extract year and mileage from title or attributes
                                    const attributes = listing.querySelector('.ui-search-item__group--attributes');
                                    const attributesText = attributes ? attributes.innerText : '';
                                    
                                    items.push({
                                        title: title,
                                        price: price,
                                        url: url,
                                        location: location,
                                        attributes: attributesText
                                    });
                                } catch (e) {
                                    // Skip problematic items
                                }
                            });
                            
                            return items;
                        }
                    """)
                    
                    # Process extracted data
                    for item_data in items_data:
                        try:
                            # Extract year and mileage from title or attributes
                            year = self._extract_year_from_text(
                                item_data.get('title', '') + ' ' + item_data.get('attributes', '')
                            )
                            mileage = self._extract_mileage_from_text(
                                item_data.get('title', '') + ' ' + item_data.get('attributes', '')
                            )
                            
                            listing = {
                                "title": item_data.get("title", ""),
                                "price": item_data.get("price"),
                                "year": year,
                                "mileage": mileage,
                                "latitude": None,  # Would need geocoding service
                                "longitude": None,
                                "city": self._extract_city_from_location(item_data.get("location", ""), city),
                                "url": item_data.get("url", ""),
                            }
                            
                            if listing["title"] and listing["url"]:
                                listings.append(self.normalize_listing(listing))
                        except Exception:
                            continue
                        
                        # Rate limiting delay
                        await self.delay()
                    
                except Exception as e:
                    # Log error for debugging but continue execution
                    logger.error(f"Error during MercadoLibre scraping: {str(e)}", exc_info=True)
                finally:
                    await browser.close()
                    
        except Exception as e:
            # Log error for debugging but return empty list to allow other scrapers to continue
            logger.error(f"Failed to initialize MercadoLibre scraper: {str(e)}", exc_info=True)
        
        return listings
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract year from text using regex."""
        # Look for 4-digit years between 1900 and 2030
        year_pattern = r'\b(19[0-9]{2}|20[0-2][0-9]|2030)\b'
        match = re.search(year_pattern, text)
        if match:
            year = int(match.group(1))
            return year
        return None
    
    def _extract_mileage_from_text(self, text: str) -> Optional[int]:
        """Extract mileage from text using regex."""
        # Look for numbers followed by km
        mileage_pattern = r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:km|kilómetros|kilometros)'
        match = re.search(mileage_pattern, text, re.IGNORECASE)
        if match:
            mileage_str = match.group(1).replace('.', '').replace(',', '')
            try:
                return int(mileage_str)
            except ValueError:
                pass
        return None
    
    def _extract_city_from_location(self, location: str, default_city: str) -> str:
        """Extract city from location string."""
        if not location:
            return default_city
        
        # Common Colombian cities
        cities = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 
                  'Bucaramanga', 'Pereira', 'Manizales', 'Armenia', 'Ibagué']
        
        for city in cities:
            if city.lower() in location.lower():
                return city
        
        return location.split(',')[0].strip() if location else default_city

