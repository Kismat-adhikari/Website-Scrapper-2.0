"""
Browser Predictor - Phase 4 Implementation
Predicts when to use browser rendering vs regular HTTP
"""

import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BrowserPredictor:
    """Predicts whether a site needs browser rendering"""
    
    # Known JS-heavy domains that need browser rendering
    JS_HEAVY_DOMAINS = {
        # Social media
        'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
        'tiktok.com', 'pinterest.com', 'reddit.com',
        
        # Single Page Apps
        'angular.io', 'react.dev', 'vuejs.org',
        
        # Common SPA frameworks indicators
        'vercel.app', 'netlify.app', 'herokuapp.com',
        
        # Known problematic sites
        'cloudflare.com', 'akamai.com'
    }
    
    # Indicators in HTML that suggest JS rendering needed
    JS_INDICATORS = [
        'react', 'angular', 'vue', 'ember', 'backbone',
        'webpack', 'browserify', 'rollup',
        '__NEXT_DATA__', '__NUXT__', 'ng-app',
        'data-reactroot', 'data-react-helmet',
        'spa-', 'single-page'
    ]
    
    # Indicators that site is static/simple
    STATIC_INDICATORS = [
        'wordpress', 'wix', 'squarespace', 'shopify',
        'drupal', 'joomla', 'blogger'
    ]
    
    def __init__(self):
        self.prediction_cache = {}
        self.success_rate = {}  # Track prediction accuracy
    
    def should_use_browser(self, url: str, html: Optional[str] = None, 
                          response_time: Optional[float] = None) -> bool:
        """
        Predict if browser rendering is needed
        
        Args:
            url: URL to check
            html: HTML content (if available)
            response_time: Response time in seconds
        
        Returns:
            True if browser rendering recommended
        """
        # Check cache first
        if url in self.prediction_cache:
            return self.prediction_cache[url]
        
        domain = self._extract_domain(url)
        
        # Check if domain is known JS-heavy
        if self._is_js_heavy_domain(domain):
            logger.info(f"Domain {domain} is known JS-heavy")
            self.prediction_cache[url] = True
            return True
        
        # If we have HTML, analyze it
        if html:
            html_lower = html.lower()
            
            # Check for static site indicators (don't need browser)
            static_score = sum(1 for indicator in self.STATIC_INDICATORS 
                             if indicator in html_lower)
            
            if static_score >= 2:
                logger.info(f"Site appears to be static (score: {static_score})")
                self.prediction_cache[url] = False
                return False
            
            # Check for JS framework indicators
            js_score = sum(1 for indicator in self.JS_INDICATORS 
                          if indicator in html_lower)
            
            if js_score >= 3:
                logger.info(f"Site appears to be JS-heavy (score: {js_score})")
                self.prediction_cache[url] = True
                return True
            
            # Check if HTML is suspiciously small (might be SPA shell)
            if len(html) < 5000 and '<div id="root"' in html_lower:
                logger.info("Site has small HTML with root div (likely SPA)")
                self.prediction_cache[url] = True
                return True
        
        # Check response time (slow = likely JS-heavy)
        if response_time and response_time > 3.0:
            logger.info(f"Slow response time ({response_time:.2f}s) suggests JS rendering")
            self.prediction_cache[url] = True
            return True
        
        # Default: don't use browser (faster)
        self.prediction_cache[url] = False
        return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''
    
    def _is_js_heavy_domain(self, domain: str) -> bool:
        """Check if domain is known to be JS-heavy"""
        # Check exact match
        if domain in self.JS_HEAVY_DOMAINS:
            return True
        
        # Check if any known domain is a suffix
        for js_domain in self.JS_HEAVY_DOMAINS:
            if domain.endswith(js_domain):
                return True
        
        return False
    
    def record_success(self, url: str, used_browser: bool, found_data: bool):
        """
        Record prediction success/failure for learning
        
        Args:
            url: URL that was scraped
            used_browser: Whether browser was used
            found_data: Whether data was found
        """
        domain = self._extract_domain(url)
        
        if domain not in self.success_rate:
            self.success_rate[domain] = {
                'browser_success': 0,
                'browser_fail': 0,
                'http_success': 0,
                'http_fail': 0
            }
        
        if used_browser:
            if found_data:
                self.success_rate[domain]['browser_success'] += 1
            else:
                self.success_rate[domain]['browser_fail'] += 1
        else:
            if found_data:
                self.success_rate[domain]['http_success'] += 1
            else:
                self.success_rate[domain]['http_fail'] += 1
    
    def get_stats(self) -> dict:
        """Get predictor statistics"""
        return {
            'cached_predictions': len(self.prediction_cache),
            'tracked_domains': len(self.success_rate),
            'js_heavy_domains': len(self.JS_HEAVY_DOMAINS)
        }
    
    def clear_cache(self):
        """Clear prediction cache"""
        self.prediction_cache.clear()
        logger.info("Cleared browser prediction cache")


# Global predictor instance
_predictor: Optional[BrowserPredictor] = None


def get_browser_predictor() -> BrowserPredictor:
    """Get or create the global browser predictor"""
    global _predictor
    
    if _predictor is None:
        _predictor = BrowserPredictor()
    
    return _predictor
