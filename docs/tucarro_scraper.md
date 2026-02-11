# TuCarro Scraper Implementation

## Overview

The TuCarro scraper has been implemented to fetch vehicle listings from TuCarro Colombia (https://vehiculos.tucarro.com.co), which is MercadoLibre's dedicated vehicle marketplace for Colombia.

## Key Features

### 1. 403 Forbidden Error Prevention

The scraper implements several techniques to avoid getting blocked with 403 Forbidden errors:

- **Realistic User Agent**: Uses a modern Chrome user agent string
- **Proper HTTP Headers**: Includes all standard browser headers (Accept, Accept-Language, Accept-Encoding, etc.)
- **Browser Automation Settings**: Disables automation detection with `--disable-blink-features=AutomationControlled`
- **Locale Configuration**: Sets locale to `es-CO` (Spanish - Colombia)
- **Viewport Configuration**: Uses a standard desktop resolution (1920x1080)
- **Headless Mode**: Runs browser in headless mode for efficiency

### 2. Robust Selector Strategy

The scraper uses multiple fallback selectors to handle variations in the HTML structure:

```python
# Title selectors (tries in order)
- 'h2.ui-search-item__title'
- '.ui-search-item__title'
- '.poly-component__title'
- 'h2.poly-box'
- 'a.ui-search-link h2'

# Listing container selectors
- '.ui-search-layout__item'
- '.ui-search-result'
- '.poly-card'
- '.ui-search-result__content-wrapper'
```

### 3. Data Extraction

The scraper extracts the following information from each listing:

- **Title**: Vehicle make, model, and description
- **Price**: Numeric price value (COP)
- **Year**: Manufacturing year (extracted from title/attributes)
- **Mileage**: Kilometers driven (extracted from title/attributes)
- **Location**: City/region where vehicle is located
- **URL**: Direct link to the original listing

### 4. Rate Limiting

The scraper respects the website by:
- Adding delays between processing each listing (2-5 seconds configurable)
- Limiting results to 20 listings per search
- Using proper wait conditions for page loading

## Technical Implementation

### Class Structure

```python
class TuCarroScraper(BaseScraper):
    BASE_URL = "https://vehiculos.tucarro.com.co"
    
    def get_source_name(self) -> str:
        return "TuCarro"
    
    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        # Implementation uses Playwright for browser automation
```

### Key Methods

1. **`scrape(query, city)`**: Main scraping method that:
   - Launches Playwright browser with proper configuration
   - Navigates to search results page
   - Waits for content to load
   - Extracts listing data using JavaScript evaluation
   - Returns normalized listing data

2. **`_extract_year_from_text(text)`**: Uses regex to find 4-digit years (1900-2030)

3. **`_extract_mileage_from_text(text)`**: Extracts mileage numbers followed by "km" or "kilómetros"

4. **`_extract_city_from_location(location, default)`**: Matches against common Colombian cities

## Integration

The TuCarro scraper is integrated into the CarScan application:

1. **Registered in scrapers package** (`app/scrapers/__init__.py`)
2. **Added to VehicleService** (`app/services/vehicle_service.py`)
3. **Runs concurrently with other scrapers** when a search is performed

## Usage

The scraper is automatically invoked when users perform a vehicle search:

```python
# In VehicleService
self.scrapers = [
    MercadoLibreScraper(),
    TuCarroScraper(),  # Added TuCarro scraper
]

# Both scrapers run concurrently
tasks = [scraper.scrape(query, city) for scraper in self.scrapers]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Gracefully handles connection timeouts
- **Missing Elements**: Uses try-catch blocks to skip problematic listings
- **Empty Results**: Returns empty list if no listings found
- **403 Errors**: Prevented through proper header configuration

## Testing

To test the scraper locally:

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   ```

2. The scraper will be automatically tested when:
   - Running the full application with `docker-compose up`
   - Performing a vehicle search through the API
   - Using the frontend search interface

## Troubleshooting

### If 403 Errors Still Occur

1. **Check Network Access**: Ensure the deployment environment can access `vehiculos.tucarro.com.co`
2. **Update User Agent**: User agents may need periodic updates to stay current
3. **Add Delays**: Increase `SCRAPING_DELAY_MIN` and `SCRAPING_DELAY_MAX` in `.env`
4. **Rotate User Agents**: Consider implementing user agent rotation for production

### If No Results Found

1. **Verify URL Format**: TuCarro uses format `https://vehiculos.tucarro.com.co/{query}`
2. **Check Selectors**: Website structure may have changed - update selectors
3. **Inspect HTML**: Use browser dev tools to verify current class names
4. **Test Search Query**: Some queries may return no results legitimately

## Maintenance

To keep the scraper working:

1. **Monitor for Changes**: TuCarro may update their HTML structure
2. **Update Selectors**: Add new selectors if old ones stop working
3. **Test Regularly**: Run periodic tests to ensure scraper still works
4. **Check Logs**: Review application logs for scraping errors

## Responsible Scraping

This scraper follows responsible scraping practices:

✅ Uses realistic browser behavior  
✅ Includes rate limiting and delays  
✅ Does not bypass CAPTCHAs  
✅ Does not store or rehost images  
✅ Always links back to original listings  
✅ Respects robots.txt  
✅ Only scrapes publicly available data  

## Future Enhancements

Potential improvements for the TuCarro scraper:

- [ ] Add support for pagination (scrape multiple pages)
- [ ] Extract more vehicle attributes (transmission, fuel type, color)
- [ ] Implement caching to reduce duplicate scraping
- [ ] Add proxy support for production deployments
- [ ] Extract actual coordinates from listings (if available)
- [ ] Support filtered searches (by price range, year, etc.)
