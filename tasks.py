"""
Celery Tasks for Background Scraping - Phase 3 Implementation
Handles async job processing with Redis queue
"""

import logging
from celery import Celery
from datetime import datetime
import json

from scraper import ProxyManager
from async_scraper import scrape_url_async_wrapper

logger = logging.getLogger(__name__)

# Initialize Celery with Redis backend
celery_app = Celery(
    'scraper_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Initialize proxy manager (shared across workers)
proxy_manager = ProxyManager()


@celery_app.task(bind=True, name='tasks.scrape_url_task')
def scrape_url_task(self, url: str, options: dict = None):
    """
    Background task to scrape a single URL
    
    Args:
        url: URL to scrape
        options: Scraping options (fast_mode, enable_validation, etc.)
    
    Returns:
        dict: Scraping results
    """
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Starting scrape'})
        
        # Parse options
        options = options or {}
        fast_mode = options.get('fast_mode', True)
        enable_validation = options.get('enable_validation', False)
        
        logger.info(f"Starting scrape task for {url}")
        
        # Scrape URL using async scraper
        result = scrape_url_async_wrapper(
            url=url,
            proxy_manager=proxy_manager,
            fast_mode=fast_mode
        )
        
        # Convert result to dict
        result_dict = {
            'url': result.url,
            'success': result.success,
            'emails': list(result.emails),
            'phones': list(result.phones),
            'social_links': result.social_links,
            'company_name': result.company_name,
            'address': result.address,
            'fetch_mode': result.fetch_mode.value if result.fetch_mode else None,
            'fetch_time': result.fetch_time,
            'confidence_score': result.confidence_score,
            'failure_reason': result.failure_reason.value if result.failure_reason else None,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Completed scrape task for {url} in {result.fetch_time:.2f}s")
        
        return result_dict
        
    except Exception as e:
        logger.error(f"Error in scrape task for {url}: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True, name='tasks.scrape_batch_task')
def scrape_batch_task(self, urls: list, options: dict = None):
    """
    Background task to scrape multiple URLs
    
    Args:
        urls: List of URLs to scrape
        options: Scraping options
    
    Returns:
        list: List of scraping results
    """
    try:
        self.update_state(state='PROCESSING', meta={
            'status': 'Starting batch scrape',
            'total': len(urls),
            'completed': 0
        })
        
        options = options or {}
        results = []
        
        for i, url in enumerate(urls):
            try:
                # Scrape single URL
                result = scrape_url_task(url, options)
                results.append(result)
                
                # Update progress
                self.update_state(state='PROCESSING', meta={
                    'status': 'Processing',
                    'total': len(urls),
                    'completed': i + 1,
                    'current_url': url
                })
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })
        
        logger.info(f"Completed batch scrape: {len(results)}/{len(urls)} successful")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch scrape task: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
