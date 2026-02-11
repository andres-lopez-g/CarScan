"""
Scrapers package initialization.
"""
from .base_scraper import BaseScraper
from .mercadolibre_scraper import MercadoLibreScraper
from .tucarro_scraper import TuCarroScraper

__all__ = ["BaseScraper", "MercadoLibreScraper", "TuCarroScraper"]
