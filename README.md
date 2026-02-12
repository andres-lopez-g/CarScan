# CarScan

**Vehicle Listing Aggregator for Colombia**

CarScan is a production-ready web application that aggregates vehicle listings (cars and motorcycles) from multiple Colombian marketplaces, normalizes the data, and allows users to compare prices and distances using geolocation.

![CarScan](https://img.shields.io/badge/CarScan-Vehicle%20Finder-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

## 🚀 Features

- **Multi-Source Aggregation**: Searches MercadoLibre Colombia, TuCarro, VendeTuNave, FincaRaiz, and BodegasYLocales
- **Price Comparison**: Normalizes prices and ranks listings by best offer
- **Geospatial Search**: Calculate distances from your location
- **Interactive Map**: View listings on OpenStreetMap with Leaflet.js
- **Real-time Scraping**: Responsible web scraping with rate limiting and proper headers to avoid 403 errors
- **Advanced Filtering**: Filter by price, year, mileage, and location
- **Smart Scoring**: AI-powered scoring algorithm to find the best deals

## 🏗️ Tech Stack

### Backend
- **Python 3.11**
- **FastAPI** - Modern, fast web framework
- **PostgreSQL + PostGIS** - Geospatial database
- **SQLAlchemy** - Async ORM
- **Playwright** - Web scraping
- **BeautifulSoup4** - HTML parsing
- **Redis** - Caching and task queue

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Leaflet.js** - Interactive maps
- **OpenStreetMap** - Map tiles
- **Axios** - API client

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Uvicorn** - ASGI server

## 📋 Prerequisites

- Docker and Docker Compose
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/andres-lopez-g/CarScan.git
   cd CarScan
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
CarScan/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core configuration
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── scrapers/         # Web scrapers
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── components/           # React components
│   ├── pages/                # Next.js pages
│   ├── styles/               # CSS styles
│   ├── package.json
│   └── Dockerfile
├── docs/                     # Documentation
├── docker-compose.yml
├── instructions.md
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Application
APP_NAME=CarScan
APP_VERSION=1.0.0
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://carscan:carscan@db:5432/carscan

# Redis
REDIS_URL=redis://redis:6379/0

# Scraping
SCRAPING_DELAY_MIN=2
SCRAPING_DELAY_MAX=5
MAX_CONCURRENT_SCRAPERS=2

# Geospatial
DEFAULT_SEARCH_RADIUS_KM=50
```

## 📡 API Endpoints

### Search Vehicles
```http
POST /api/v1/vehicles/search
Content-Type: application/json

{
  "query": "Toyota Corolla 2015",
  "user_lat": 6.2442,
  "user_lon": -75.5812,
  "max_distance_km": 50,
  "min_price": 20000000,
  "max_price": 50000000,
  "min_year": 2010,
  "max_year": 2020
}
```

### Health Check
```http
GET /health
```

## 🎯 How It Works

1. **User submits a search query** (e.g., "Toyota Corolla 2015")
2. **Backend triggers scraper** for MercadoLibre
3. **Data is normalized** and stored in PostgreSQL
4. **Scoring algorithm** calculates best offer scores:
   - Price (50% weight)
   - Mileage (30% weight)
   - Year (20% weight)
5. **Results are filtered** by user criteria
6. **Distances calculated** from user location (if provided)
7. **Rankings displayed** on interactive map and list view

## 🔒 Legal & Ethical Considerations

CarScan follows responsible scraping practices:

- ✅ No captcha bypassing
- ✅ No login-required scraping
- ✅ Rate limiting and delays between requests
- ✅ Does not store or rehost images
- ✅ Always includes original listing URLs
- ✅ Respects robots.txt

## 🗺️ Geospatial Features

- **PostGIS Integration**: Store and query geographic data
- **Distance Calculations**: Calculate distance between user and listings
- **Radius Filtering**: Filter results within specified radius
- **Interactive Maps**: View listings on OpenStreetMap

## 🧪 Development

### Backend Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev
```

## 📝 MVP Scope

Current MVP includes:
- ✅ One city (Medellín)
- ✅ One source (MercadoLibre)
- ✅ No authentication
- ✅ No payments
- ✅ Map + list view
- ✅ Links to original listings

## 🚧 Future Enhancements

- [x] TuCarro marketplace integration
- [x] Additional marketplace - TuCarro integrated
- [x] BodegasYLocales marketplace integration
- [x] FincaRaiz marketplace integration (warehouse rentals)
- [x] VendeTuNave marketplace integration
- [ ] More cities and regions
- [ ] User authentication
- [ ] Saved searches
- [ ] Price alerts
- [ ] Advanced filters (brand, model, transmission)
- [ ] Favorites and comparisons
- [ ] Mobile app
- [ ] OLX marketplace integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Andres Lopez**
- GitHub: [@andres-lopez-g](https://github.com/andres-lopez-g)

## 🙏 Acknowledgments

- OpenStreetMap contributors
- FastAPI framework
- Next.js team
- Leaflet.js community

---

**CarScan** - Find the best vehicle deals in Colombia 🚗🇨🇴
