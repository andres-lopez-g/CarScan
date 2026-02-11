# CarScan API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Search Vehicles

Search for vehicle listings from MercadoLibre.

**Endpoint:** `POST /vehicles/search`

**Request Body:**
```json
{
  "query": "Toyota Corolla 2015",
  "user_lat": 6.2442,
  "user_lon": -75.5812,
  "max_distance_km": 50,
  "min_price": 20000000,
  "max_price": 50000000,
  "min_year": 2010,
  "max_year": 2020,
  "max_mileage": 150000,
  "city": "Medellín"
}
```

**Response:**
```json
{
  "query": "Toyota Corolla 2015",
  "total_results": 25,
  "listings": [
    {
      "id": 1,
      "source": "MercadoLibre",
      "title": "Toyota Corolla 2015 XEI",
      "price": 35000000,
      "year": 2015,
      "mileage": 80000,
      "latitude": 6.2518,
      "longitude": -75.5636,
      "city": "Medellín",
      "url": "https://...",
      "created_at": "2024-01-15T10:30:00",
      "score": 0.45,
      "distance_km": 2.3
    }
  ]
}
```

### 2. Health Check

**Endpoint:** `GET /vehicles/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "CarScan API"
}
```

## Scoring Algorithm

```
score = (price_normalized × 0.5) + (mileage_normalized × 0.3) + (year_normalized × 0.2)
```

Lower score = better offer
