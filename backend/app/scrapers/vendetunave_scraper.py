"""
VendeTuNave Colombia scraper.

VendeTuNave is a Colombian marketplace for vehicles (cars, motorcycles, boats).
The site is built with Next.js and embeds all listing data as JSON inside a
<script id="__NEXT_DATA__"> tag on the page.

This scraper extracts that JSON directly — no Playwright needed.
URL pattern discovered from the HTML:
  https://www.vendetunave.co/vehiculos/carrosycamionetas?q=<query>&ciudad=<city>

The JSON structure (from __NEXT_DATA__) is:
  props.pageProps.data.vehicles  -> list of vehicle objects
Each vehicle has: id, title, descripcion, precio, marca, modelo, ano,
  kilometraje, combustible, transmision, labelCiudad, labelDep, nameImage, extension
"""
import json
import re
import logging
import asyncio
import random
from typing import List, Dict, Optional
from urllib.parse import quote_plus

import httpx

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class VendeTuNaveScraper(BaseScraper):
    """Scraper for VendeTuNave Colombia marketplace."""

    BASE_URL = "https://www.vendetunave.co"
    LISTING_URL = "https://www.vendetunave.co/vehiculos/carrosycamionetas"
    IMAGE_BASE = "https://static.vendetunave.co/images/vehiculos"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    def get_source_name(self) -> str:
        return "VendeTuNave"

    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Scrape vehicle listings from VendeTuNave.

        Fetches the Next.js page and extracts the __NEXT_DATA__ JSON blob,
        which contains all listing data pre-rendered by the server.

        Args:
            query: Search query (e.g., "Toyota Corolla 2015")
            city: City to search in (default: Medellín)

        Returns:
            List of normalized vehicle listings
        """
        listings = []

        try:
            # Build search URL
            params = {"q": query}
            if city:
                params["ciudad"] = city.lower()

            url = self.LISTING_URL
            query_string = "&".join(f"{k}={quote_plus(v)}" for k, v in params.items())
            full_url = f"{url}?{query_string}"

            logger.info(f"VendeTuNave: fetching {full_url}")

            async with httpx.AsyncClient(
                headers=self.HEADERS,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = await client.get(full_url)

            if response.status_code == 403:
                logger.warning(f"VendeTuNave returned 403 Forbidden for query: {query}")
                return listings

            if response.status_code != 200:
                logger.warning(
                    f"VendeTuNave returned status {response.status_code} for query: {query}"
                )
                return listings

            html = response.text

            # Extract the __NEXT_DATA__ JSON blob
            vehicles = self._extract_next_data_vehicles(html)

            if not vehicles:
                logger.warning(f"VendeTuNave: no vehicles found in __NEXT_DATA__ for query: {query}")
                return listings

            logger.info(f"VendeTuNave: found {len(vehicles)} vehicles for query: {query}")

            for vehicle in vehicles:
                try:
                    listing = self._parse_vehicle(vehicle)
                    if listing:
                        listings.append(self.normalize_listing(listing))
                except Exception as e:
                    logger.debug(f"VendeTuNave: error parsing vehicle: {e}")
                    continue

                # Polite delay between processing items
                await asyncio.sleep(random.uniform(0.05, 0.15))

        except httpx.RequestError as e:
            logger.error(f"VendeTuNave network error for query '{query}': {e}")
        except Exception as e:
            logger.error(f"VendeTuNave scraper error for query '{query}': {e}", exc_info=True)

        logger.info(f"VendeTuNave: returning {len(listings)} listings.")
        return listings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_next_data_vehicles(self, html: str) -> List[Dict]:
        """
        Parse the __NEXT_DATA__ <script> tag and return the vehicles list.

        JSON path: props -> pageProps -> data -> vehicles
        """
        try:
            match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            if not match:
                logger.warning("VendeTuNave: __NEXT_DATA__ script tag not found")
                return []

            next_data = json.loads(match.group(1))
            vehicles = (
                next_data
                .get("props", {})
                .get("pageProps", {})
                .get("data", {})
                .get("vehicles", [])
            )
            return vehicles if isinstance(vehicles, list) else []

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"VendeTuNave: failed to parse __NEXT_DATA__: {e}")
            return []

    def _parse_vehicle(self, v: Dict) -> Optional[Dict]:
        """
        Transform a raw vehicle object from the API JSON into our standard format.

        Fields available (from the HTML you shared):
          id, title, descripcion, precio, marca, modelo, ano, kilometraje,
          combustible, transmision, labelCiudad, labelDep, nameImage, extension,
          condicion, tipoPrecioLabel, financiacion, permuta
        """
        vehicle_id = v.get("id")
        title = v.get("title", "").strip()

        if not title or not vehicle_id:
            return None

        # Price is an integer in Colombian pesos.
        # Keep it as a plain integer string (no decimal point) so that
        # base_scraper._parse_price doesn't mistake the "." in "53000000.0"
        # for a Colombian thousand separator and remove it, producing 530000000.
        price_raw = v.get("precio")
        price = int(price_raw) if price_raw and isinstance(price_raw, (int, float)) else None

        # Year
        year = v.get("ano")
        if year:
            try:
                year = int(year)
                if not (1900 <= year <= 2030):
                    year = None
            except (ValueError, TypeError):
                year = None

        # Mileage
        mileage = v.get("kilometraje")
        if mileage:
            try:
                mileage = int(mileage)
            except (ValueError, TypeError):
                mileage = None

        # City / location
        city = v.get("labelCiudad", "").strip().title()
        if not city:
            city = v.get("labelDep", "").strip().title()

        # Build the listing URL (vehicle detail page)
        # Pattern: /vehiculo/<id>/<slug-from-title>
        slug = title.lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        url = f"{self.BASE_URL}/vehiculo/{vehicle_id}/{slug}"

        # Build image URL
        name_image = v.get("nameImage", "")
        extension = v.get("extension", "jpeg")
        image_url = None
        if name_image:
            image_url = f"{self.IMAGE_BASE}/{name_image}.{extension}"

        return {
            "title": title,
            "price": str(price) if price is not None else None,
            "year": str(year) if year else None,
            "mileage": str(mileage) if mileage else None,
            "latitude": None,
            "longitude": None,
            "city": city,
            "url": url,
            "image_url": image_url,
            "description": v.get("descripcion", "").strip(),
            "brand": v.get("marca", "").strip(),
            "model": v.get("modelo", "").strip(),
            "fuel": v.get("combustible", "").strip(),
            "transmission": v.get("transmision", "").strip(),
            "condition": v.get("condicion", "").strip(),
        }
