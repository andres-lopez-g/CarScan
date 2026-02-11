"""
TuCarro Colombia scraper using Playwright for JavaScript rendering.

TuCarro is MercadoLibre's vehicle marketplace in Colombia.
This scraper handles the 403 Forbidden error by using proper headers and user agent.
"""
from typing import List, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper
import re


class TuCarroScraper(BaseScraper):
    """Scraper for TuCarro Colombia marketplace using Playwright."""
    
    BASE_URL = "https://vehiculos.tucarro.com.co"
    
    def get_source_name(self) -> str:
        return "TuCarro"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from TuCarro using Playwright.
        
        This implementation handles 403 Forbidden errors by:
        - Using a realistic user agent
        - Setting proper browser headers
        - Adding viewport configuration
        - Using headless mode
        
        Args:
            query: Search query
            city: City to search in
            
        Returns:
            List of normalized vehicle listings
        """
        listings = []
        
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                # Create context with realistic user agent and headers
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="es-CO",
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                    }
                )
                
                page = await context.new_page()
                
                try:
                    # Build search URL
                    search_query = query.replace(" ", "-").lower()
                    url = f"{self.BASE_URL}/{search_query}"
                    
                    # Navigate to search page with longer timeout
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Wait for listings to load
                    # TuCarro uses the same ui-search structure as MercadoLibre
                    try:
                        await page.wait_for_selector(".ui-search-layout__item, .ui-search-result", timeout=10000)
                    except PlaywrightTimeout:
                        # Try alternative selector or return empty
                        try:
                            await page.wait_for_selector(".poly-card", timeout=5000)
                        except PlaywrightTimeout:
                            await browser.close()
                            return listings
                    
                    # Extract listings using JavaScript evaluation
                    items_data = await page.evaluate("""
                        () => {
                            const items = [];
                            
                            // Try multiple selectors for flexibility
                            const selectors = [
                                '.ui-search-layout__item',
                                '.ui-search-result',
                                '.poly-card',
                                '.ui-search-result__content-wrapper'
                            ];
                            
                            let listings = [];
                            for (const selector of selectors) {
                                listings = document.querySelectorAll(selector);
                                if (listings.length > 0) break;
                            }
                            
                            listings.forEach((listing, index) => {
                                if (index >= 20) return; // Limit to 20
                                
                                try {
                                    // Extract title - try multiple selectors
                                    const titleSelectors = [
                                        'h2.ui-search-item__title',
                                        '.ui-search-item__title',
                                        '.poly-component__title',
                                        'h2.poly-box',
                                        'a.ui-search-link h2'
                                    ];
                                    let title = '';
                                    for (const sel of titleSelectors) {
                                        const elem = listing.querySelector(sel);
                                        if (elem) {
                                            title = elem.innerText;
                                            break;
                                        }
                                    }
                                    
                                    // Extract price - try multiple selectors
                                    const priceSelectors = [
                                        '.andes-money-amount__fraction',
                                        '.price-tag-fraction',
                                        '.poly-price__current .andes-money-amount__fraction',
                                        '.ui-search-price__second-line .andes-money-amount__fraction'
                                    ];
                                    let price = null;
                                    for (const sel of priceSelectors) {
                                        const elem = listing.querySelector(sel);
                                        if (elem) {
                                            price = elem.innerText;
                                            break;
                                        }
                                    }
                                    
                                    // Extract URL - try multiple selectors
                                    const linkSelectors = [
                                        'a.ui-search-link',
                                        'a.ui-search-item__group__element',
                                        'a.poly-component__link',
                                        'a[href*="/MCO"]'
                                    ];
                                    let url = '';
                                    for (const sel of linkSelectors) {
                                        const elem = listing.querySelector(sel);
                                        if (elem && elem.href) {
                                            url = elem.href;
                                            break;
                                        }
                                    }
                                    
                                    // Extract location - try multiple selectors
                                    const locationSelectors = [
                                        '.ui-search-item__group--location',
                                        '.ui-search-item__location',
                                        '.poly-component__location'
                                    ];
                                    let location = '';
                                    for (const sel of locationSelectors) {
                                        const elem = listing.querySelector(sel);
                                        if (elem) {
                                            location = elem.innerText;
                                            break;
                                        }
                                    }
                                    
                                    // Extract attributes (year, mileage, etc.)
                                    const attributeSelectors = [
                                        '.ui-search-item__group--attributes',
                                        '.poly-attributes-list',
                                        '.ui-search-item__subtitle'
                                    ];
                                    let attributes = '';
                                    for (const sel of attributeSelectors) {
                                        const elem = listing.querySelector(sel);
                                        if (elem) {
                                            attributes = elem.innerText;
                                            break;
                                        }
                                    }
                                    
                                    // Only add if we have at least title
                                    if (title) {
                                        items.push({
                                            title: title,
                                            price: price,
                                            url: url,
                                            location: location,
                                            attributes: attributes
                                        });
                                    }
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
                    # Log error in production
                    pass
                finally:
                    await browser.close()
                    
        except Exception as e:
            # Log error in production
            pass
        
        return listings
    
    def _extract_year_from_text(self, text: str) -> int | None:
        """Extract year from text using regex."""
        # Look for 4-digit years between 1900 and 2030
        year_pattern = r'\b(19[0-9]{2}|20[0-2][0-9]|2030)\b'
        match = re.search(year_pattern, text)
        if match:
            year = int(match.group(1))
            return year
        return None
    
    def _extract_mileage_from_text(self, text: str) -> int | None:
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
                  'Bucaramanga', 'Pereira', 'Manizales', 'Armenia', 'Ibagué',
                  'Villavicencio', 'Pasto', 'Cúcuta', 'Montería', 'Neiva']
        
        for city in cities:
            if city.lower() in location.lower():
                return city
        
        return location.split(',')[0].strip() if location else default_city
