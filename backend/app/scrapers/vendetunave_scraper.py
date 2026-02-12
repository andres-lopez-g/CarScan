"""
VendeTuNave Colombia scraper using Playwright for JavaScript rendering.

VendeTuNave is a Colombian marketplace for vehicles (cars, motorcycles, boats).
This scraper handles vehicle listings and normalizes them for the CarScan platform.
"""
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)


class VendeTuNaveScraper(BaseScraper):
    """Scraper for VendeTuNave Colombia marketplace using Playwright."""
    
    BASE_URL = "https://www.vendetunave.co"
    
    def get_source_name(self) -> str:
        return "VendeTuNave"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from VendeTuNave using Playwright.
        
        This implementation uses Playwright to handle JavaScript-rendered content
        with stealth techniques to avoid detection.
        
        Args:
            query: Search query (e.g., "Toyota Corolla 2015")
            city: City to search in (default: Medellín)
            
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
                    # Build search URL for VendeTuNave
                    # Typical format: /carros/buscar?q=query or /vehiculos/search
                    search_query = query.replace(" ", "+")
                    city_normalized = city.lower().replace("í", "i").replace("é", "e")
                    url = f"{self.BASE_URL}/carros/buscar?q={search_query}&ciudad={city_normalized}"
                    
                    # Navigate to search page with error handling
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Check response status
                    if response and response.status == 403:
                        logger.warning(f"VendeTuNave returned 403 Forbidden for query: {query}")
                        print(f"⚠️  VendeTuNave returned 403 Forbidden for query: {query}")
                        await browser.close()
                        return listings
                    
                    if response and response.status != 200:
                        logger.warning(f"VendeTuNave returned status {response.status} for query: {query}")
                        await browser.close()
                        return listings
                    
                    # Wait for listings to load
                    try:
                        await page.wait_for_selector(".vehicle-card, .car-card, .listing-item, article", timeout=10000)
                    except PlaywrightTimeout:
                        logger.warning(f"No results found for query: {query}")
                        await browser.close()
                        return listings
                    
                    # Extract listings using JavaScript evaluation
                    items_data = await page.evaluate("""
                        () => {
                            const items = [];
                            
                            // Try multiple selectors for vehicle cards
                            const selectors = [
                                '.vehicle-card',
                                '.car-card',
                                '.listing-item',
                                'article[data-vehicle]',
                                '.card-vehicle',
                                '[data-listing]'
                            ];
                            
                            let listings = [];
                            for (const selector of selectors) {
                                listings = document.querySelectorAll(selector);
                                if (listings.length > 0) break;
                            }
                            
                            // Fallback to article elements if no specific cards found
                            if (listings.length === 0) {
                                listings = document.querySelectorAll('article');
                            }
                            
                            listings.forEach((listing, index) => {
                                if (index >= 20) return; // Limit to 20 results
                                
                                try {
                                    // Extract title - vehicle brand/model/year
                                    const titleElem = listing.querySelector('h2, h3, .title, .vehicle-title, [class*="title"]');
                                    const title = titleElem ? titleElem.innerText.trim() : '';
                                    
                                    // Extract price
                                    const priceElem = listing.querySelector('.price, [class*="price"], [data-price]');
                                    const price = priceElem ? priceElem.innerText.trim() : null;
                                    
                                    // Extract URL
                                    const linkElem = listing.querySelector('a[href*="/vehiculo/"], a[href*="/carro/"], a[href*="/auto/"], a');
                                    const url = linkElem ? linkElem.href : '';
                                    
                                    // Extract location
                                    const locationElem = listing.querySelector('.location, [class*="location"], [class*="city"]');
                                    const location = locationElem ? locationElem.innerText.trim() : '';
                                    
                                    // Extract year
                                    const yearElem = listing.querySelector('[class*="year"], .year');
                                    const year = yearElem ? yearElem.innerText.trim() : '';
                                    
                                    // Extract mileage/kilometers
                                    const mileageElem = listing.querySelector('[class*="mileage"], [class*="km"], .kilometers');
                                    const mileage = mileageElem ? mileageElem.innerText.trim() : '';
                                    
                                    // Get all text for attribute extraction
                                    const allText = listing.innerText || '';
                                    
                                    if (title || url) {
                                        items.push({
                                            title: title,
                                            price: price,
                                            url: url,
                                            location: location,
                                            year: year,
                                            mileage: mileage,
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
                    
                    logger.info(f"Extracted {len(items_data)} items from VendeTuNave for query: {query}")
                    
                    # Process extracted data
                    for item_data in items_data:
                        try:
                            # Extract year and mileage from text
                            year = self._extract_year_from_text(
                                item_data.get('title', '') + ' ' + 
                                item_data.get('year', '') + ' ' + 
                                item_data.get('attributes', '')
                            )
                            mileage = self._extract_mileage_from_text(
                                item_data.get('title', '') + ' ' + 
                                item_data.get('mileage', '') + ' ' + 
                                item_data.get('attributes', '')
                            )
                            
                            listing = {
                                "title": item_data.get("title", ""),
                                "price": item_data.get("price"),
                                "year": year,
                                "mileage": mileage,
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
                    logger.error(f"Error during VendeTuNave scraping: {e}", exc_info=True)
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"VendeTuNave scraper initialization error: {e}", exc_info=True)
        
        logger.info(f"VendeTuNave scraper completed. Returning {len(listings)} listings.")
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
        # Look for numbers followed by km (with or without separators)
        mileage_pattern = r'(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:km|kilómetros|kilometros)'
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
