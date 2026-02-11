# CarScan - Quick Start Guide

This guide will help you get CarScan up and running in minutes.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker + Docker Compose (Linux)
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/andres-lopez-g/CarScan.git
cd CarScan
```

### 2. Configure Environment (Optional)

The application works with default settings, but you can customize if needed:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env if you want to change any settings
```

### 3. Start the Application

```bash
docker-compose up --build
```

This will:
- Build the backend (FastAPI) container
- Build the frontend (Next.js) container
- Start PostgreSQL with PostGIS extension
- Start Redis for caching
- Initialize the database
- Start all services

**First-time build may take 5-10 minutes to download dependencies.**

### 4. Access the Application

Once all services are running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Using CarScan

### Web Interface

1. Open http://localhost:3000 in your browser
2. Enter a search query (e.g., "Toyota Corolla 2015")
3. Click "Search"
4. View results on the map and in the list
5. Click "View Original Listing" to see the vehicle on MercadoLibre

### API Usage

You can also use the API directly:

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Toyota Corolla 2015",
    "city": "Medellín",
    "max_distance_km": 50
  }'
```

## Stopping the Application

```bash
# Stop all services (Ctrl+C in the terminal, then:)
docker-compose down

# To also remove volumes (database data):
docker-compose down -v
```

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, 5432, or 6379 are already in use, you can either:
- Stop the service using that port
- Modify the port mappings in `docker-compose.yml`

### Build Failures

If the build fails:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database Connection Issues

Wait for the database health check to complete. You'll see:
```
carscan_db | database system is ready to accept connections
```

### Playwright Installation Issues

The first build installs Playwright browsers, which can take time. If it fails:
```bash
docker-compose down
docker-compose build backend --no-cache
docker-compose up
```

## Development Mode

For development with hot-reload:

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Next Steps

- Check the [README.md](README.md) for full documentation
- Explore the [API Documentation](docs/API.md)
- View [API Swagger UI](http://localhost:8000/docs) when running

## Support

For issues or questions, please open an issue on GitHub.
