"""
VendeTuNave Rust-backed scraper.

Delegates the actual HTTP scraping to the compiled Rust binary
(`vendetunave-scraper`), which queries
https://www.vendetunave.co/vehiculos/carrosycamionetas using the site's
search bar and returns a JSON array of vehicle listings.

The binary is expected to be available either on PATH or at the path
configured via the VENDETUNAVE_RUST_BIN environment variable.
"""
import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Optional

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Allow operators to point at a custom binary location.
_DEFAULT_BINARY = "vendetunave-scraper"
_BINARY_PATH = os.environ.get("VENDETUNAVE_RUST_BIN", _DEFAULT_BINARY)


class VendeTuNaveRustScraper(BaseScraper):
    """
    Scraper for VendeTuNave Colombia that uses a compiled Rust binary.

    The Rust binary handles all networking and HTML parsing, then writes a
    JSON array to stdout.  This Python class is responsible only for
    launching the process, collecting its output, and normalising the
    results into the CarScan format.
    """

    def get_source_name(self) -> str:
        return "VendeTuNave"

    async def scrape(self, query: str, city: str = "Medellín") -> List[Dict]:
        """
        Run the Rust scraper binary and return normalised vehicle listings.

        Args:
            query: Search query (e.g. "Toyota Corolla 2019")
            city:  City used as fallback when the listing has no city field.

        Returns:
            List of normalised vehicle listing dictionaries.
        """
        try:
            raw_listings = await self._run_binary(query)
        except FileNotFoundError:
            logger.error(
                "vendetunave-scraper binary not found at '%s'. "
                "Build it with `cargo build --release` inside rust-scraper/ "
                "and make sure the binary is on PATH or set VENDETUNAVE_RUST_BIN.",
                _BINARY_PATH,
            )
            return []
        except Exception as exc:
            logger.error("VendeTuNaveRustScraper error: %s", exc, exc_info=True)
            return []

        listings = []
        for item in raw_listings:
            try:
                listing = {
                    "title": item.get("title", ""),
                    "price": item.get("price"),
                    "year": item.get("year"),
                    "mileage": item.get("mileage"),
                    "latitude": None,
                    "longitude": None,
                    "city": item.get("city") or city,
                    "url": item.get("url", ""),
                }
                if listing["title"] and listing["url"]:
                    listings.append(self.normalize_listing(listing))
            except Exception:
                continue

        logger.info(
            "VendeTuNaveRustScraper: %d listings found for query '%s'.",
            len(listings),
            query,
        )
        return listings

    async def _run_binary(self, query: str) -> List[Dict]:
        """
        Execute the Rust binary in a thread pool so it does not block the
        asyncio event loop, then parse and return its JSON output.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._invoke_binary, query)

    def _invoke_binary(self, query: str) -> List[Dict]:
        """Synchronous helper that calls the Rust binary via subprocess."""
        cmd = [_BINARY_PATH, "--query", query]
        logger.debug("Running: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.warning(
                "vendetunave-scraper exited with code %d. stderr: %s",
                result.returncode,
                result.stderr,
            )

        stdout = result.stdout.strip()
        if not stdout:
            return []

        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                return data
            logger.warning("Unexpected JSON output from binary: %s", type(data))
            return []
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse binary JSON output: %s", exc)
            return []
