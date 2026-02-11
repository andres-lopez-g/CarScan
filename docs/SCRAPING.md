# MercadoLibre Scraping Implementation Guide

## Overview

The CarScan project uses **Playwright** for automated web scraping of **MercadoLibre Colombia** and **TuCarro**. This document explains how the scraping automation works.

**Note**: TuCarro is a MercadoLibre brand focused on vehicles, using the same platform and structure.

## Architecture

### 1. Scraping Flow

```
User Search → API Request → VehicleService → MercadoLibreScraper → Playwright → MercadoLibre Website
                                                                              ↓
                                                                      Extract Data
                                                                              ↓
                                                                      Normalize Data
                                                                              ↓
                                                                    Store in Database
                                                                              ↓
                                                                    Return to User
```

### 2. Technology Stack

- **Playwright**: Headless browser automation (handles JavaScript rendering)
- **Python async/await**: Asynchronous scraping for performance
- **Regex patterns**: Extract year and mileage from text
- **httpx** (backup): For simple HTTP requests if needed

## How It Works

### Step 1: Browser Automation with Playwright

```python
# Launch headless Chromium browser
browser = await p.chromium.launch(headless=True)

# Create realistic browser context
context = await browser.new_context(
    user_agent="Mozilla/5.0...",  # Realistic user agent
    viewport={"width": 1920, "height": 1080}
)
```

**Why Playwright?**
- MercadoLibre uses JavaScript to render content
- Handles dynamic content loading
- More reliable than static HTML parsing
- Can wait for elements to load

### Step 2: Navigate to Search Results

```python
# Build search URL
url = f"https://carros.mercadolibre.com.co/{query}_NoIndex_True"

# Navigate and wait for content
await page.goto(url, wait_until="domcontentloaded")
await page.wait_for_selector(".ui-search-result")
```

### Step 3: Extract Data Using JavaScript Evaluation

Instead of parsing HTML on the Python side, we execute JavaScript in the browser context:

```python
items_data = await page.evaluate("""
    () => {
        const items = [];
        const listings = document.querySelectorAll('.ui-search-result');
        
        listings.forEach((listing) => {
            // Extract title
            const titleElem = listing.querySelector('h2.ui-search-item__title');
            const title = titleElem ? titleElem.innerText : '';
            
            // Extract price
            const priceElem = listing.querySelector('.andes-money-amount__fraction');
            const price = priceElem ? priceElem.innerText : null;
            
            // Extract URL
            const linkElem = listing.querySelector('a.ui-search-link');
            const url = linkElem ? linkElem.href : '';
            
            items.push({ title, price, url });
        });
        
        return items;
    }
""")
```

**Benefits:**
- Executes in browser context (sees actual rendered content)
- Gets exact text as displayed to users
- More reliable than CSS selectors from Python

### Step 4: Data Extraction & Normalization

#### Extract Year
```python
def _extract_year_from_text(self, text: str) -> int | None:
    # Look for 4-digit years (1900-2030)
    year_pattern = r'\b(19[0-9]{2}|20[0-2][0-9]|2030)\b'
    match = re.search(year_pattern, text)
    return int(match.group(1)) if match else None
```

#### Extract Mileage
```python
def _extract_mileage_from_text(self, text: str) -> int | None:
    # Look for numbers followed by "km"
    mileage_pattern = r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:km|kilómetros)'
    match = re.search(mileage_pattern, text, re.IGNORECASE)
    # Parse and clean: "150.000 km" → 150000
```

#### Extract City
```python
def _extract_city_from_location(self, location: str, default_city: str) -> str:
    # Match against known Colombian cities
    cities = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', ...]
    for city in cities:
        if city.lower() in location.lower():
            return city
```

### Step 5: Price Normalization

The `BaseScraper` class handles price normalization:

```python
def _parse_price(self, price_str: str) -> float:
    # "$ 35.000.000" → 35000000.0
    clean = price_str.replace("$", "").replace(".", "").replace(",", "")
    return float(clean)
```

### Step 6: Rate Limiting (Responsible Scraping)

```python
async def delay(self):
    # Random delay between 2-5 seconds (configurable)
    await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))
```

**Why:**
- Prevents overwhelming the server
- Avoids IP blocking
- Ethical scraping practice

## Responsible Scraping Practices

### 1. Legal Compliance
✅ Only scrapes publicly available data  
✅ No login-required content  
✅ No CAPTCHA bypassing  
✅ Includes original listing URLs  
✅ Does not store/rehost images  

### 2. Technical Safeguards
✅ Rate limiting (2-5 second delays)  
✅ Realistic user agent  
✅ Timeout handling  
✅ Error gracefully handling  
✅ Respects robots.txt (should add check)  

### 3. Configuration

Set in `backend/.env`:
```bash
SCRAPING_DELAY_MIN=2  # Minimum delay in seconds
SCRAPING_DELAY_MAX=5  # Maximum delay in seconds
MAX_CONCURRENT_SCRAPERS=1  # Limit concurrent scrapers
```

## Limitations & Considerations

### Current Limitations

1. **CSS Selectors May Change**
   - MercadoLibre can update their HTML structure
   - Selectors need periodic updates
   - Solution: Monitor and update selectors

2. **No Geocoding Yet**
   - Latitude/Longitude are set to None
   - Need to integrate geocoding service (Nominatim)
   - Would convert city names to coordinates

3. **Anti-Bot Detection**
   - MercadoLibre may have bot detection
   - May require:
     - Proxy rotation
     - More sophisticated user agent rotation
     - Solving CAPTCHAs (not implemented - ethical consideration)

4. **Limited to 20 Results**
   - Currently limits to first 20 listings
   - Can be increased but increases scraping time

### Production Considerations

For production deployment, consider:

