# TuCarro Page Structure Analysis

## Overview

**TuCarro** (https://carros.tucarro.com.co/) is a Colombian vehicle marketplace that was acquired by MercadoLibre and now operates as part of the MercadoLibre network. The site specializes in vehicle listings (cars and motorcycles) in Colombia.

## Page Structure

### Layout Components

The TuCarro page follows the standard MercadoLibre UI/UX design with three main sections:

#### 1. **Search Bar (Top)**
- **Location**: Top of the page, in the header/navigation area
- **Type**: Text input field with search functionality
- **Common Selectors**:
  - `input[placeholder*="Buscar"]`
  - `.nav-search-input`
  - `form.nav-search input`
  - `header input[type="text"]`
- **Functionality**: 
  - Free-text search for vehicles
  - Accepts queries like "Toyota Corolla 2015", "Mazda CX-5", "motos"
  - Triggers search on Enter key or submit button click

#### 2. **Filters (Left Sidebar)**
- **Location**: Left side of the page, below the search results
- **Type**: Collapsible filter groups
- **Common Filter Categories**:
  - **Marca** (Brand): Toyota, Chevrolet, Mazda, Renault, etc.
  - **Modelo** (Model): Specific vehicle models
  - **Año** (Year): Range selector or checkboxes
  - **Precio** (Price): Min/max price inputs
  - **Kilómetros** (Mileage): Mileage range
  - **Combustible** (Fuel Type): Gasolina, Diesel, Eléctrico, Híbrido
  - **Transmisión** (Transmission): Manual, Automática
  - **Ubicación** (Location): Cities and regions
  - **Color**: Vehicle color options
  - **Tipo de vendedor** (Seller Type): Concesionario, Particular
  
- **Common Selectors**:
  - `.ui-search-filter-groups`
  - `.ui-search-sidebar`
  - `aside`
  - `.ui-search-filter-dl-title` (filter titles)
  - `.ui-search-filter-name` (filter options)

#### 3. **Search Results (Center/Right)**
- **Location**: Main content area, to the right of filters
- **Type**: Grid or list of vehicle listings
- **Result Card Structure**:
  - **Title**: Vehicle name (brand, model, year)
  - **Price**: COP (Colombian Peso) format
  - **Thumbnail**: Vehicle image
  - **Attributes**: Year, mileage, location
  - **Link**: URL to detailed listing page

- **Common Selectors**:
  - `.ui-search-result` (each listing card)
  - `.ui-search-item__title` (listing title)
  - `.andes-money-amount__fraction` (price)
  - `.ui-search-item__group--location` (location)
  - `a.ui-search-link` (listing URL)

## Technical Details

### Platform Architecture
- **Framework**: React-based SPA (Single Page Application)
- **Rendering**: Client-side JavaScript rendering
- **API**: Internal MercadoLibre API calls
- **CSS Framework**: Andes Design System (MercadoLibre's design system)

### URL Structure

#### Homepage
```
https://carros.tucarro.com.co/
```
*Note: This may redirect to `carros.mercadolibre.com.co`*

#### Search Results
```
https://carros.tucarro.com.co/[query]
https://carros.tucarro.com.co/toyota-corolla-2015
https://carros.tucarro.com.co/mazda-cx-5_NoIndex_True
```

#### With Filters
```
https://carros.tucarro.com.co/[query]?[filters]
Example:
https://carros.tucarro.com.co/toyota?YEAR=2015-*&PRICE=*-50000000
```

### Key CSS Classes (Andes Design System)

#### Layout
- `.ui-search-layout` - Main layout container
- `.ui-search-sidebar` - Left sidebar with filters
- `.ui-search-main` - Main content area with results

#### Search Results
- `.ui-search-results` - Results container
- `.ui-search-result` - Individual result card
- `.ui-search-result__content` - Result content wrapper
- `.ui-search-result__image` - Result image container

#### Result Details
- `.ui-search-item__title` - Listing title
- `.ui-search-item__subtitle` - Optional subtitle
- `.andes-money-amount` - Price container
- `.andes-money-amount__fraction` - Price number
- `.andes-money-amount__currency-symbol` - Currency symbol
- `.ui-search-item__group--location` - Location text
- `.ui-search-item__group--attributes` - Attributes (year, km, etc.)

#### Filters
- `.ui-search-filter-groups` - All filter groups
- `.ui-search-filter-group` - Single filter group
- `.ui-search-filter-dl-title` - Filter category title
- `.ui-search-filter-name` - Individual filter option
- `.ui-search-filter-checkbox` - Checkbox input

### Data Extraction Strategy

#### Using Playwright (Recommended)
Since TuCarro uses JavaScript rendering, Playwright is necessary to:
1. Wait for dynamic content to load
2. Execute JavaScript to extract rendered data
3. Handle lazy-loaded images and content

#### Extraction Points
1. **Navigate to search URL**
2. **Wait for results selector**: `.ui-search-result`
3. **Extract from each result**:
   - Title from `.ui-search-item__title`
   - Price from `.andes-money-amount__fraction`
   - URL from `a.ui-search-link[href]`
   - Location from `.ui-search-item__group--location`
   - Attributes from `.ui-search-item__group--attributes`

4. **Parse attributes** (from title or attributes text):
   - Year: Regex `\b(19[0-9]{2}|20[0-2][0-9]|2030)\b`
   - Mileage: Regex `(\d{1,3}(?:[.,]\d{3})*)\s*(?:km|kilómetros)`

## Relationship with MercadoLibre

TuCarro is a **MercadoLibre brand** and uses the **same platform and infrastructure**:

- **Shared Codebase**: Uses MercadoLibre's Andes Design System
- **Same Selectors**: CSS classes are identical
- **Same API**: Backend API is MercadoLibre's
- **Unified Search**: Results may appear in both TuCarro and MercadoLibre

### Implications for Scraping
1. **Reusable Logic**: MercadoLibre scraper can be adapted for TuCarro with minimal changes
2. **Same Selectors**: CSS selectors are identical or very similar
3. **Similar Structure**: Page layout and HTML structure are the same
4. **Common Challenges**: Both have JavaScript rendering, rate limiting, bot detection

## Scraping Considerations

### Legal & Ethical
✅ Public data only (no login required)  
✅ Rate limiting required (2-5 seconds between requests)  
✅ Respect robots.txt  
✅ Include original listing URLs  
✅ Do not store/rehost images  
✅ Realistic user agents  

### Technical Challenges
⚠️ **JavaScript Rendering**: Requires Playwright or similar  
⚠️ **Dynamic Content**: Wait for elements to load  
⚠️ **Rate Limiting**: Avoid IP blocks  
⚠️ **Selector Changes**: MercadoLibre may update UI  
⚠️ **Bot Detection**: May need proxy rotation for heavy usage  

### Best Practices
1. **Use Playwright** with headless Chromium
2. **Wait for selectors** before extracting
3. **Random delays** between requests (2-5 seconds)
4. **Realistic user agent** and viewport
5. **Error handling** for missing elements
6. **Fallback selectors** for robustness
7. **Limit results** per request (e.g., 20-50)

## Example Query Patterns

### By Vehicle Type
```
https://carros.tucarro.com.co/carros
https://carros.tucarro.com.co/motos
```

### By Brand
```
https://carros.tucarro.com.co/toyota
https://carros.tucarro.com.co/chevrolet
https://carros.tucarro.com.co/mazda
```

### By Brand and Model
```
https://carros.tucarro.com.co/toyota-corolla
https://carros.tucarro.com.co/chevrolet-spark
https://carros.tucarro.com.co/mazda-cx-5
```

### With Year
```
https://carros.tucarro.com.co/toyota-corolla-2015
https://carros.tucarro.com.co/chevrolet-spark-2018
```

### With Location
```
https://carros.tucarro.com.co/toyota?STATE=52  # Medellín
https://carros.tucarro.com.co/mazda?STATE=7    # Bogotá
```

## Implementation Recommendations

### Approach 1: Separate TuCarro Scraper (Recommended)
Create a dedicated `TuCarroScraper` class that:
- Inherits from `BaseScraper`
- Uses TuCarro-specific URL: `https://carros.tucarro.com.co/`
- Reuses MercadoLibre's selectors (or shares a mixin)
- Allows independent configuration and rate limiting

**Pros**: 
- Clear separation of concerns
- Independent rate limiting per source
- Easier to maintain and debug
- Can track source separately

### Approach 2: Unified MercadoLibre/TuCarro Scraper
Extend `MercadoLibreScraper` to support both domains:
- Accept `base_url` parameter
- Use same selectors and logic
- Toggle between `carros.mercadolibre.com.co` and `carros.tucarro.com.co`

**Pros**:
- Less code duplication
- Simplified maintenance
- Shared selector updates

### Recommended: Approach 1 with Shared Mixin

```python
# scrapers/mercadolibre_base.py
class MercadoLibreBaseMixin:
    """Shared logic for MercadoLibre-platform scrapers."""
    
    def get_result_selectors(self):
        return {
            'result': '.ui-search-result',
            'title': '.ui-search-item__title',
            'price': '.andes-money-amount__fraction',
            'link': 'a.ui-search-link',
            'location': '.ui-search-item__group--location',
            'attributes': '.ui-search-item__group--attributes'
        }

# scrapers/mercadolibre_scraper.py
class MercadoLibreScraper(BaseScraper, MercadoLibreBaseMixin):
    BASE_URL = "https://carros.mercadolibre.com.co"

# scrapers/tucarro_scraper.py
class TuCarroScraper(BaseScraper, MercadoLibreBaseMixin):
    BASE_URL = "https://carros.tucarro.com.co"
```

## Data Normalization

Both TuCarro and MercadoLibre listings should be normalized to:

```python
{
    "source": "TuCarro" | "MercadoLibre",
    "title": str,          # Full listing title
    "price": float,        # Normalized price (COP)
    "year": int,           # Vehicle year (2010-2030)
    "mileage": int,        # Kilometers
    "latitude": float,     # Geocoded from city
    "longitude": float,    # Geocoded from city
    "city": str,           # Colombian city name
    "url": str,            # Original listing URL
}
```

## Testing Strategy

1. **Unit Tests**: Test selector extraction and normalization
2. **Integration Tests**: Test full scrape with mock Playwright
3. **Manual Tests**: Verify against live site (with rate limiting)
4. **Comparison**: Compare results between MercadoLibre and TuCarro

## Conclusion

TuCarro is essentially a branded version of MercadoLibre focused on vehicles. The implementation can reuse most of the MercadoLibre scraper logic with minimal modifications. The key is to maintain the same structure and selectors while allowing for independent configuration and rate limiting per source.

**Key Takeaways**:
- ✓ Search bar at top (standard MercadoLibre header)
- ✓ Filters on left sidebar (collapsible categories)
- ✓ Results in center/right (grid of cards)
- ✓ Uses Andes Design System (MercadoLibre's CSS framework)
- ✓ Requires JavaScript rendering (Playwright needed)
- ✓ Can reuse MercadoLibre scraper logic with URL change
