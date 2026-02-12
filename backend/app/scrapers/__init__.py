"""
Scrapers package initialization.
"""
from .base_scraper import BaseScraper
from .mercadolibre_scraper import MercadoLibreScraper
from .tucarro_scraper import TuCarroScraper
from .bodegasylocales_scraper import BodegasYLocalesScraper
from .fincaraiz_scraper import FincaRaizScraper
from .vendetunave_scraper import VendeTuNaveScraper

__all__ = [
    "BaseScraper",
    "MercadoLibreScraper",
    "TuCarroScraper",
    "BodegasYLocalesScraper",
    "FincaRaizScraper",
    "VendeTuNaveScraper",
]