1. **Background Workers** (Celery)
   ```python
   # Instead of scraping on each request:
   @celery_app.task
   async def scrape_periodic():
       # Run scraper every hour
       # Store results in database
   ```

2. **Caching**
   ```python
   # Cache results in Redis for 1 hour
   # Return cached data if recent
   ```

3. **Error Handling & Logging**
   ```python
   import logging
   logger.error(f"Scraping failed: {e}")
   # Send alerts on failures
   ```

4. **Proxy Rotation**
   ```python
   # Use proxy service for distributed scraping
   context = await browser.new_context(proxy={
       "server": "http://proxy:8080"
   })
   ```

## Testing the Scraper

### Manual Test

```bash
# Start the backend
cd backend
uvicorn app.main:app --reload

# Make API request
curl -X POST "http://localhost:8000/api/v1/vehicles/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Toyota Corolla 2015",
    "city": "Medellín"
  }'
```

### Debug Mode

Enable debug logging in `backend/.env`:
```bash
DEBUG=true
```

This will show:
- URLs being scraped
- Number of items found
- Parsing errors
- Timing information

## Alternatives to Playwright

### Option 1: API Access (Ideal but unavailable)
MercadoLibre has an official API, but it requires:
- Business registration
- API approval
- Rate limits
- May not include all listings

### Option 2: Static HTML Parsing (httpx + BeautifulSoup)
Faster but less reliable:
- Doesn't handle JavaScript
- May miss dynamic content
- More prone to breaking

### Option 3: Selenium (Alternative to Playwright)
Similar to Playwright but:
- Heavier weight
- Slower startup
- Less modern API

## Future Enhancements

1. **Add Nominatim Geocoding**
   ```python
   from geopy.geocoders import Nominatim
   
   async def geocode_city(city: str):
       geolocator = Nominatim(user_agent="carscan")
       location = geolocator.geocode(f"{city}, Colombia")
       return location.latitude, location.longitude
   ```

2. **Implement Proxy Rotation**
3. **Add Retry Logic with Exponential Backoff**
4. **Monitor Scraper Health**
5. **Add Unit Tests for Parsers**
6. **Implement Robots.txt Checking**

## Conclusion

The MercadoLibre scraper uses Playwright for reliable, JavaScript-aware web scraping. It follows responsible scraping practices with rate limiting, realistic user agents, and error handling. The modular design allows easy addition of more scrapers for other marketplaces in the future.

## TuCarro Scraper

### Overview

TuCarro (https://carros.tucarro.com.co/) is a MercadoLibre brand focused on vehicle listings in Colombia. It uses the **same platform, structure, and CSS classes** as MercadoLibre, making the scraping implementation very similar.

### Key Similarities with MercadoLibre

1. **Andes Design System**: Uses the same CSS framework
2. **UI Structure**: Same layout (search bar top, filters left, results center)
3. **CSS Selectors**: Identical selectors (`.ui-search-result`, `.andes-money-amount__fraction`, etc.)
4. **JavaScript Rendering**: Requires Playwright for dynamic content
5. **URL Structure**: Similar search URL patterns

### Implementation

The `TuCarroScraper` class is implemented in `backend/app/scrapers/tucarro_scraper.py` and:

- Inherits from `BaseScraper`
- Uses `BASE_URL = "https://carros.tucarro.com.co"`
- Reuses the same extraction logic as `MercadoLibreScraper`
- Returns normalized data with `source = "TuCarro"`

### Page Structure

#### Search Bar (Top)
- Located in the header navigation
- Standard MercadoLibre search input
- Selector: `input[placeholder*="Buscar"]`

#### Filters (Left Sidebar)
Common filter categories:
- **Marca** (Brand): Toyota, Chevrolet, Mazda, etc.
- **Año** (Year): Year range selector
- **Precio** (Price): Min/max price inputs
- **Kilómetros** (Mileage): Mileage range
- **Combustible** (Fuel Type): Gasolina, Diesel, etc.
- **Transmisión** (Transmission): Manual, Automática
- **Ubicación** (Location): Colombian cities

#### Search Results (Center/Right)
- Grid of vehicle listing cards
- Each card contains: title, price, image, location, attributes
- Same HTML structure as MercadoLibre

### Running Multiple Scrapers

The `VehicleService` now runs **both** MercadoLibre and TuCarro scrapers:

```python
class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scrapers = [
            MercadoLibreScraper(),
            TuCarroScraper(),
        ]
```

Scrapers run **concurrently** using `asyncio.gather()`:

```python
tasks = [scraper.scrape(query, city) for scraper in self.scrapers]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

This approach:
- ✅ Runs both scrapers simultaneously
- ✅ Handles exceptions gracefully
- ✅ Aggregates results from multiple sources
- ✅ Provides more comprehensive search results

### Benefits of Adding TuCarro

1. **More Listings**: TuCarro specializes in vehicles, may have exclusive listings
2. **Better Coverage**: Expands search to another major Colombian marketplace
3. **Price Comparison**: Compare prices across both platforms
4. **Same Technology**: No additional dependencies needed
5. **Minimal Code**: Reuses existing scraping infrastructure

### URL Examples

```
# Homepage
https://carros.tucarro.com.co/

# Search by query
https://carros.tucarro.com.co/toyota-corolla-2015

# Search with filters
https://carros.tucarro.com.co/toyota?YEAR=2015-*&PRICE=*-50000000
```

### Maintenance Notes

Since TuCarro uses the MercadoLibre platform:
- ✅ Selector updates needed for MercadoLibre also apply to TuCarro
- ✅ Same rate limiting configuration works for both
- ✅ Shared extraction logic reduces maintenance overhead

For detailed page structure analysis, see: `docs/TUCARRO_ANALYSIS.md`
