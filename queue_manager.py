"""
Queue Manager - Phase 3 Implementation
Manages job queue, status tracking, and result caching
"""

import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enum"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class QueueManager:
    """Manages job queue and result caching with Redis"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=2):
        """Initialize queue manager with Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def store_job(self, job_id: str, url: str, options: dict = None) -> bool:
        """
        Store job metadata
        
        Args:
            job_id: Unique job identifier
            url: URL to scrape
            options: Scraping options
        
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False
        
        try:
            job_data = {
                'job_id': job_id,
                'url': url,
                'options': options or {},
                'status': JobStatus.PENDING.value,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Store job with 1 hour TTL
            self.redis_client.setex(
                f'job:{job_id}',
                timedelta(hours=1),
                json.dumps(job_data)
            )
            
            logger.info(f"Stored job {job_id} for URL {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job metadata
        
        Args:
            job_id: Job identifier
        
        Returns:
            dict: Job data or None
        """
        if not self.redis_client:
            return None
        
        try:
            job_data = self.redis_client.get(f'job:{job_id}')
            if job_data:
                return json.loads(job_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: JobStatus, meta: dict = None) -> bool:
        """
        Update job status
        
        Args:
            job_id: Job identifier
            status: New status
            meta: Additional metadata
        
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False
        
        try:
            job_data = self.get_job(job_id)
            if not job_data:
                return False
            
            job_data['status'] = status.value
            job_data['updated_at'] = datetime.now().isoformat()
            
            if meta:
                job_data.update(meta)
            
            self.redis_client.setex(
                f'job:{job_id}',
                timedelta(hours=1),
                json.dumps(job_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False
    
    def store_result(self, job_id: str, result: dict) -> bool:
        """
        Store scraping result
        
        Args:
            job_id: Job identifier
            result: Scraping result
        
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False
        
        try:
            # Store result with 1 hour TTL
            self.redis_client.setex(
                f'result:{job_id}',
                timedelta(hours=1),
                json.dumps(result)
            )
            
            # Update job status
            self.update_job_status(job_id, JobStatus.COMPLETED, {'result_stored': True})
            
            logger.info(f"Stored result for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing result for job {job_id}: {e}")
            return False
    
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get scraping result
        
        Args:
            job_id: Job identifier
        
        Returns:
            dict: Result data or None
        """
        if not self.redis_client:
            return None
        
        try:
            result_data = self.redis_client.get(f'result:{job_id}')
            if result_data:
                return json.loads(result_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting result for job {job_id}: {e}")
            return None
    
    def cache_url_result(self, url: str, result: dict, ttl_hours: int = 1) -> bool:
        """
        Cache result by URL for faster repeated lookups
        
        Args:
            url: URL that was scraped
            result: Scraping result
            ttl_hours: Cache TTL in hours
        
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False
        
        try:
            # Normalize URL for caching
            cache_key = f'url_cache:{url.lower().strip()}'
            
            self.redis_client.setex(
                cache_key,
                timedelta(hours=ttl_hours),
                json.dumps(result)
            )
            
            logger.info(f"Cached result for URL {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result for URL {url}: {e}")
            return False
    
    def get_cached_url_result(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result by URL
        
        Args:
            url: URL to lookup
        
        Returns:
            dict: Cached result or None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f'url_cache:{url.lower().strip()}'
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for URL {url}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result for URL {url}: {e}")
            return None
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job and its result
        
        Args:
            job_id: Job identifier
        
        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(f'job:{job_id}')
            self.redis_client.delete(f'result:{job_id}')
            logger.info(f"Deleted job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Get queue statistics
        
        Returns:
            dict: Queue stats (pending, processing, completed, failed)
        """
        if not self.redis_client:
            return {'error': 'Redis not connected'}
        
        try:
            stats = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'total': 0
            }
            
            # Get all job keys
            job_keys = self.redis_client.keys('job:*')
            stats['total'] = len(job_keys)
            
            # Count by status
            for key in job_keys:
                job_data = json.loads(self.redis_client.get(key))
                status = job_data.get('status', 'unknown')
                if status in stats:
                    stats[status] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'error': str(e)}
