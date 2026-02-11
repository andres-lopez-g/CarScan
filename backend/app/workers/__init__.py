"""
Background workers for asynchronous scraping tasks.

This module will handle background scraping jobs using Celery.
For now, scraping happens synchronously in the API request.
"""

# Future implementation: Celery workers for background scraping
# from celery import Celery
# from app.core.config import settings
# 
# celery_app = Celery('carscan', broker=settings.redis_url)
