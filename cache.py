"""
Simple in-memory cache for HTTP responses and extraction results
"""

import time
import threading
from typing import Optional, Dict, Any


class SimpleCache:
    """Thread-safe in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
        self.stats = {'hits': 0, 'misses': 0, 'expired': 0}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry['timestamp'] < entry['ttl']:
                    self.stats['hits'] += 1
                    return entry['value']
                else:
                    # Expired
                    del self.cache[key]
                    self.stats['expired'] += 1
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        with self.lock:
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self.default_ttl
            }
    
    def delete(self, key: str):
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'expired': self.stats['expired'],
                'hit_rate': round(self.stats['hits'] / max(1, self.stats['hits'] + self.stats['misses']) * 100, 2)
            }


# Global cache instances
http_cache = SimpleCache(default_ttl=3600)  # 1 hour for HTTP responses
extraction_cache = SimpleCache(default_ttl=3600)  # 1 hour for extraction results
