"""
FincaRaiz Colombia scraper using Playwright for JavaScript rendering.

FincaRaiz is one of the largest real estate marketplaces in Colombia.
This scraper handles warehouse (bodegas) rental listings.
"""
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)


class FincaRaizScraper(BaseScraper):
    """Scraper for FincaRaiz Colombia marketplace using Playwright."""
    
    BASE_URL = "https://www.fincaraiz.com.co"
    
    def get_source_name(self) -> str:
        return "FincaRaiz"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape warehouse rental listings from FincaRaiz using Playwright.
        
        This implementation uses Playwright to handle JavaScript-rendered content
        with stealth techniques to avoid detection.
        
        Args:
            query: Search query (e.g., "bodega arriendo")
            city: City to search in (default: Medellín)
            
        Returns:
            List of normalized property listings
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
                    # Build search URL for FincaRaiz
                    # URL format: /arriendo/bodegas/ciudad or search with query params
                    city_normalized = city.lower().replace("í", "i").replace("é", "e").replace("á", "a")
                    
                    # If query contains "bodega" search for warehouses
                    if "bodega" in query.lower():
                        url = f"{self.BASE_URL}/arriendo/bodegas/{city_normalized}"
                    else:
                        # General search with query
                        search_query = query.replace(" ", "-").lower()
                        url = f"{self.BASE_URL}/arriendo/{search_query}/{city_normalized}"
                    
                    # Navigate to search page with error handling
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Check response status
                    if response and response.status == 403:
                        logger.warning(f"FincaRaiz returned 403 Forbidden for query: {query}")
                        print(f"⚠️  FincaRaiz returned 403 Forbidden for query: {query}")
                        await browser.close()
                        return listings
                    
                    if response and response.status != 200:
                        logger.warning(f"FincaRaiz returned status {response.status} for query: {query}")
                        await browser.close()
                        return listings
                    
                    # Wait for listings to load
                    # FincaRaiz uses various card classes for property listings
                    try:
                        await page.wait_for_selector(".MuiCard-root, .listingCard, .property-card, article[data-testid]", timeout=10000)
                    except PlaywrightTimeout:
                        logger.warning(f"No results found for query: {query}")
                        await browser.close()
                        return listings
                    
                    # Extract listings using JavaScript evaluation
                    items_data = await page.evaluate("""
                        () => {
                            const items = [];
                            
                            // FincaRaiz uses Material-UI cards or custom card components
                            const selectors = [
                                '.MuiCard-root',
                                '.listingCard',
                                '.property-card',
                                'article[data-testid]',
                                '[data-listing-id]',
                                '.listing-card'
                            ];
                            
                            let listings = [];
                            for (const selector of selectors) {
                                listings = document.querySelectorAll(selector);
                                if (listings.length > 0) break;
                            }
                            
                            listings.forEach((listing, index) => {
                                if (index >= 20) return; // Limit to 20 results
                                
                                try {
                                    // Extract title - FincaRaiz shows property type and location
                                    const titleElem = listing.querySelector('h2, h3, .title, [class*="title"], [class*="Title"]');
                                    const title = titleElem ? titleElem.innerText.trim() : '';
                                    
                                    // Extract price - look for price containers
                                    const priceElem = listing.querySelector('[class*="price"], [class*="Price"], .price, span[class*="amount"]');
                                    const price = priceElem ? priceElem.innerText.trim() : null;
                                    
                                    // Extract URL
                                    const linkElem = listing.querySelector('a[href*="/inmueble/"], a[href*="/bodega/"], a');
                                    const url = linkElem ? linkElem.href : '';
                                    
                                    // Extract location/address
                                    const locationElem = listing.querySelector('[class*="location"], [class*="address"], .location, .address');
                                    const location = locationElem ? locationElem.innerText.trim() : '';
                                    
                                    // Extract area
                                    const areaElem = listing.querySelector('[class*="area"], [class*="size"], .area');
                                    const area = areaElem ? areaElem.innerText.trim() : '';
                                    
                                    // Extract features (rooms, bathrooms, etc.)
                                    const featuresElem = listing.querySelector('[class*="features"], [class*="amenities"]');
                                    const features = featuresElem ? featuresElem.innerText.trim() : '';
                                    
                                    // Get all text for attribute extraction
                                    const allText = listing.innerText || '';
                                    
                                    if (title || url) {
                                        items.push({
                                            title: title,
                                            price: price,
                                            url: url,
                                            location: location,
                                            area: area,
                                            features: features,
                                            attributes: allText
                                        });
                                    }
                                } catch (e) {
                                    // Skip problematic items
                                }
                            });
                            
                            return items;
                        }
                    """)
                    
                    logger.info(f"Extracted {len(items_data)} items from FincaRaiz for query: {query}")
                    
                    # Process extracted data
                    for item_data in items_data:
                        try:
                            # Extract area from text
                            area = self._extract_area_from_text(
                                item_data.get('title', '') + ' ' + 
                                item_data.get('area', '') + ' ' + 
                                item_data.get('attributes', '')
                            )
                            
                            # NOTE: For property listings, we repurpose the 'mileage' field 
                            # to store area (m²) since the current schema is vehicle-focused.
                            # A future enhancement could add a dedicated 'area' field.
                            listing = {
                                "title": item_data.get("title", ""),
                                "price": item_data.get("price"),
                                "year": None,  # Properties don't have year
                                "mileage": area,  # Repurposed for area (m²) in property listings
                                "latitude": None,
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
                    logger.error(f"Error during FincaRaiz scraping: {e}", exc_info=True)
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"FincaRaiz scraper initialization error: {e}", exc_info=True)
        
        logger.info(f"FincaRaiz scraper completed. Returning {len(listings)} listings.")
        return listings
    
    def _extract_area_from_text(self, text: str) -> Optional[int]:
        """Extract area in m2 from text using regex."""
        # Look for numbers followed by m2 or metros
        area_pattern = r'(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:m2|m²|metros|mts)'
        match = re.search(area_pattern, text, re.IGNORECASE)
        if match:
            area_str = match.group(1).replace('.', '').replace(',', '')
            try:
                return int(area_str)
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
