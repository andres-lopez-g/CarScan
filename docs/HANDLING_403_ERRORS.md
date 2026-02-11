# Handling 403 Forbidden Errors in Web Scraping

## Problem

When scraping MercadoLibre and TuCarro, you may encounter **403 Forbidden** errors. This indicates that the website has detected automated access and is blocking the request.

## Why This Happens

1. **Bot Detection**: Websites use various techniques to detect bots:
   - User-Agent header inspection
   - Missing browser headers (Accept, Accept-Language, etc.)
   - Request patterns (too fast, too many requests)
   - Lack of JavaScript execution fingerprints
   - WebDriver detection in Playwright/Selenium

2. **Anti-Scraping Protection**: MercadoLibre implements:
   - Rate limiting
   - CAPTCHA challenges
   - IP-based blocking
   - Behavioral analysis

## Solutions

### 1. Enhanced Headers (First Try)

Use complete, realistic browser headers:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}
```

### 2. Playwright Stealth Mode (Recommended)

Configure Playwright to avoid detection:

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='es-CO',
        timezone_id='America/Bogota',
        extra_http_headers={
            'Accept-Language': 'es-CO,es;q=0.9',
        }
    )
    
    # Remove webdriver property
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    page = await context.new_page()
```

### 3. Rate Limiting (Essential)

Always implement delays between requests:

```python
import random
import asyncio

async def delay(min_seconds=2, max_seconds=5):
    """Random delay to appear more human-like."""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))
```

### 4. Retry Logic with Exponential Backoff

Handle temporary blocks gracefully:

```python
async def scrape_with_retry(url, max_retries=3):
    """Retry scraping with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = await fetch_page(url)
            
            if response.status == 200:
                return response
            elif response.status == 403:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    print(f"403 error, waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception("Max retries reached")
            else:
                raise Exception(f"Unexpected status: {response.status}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
            else:
                raise e
```

### 5. Proxy Rotation (For Production)

Use rotating proxies to distribute requests:

```python
proxies = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://proxy3:8080",
]

async def get_with_proxy(url, proxies):
    """Fetch with random proxy."""
    import random
    proxy = random.choice(proxies)
    
    context = await browser.new_context(
        proxy={"server": proxy}
    )
    # ... continue scraping
```

### 6. Session Management

Reuse sessions to appear more legitimate:

```python
# Instead of creating new browser for each request
# Reuse the same browser/context for multiple pages
async with async_playwright() as p:
    browser = await p.chromium.launch()
    context = await browser.new_context()
    
    for query in queries:
        page = await context.new_page()
        # scrape...
        await page.close()
        await delay()  # Rate limit
    
    await browser.close()
```

## Alternative Approaches

### Option 1: MercadoLibre Official API

**Pros:**
- No scraping needed
- Reliable and legal
- Better performance
- Official support

**Cons:**
- Requires business registration
- API approval process
- Rate limits
- May not have all public listings

**How to apply:**
https://developers.mercadolibre.com.co/

### Option 2: Manual HTML Analysis

For development and testing, use sample HTML:

1. Manually fetch a page (via browser)
2. Save HTML to file
3. Use for scraper development
4. Test selectors on real HTML structure

```python
# Load saved HTML for testing
with open('sample_page.html', 'r') as f:
    html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    # Test your selectors
```

### Option 3: Reduced Frequency

Instead of scraping on every request:
- Cache results for 1-6 hours
- Run scraper as background job (hourly/daily)
- Serve cached data to users

```python
from datetime import datetime, timedelta

class CachedScraper:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    async def get_results(self, query):
        cache_key = query
        
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return data  # Return cached
        
        # Scrape fresh data
        data = await self.scrape(query)
        self.cache[cache_key] = (datetime.now(), data)
        return data
```

## Scraper Configuration

Update `.env` to control scraping behavior:

```bash
# Scraping delays (seconds)
SCRAPING_DELAY_MIN=3
SCRAPING_DELAY_MAX=7

# Max concurrent scrapers
MAX_CONCURRENT_SCRAPERS=1

# Retry configuration
SCRAPING_MAX_RETRIES=3
SCRAPING_RETRY_DELAY=5

# Cache duration (seconds)
SCRAPING_CACHE_DURATION=3600

# Enable stealth mode
SCRAPING_STEALTH_MODE=true
```

## Error Handling in Code

Update scrapers to handle 403 gracefully:

```python
async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
    """Scrape with error handling."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await self._create_stealth_context(browser)
            page = await context.new_page()
            
            try:
                response = await page.goto(url, timeout=30000)
                
                if response.status == 403:
                    print(f"⚠️  403 Forbidden for {url}")
                    print("   Try: increase delays, use stealth mode, or rotate proxies")
                    return []
                
                if response.status != 200:
                    print(f"⚠️  Unexpected status {response.status} for {url}")
                    return []
                
                # Continue scraping...
                
            except PlaywrightTimeout:
                print(f"⚠️  Timeout loading {url}")
                return []
                
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"⚠️  Scraping error: {e}")
        return []
    
    return listings
```

## Testing Without Live Site

Use the sample HTML structure for development:

```bash
# Run analysis tool
python3 /tmp/analyze_html.py

# This creates:
# - /tmp/ml_sample_structure.html (sample HTML)
# - Key selectors for development
```

## Best Practices Summary

1. ✅ **Always use realistic headers**
2. ✅ **Enable Playwright stealth mode**
3. ✅ **Implement rate limiting (3-7 second delays)**
4. ✅ **Use retry logic with backoff**
5. ✅ **Cache results when possible**
6. ✅ **Handle 403 errors gracefully**
7. ✅ **Log errors for monitoring**
8. ✅ **Consider proxy rotation for production**
9. ✅ **Test with sample HTML first**
10. ✅ **Explore official API as alternative**

## Monitoring

Track scraping success/failure:

```python
import logging

logger = logging.getLogger(__name__)

async def scrape(self, query: str):
    try:
        # ... scraping logic
        logger.info(f"✓ Scraped {len(results)} items for '{query}'")
        return results
    except Exception as e:
        logger.error(f"✗ Scraping failed for '{query}': {e}")
        return []
```

## Conclusion

403 Forbidden errors are common when scraping. The best approach is:

1. **Development**: Use sample HTML and selectors
2. **Testing**: Enable stealth mode with delays
3. **Production**: Add proxy rotation + caching
4. **Long-term**: Apply for official API access

Always respect website policies and implement responsible scraping practices.
