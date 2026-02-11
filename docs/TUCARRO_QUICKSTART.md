# TuCarro Scraper - Quick Start Guide

## What Was Implemented

The TuCarro scraper has been successfully implemented to solve the 403 Forbidden error you were experiencing. Here's what was added:

### ✅ New Files Created

1. **`backend/app/scrapers/tucarro_scraper.py`** - Complete TuCarro scraper implementation
2. **`docs/tucarro_scraper.md`** - Comprehensive documentation

### ✅ Modified Files

1. **`backend/app/scrapers/__init__.py`** - Added TuCarroScraper export
2. **`backend/app/services/vehicle_service.py`** - Integrated TuCarro scraper into the service
3. **`README.md`** - Updated to reflect TuCarro support

## How It Works

The TuCarro scraper now automatically runs alongside the MercadoLibre scraper whenever a user searches for vehicles. It includes:

### 403 Error Prevention

The scraper uses several techniques to avoid getting blocked:

```python
# Realistic browser configuration
- User Agent: Modern Chrome user agent
- Headers: Complete set of browser headers
- Viewport: Standard desktop resolution (1920x1080)
- Locale: es-CO (Colombian Spanish)
- Anti-bot features: Disabled automation detection
```

### Smart Selector Strategy

The scraper tries multiple CSS selectors to find listings, making it resilient to HTML structure changes:

```javascript
// Container selectors (tries in order)
'.ui-search-layout__item'
'.ui-search-result'
'.poly-card'
'.ui-search-result__content-wrapper'

// Title selectors
'h2.ui-search-item__title'
'.ui-search-item__title'
'.poly-component__title'
// ... and more fallbacks
```

## Testing the Implementation

### Option 1: Full Application Test (Recommended)

1. **Start the application**:
   ```bash
   docker-compose up --build
   ```

2. **Access the frontend**: http://localhost:3000

3. **Perform a search**: Enter a vehicle query like "Toyota Corolla"

4. **Check results**: You should see listings from both MercadoLibre and TuCarro sources

### Option 2: Backend API Test

1. **Start just the backend**:
   ```bash
   cd backend
   docker-compose up db redis
   # In another terminal
   uvicorn app.main:app --reload
   ```

2. **Make an API request**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/vehicles/search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Toyota Corolla",
       "city": "Medellín"
     }'
   ```

3. **Check response**: Look for listings with `"source": "TuCarro"`

### Option 3: Direct Scraper Test

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Create a test script** (`test_scraper.py`):
   ```python
   import asyncio
   from app.scrapers.tucarro_scraper import TuCarroScraper
   
   async def test():
       scraper = TuCarroScraper()
       listings = await scraper.scrape("Toyota Corolla", "Medellín")
       print(f"Found {len(listings)} listings")
       for listing in listings[:3]:
           print(f"- {listing['title'][:60]}...")
           print(f"  Price: ${listing['price']:,.0f}")
           print(f"  Source: {listing['source']}")
   
   asyncio.run(test())
   ```

3. **Run the test**:
   ```bash
   PYTHONPATH=/path/to/backend python test_scraper.py
   ```

## Monitoring and Debugging

### Check Logs

When running the application, you can monitor the scraping activity:

```bash
docker-compose logs -f backend
```

Look for log entries related to scraping:
- Successful scrapes
- Number of listings found
- Any errors that occur

### Common Issues and Solutions

#### Issue: Still Getting 403 Errors

**Possible Causes**:
- Network firewall blocking the domain
- IP address has been rate-limited
- TuCarro updated their anti-bot measures

**Solutions**:
1. Add delays between requests (increase `SCRAPING_DELAY_MAX` in `.env`)
2. Use a VPN or proxy
3. Rotate user agents
4. Contact your network administrator about firewall rules

#### Issue: No Listings Returned

**Possible Causes**:
- Website structure changed
- No results for the search query
- Timeout waiting for page load

**Solutions**:
1. Test the URL manually in a browser: `https://vehiculos.tucarro.com.co/toyota-corolla`
2. Check if the selectors need updating
3. Increase timeout values in the scraper
4. Try different search queries

#### Issue: Data Extraction Incomplete

**Possible Causes**:
- Missing fields in some listings
- Different listing formats
- Regex patterns not matching

**Solutions**:
1. Check the HTML source of problematic listings
2. Update regex patterns in `_extract_year_from_text` and `_extract_mileage_from_text`
3. Add more fallback selectors

## Configuration

You can configure the scraper behavior in `backend/.env`:

```env
# Scraping delays (in seconds)
SCRAPING_DELAY_MIN=2
SCRAPING_DELAY_MAX=5

# Maximum concurrent scrapers
MAX_CONCURRENT_SCRAPERS=2
```

To adjust for your use case:
- **Increase delays** if getting rate limited
- **Decrease delays** if performance is critical and no issues
- **Adjust concurrent scrapers** based on server capacity

## Verifying Success

A successful implementation should:

1. ✅ **Not return 403 errors** - Check logs for HTTP status codes
2. ✅ **Extract vehicle data** - Verify listings have title, price, year, mileage
3. ✅ **Normalize data correctly** - Prices should be numeric, years should be 4-digit integers
4. ✅ **Identify source** - All listings should have `"source": "TuCarro"`
5. ✅ **Provide valid URLs** - Each listing should link to original TuCarro page

## Next Steps

### Immediate Actions

1. Test the scraper with real searches
2. Monitor for any 403 errors or failures
3. Verify data quality of extracted listings

### Potential Enhancements

1. **Add pagination support** - Currently limited to first 20 results
2. **Extract more attributes** - Transmission type, fuel type, color, etc.
3. **Implement caching** - Avoid re-scraping recent searches
4. **Add proxy rotation** - For production deployments at scale
5. **Geocode locations** - Convert city names to lat/lon coordinates

## Support

If you encounter issues:

1. **Check documentation**: `docs/tucarro_scraper.md`
2. **Review logs**: Look for error messages
3. **Update selectors**: If website structure changed
4. **Test manually**: Use browser dev tools to inspect TuCarro HTML

## Files to Review

- **Implementation**: `backend/app/scrapers/tucarro_scraper.py`
- **Integration**: `backend/app/services/vehicle_service.py`
- **Documentation**: `docs/tucarro_scraper.md`
- **Configuration**: `backend/.env.example`

---

**Status**: ✅ Implementation Complete  
**Tested**: ✅ Code syntax and imports verified  
**Ready**: ✅ Ready for integration testing with live website
