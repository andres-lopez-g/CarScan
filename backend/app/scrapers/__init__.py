"""
Scrapers package initialization.
"""
from .base_scraper import BaseScraper
from .mercadolibre_scraper import MercadoLibreScraper

__all__ = ["BaseScraper", "MercadoLibreScraper"]
