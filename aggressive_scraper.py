"""
Aggressive Scraper Module
Enhanced scraping for maximum coverage - handles JS sites, protected sites, etc.
Automatically tries multiple strategies to extract data from any website.
"""

import logging
import time
from typing import Optional, Tuple, List
from enum import Enum

logger = logging.getLogger('aggressive_scraper')
logger.setLevel(logging.DEBUG)


class ScrapingStrategy(Enum):
    """Scraping strategies in order of preference"""
    FAST_HTML = 1  # requests.get() - fastest
    JS_RENDERING = 2  # Playwright - handles JS
    HARD_MODE = 3  # Anti-blocking - handles protection
    AGGRESSIVE_JS = 4  # Playwright with longer waits - handles slow JS
    AGGRESSIVE_HARD = 5  # Hard mode with more retries - handles strict protection


class AggressiveScraper:
    """
    Aggressive scraper that tries multiple strategies to scrape any website.
    Automatically escalates if one method fails.
    """
    
    def __init__(self, base_scraper):
        """
        Initialize aggressive scraper wrapper
        
        Args:
            base_scraper: WebScraper instance to use
        """
        self.base_scraper = base_scraper
        self.strategy_history = {}  # Track what worked for each domain
    
    def scrape_aggressive(self, url: str) -> 'ScraperResult':
        """
        Scrape URL using aggressive multi-strategy approach.
        Tries multiple methods until one succeeds.
        """
        logger.info(f"Starting aggressive scrape for {url}")
        
        # Get domain for strategy history
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Check if we know what works for this domain
        preferred_strategy = self.strategy_history.get(domain)
        
        # Build strategy list
        strategies = self._build_strategy_list(preferred_strategy)
        
        # Try each strategy
        for strategy in strategies:
            logger.info(f"Trying {strategy.name} for {url}")
            result = self._try_strategy(url, strategy)
            
            # If successful, remember this strategy for this domain
            if result.status == "success" and result.emails or result.phones:
                self.strategy_history[domain] = strategy
                logger.info(f"Success with {strategy.name} for {domain}")
                return result
            
            # If failed, try next strategy
            logger.debug(f"{strategy.name} failed for {url}, trying next strategy")
        
        # All strategies failed
        logger.warning(f"All strategies failed for {url}")
        return result  # Return last result
    
    def _build_strategy_list(self, preferred: Optional[ScrapingStrategy]) -> List[ScrapingStrategy]:
        """Build list of strategies to try, with preferred first"""
        all_strategies = [
            ScrapingStrategy.FAST_HTML,
            ScrapingStrategy.JS_RENDERING,
            ScrapingStrategy.HARD_MODE,
            ScrapingStrategy.AGGRESSIVE_JS,
            ScrapingStrategy.AGGRESSIVE_HARD,
        ]
        
        if preferred and preferred in all_strategies:
            # Put preferred first
            all_strategies.remove(preferred)
            all_strategies.insert(0, preferred)
        
        return all_strategies
    
    def _try_strategy(self, url: str, strategy: ScrapingStrategy) -> 'ScraperResult':
        """Try specific scraping strategy"""
        
        if strategy == ScrapingStrategy.FAST_HTML:
            return self._scrape_fast_html(url)
        elif strategy == ScrapingStrategy.JS_RENDERING:
            return self._scrape_js_rendering(url)
        elif strategy == ScrapingStrategy.HARD_MODE:
            return self._scrape_hard_mode(url)
        elif strategy == ScrapingStrategy.AGGRESSIVE_JS:
            return self._scrape_aggressive_js(url)
        elif strategy == ScrapingStrategy.AGGRESSIVE_HARD:
            return self._scrape_aggressive_hard(url)
        
        return None
    
    def _scrape_fast_html(self, url: str) -> 'ScraperResult':
        """Standard fast HTML scraping"""
        try:
            # Temporarily disable precheck for speed
            original_precheck = self.base_scraper.precheck
            self.base_scraper.precheck = None
            
            result = self.base_scraper.scrape_url(url)
            
            self.base_scraper.precheck = original_precheck
            return result
        except Exception as e:
            logger.debug(f"Fast HTML failed: {str(e)}")
            return None
    
    def _scrape_js_rendering(self, url: str) -> 'ScraperResult':
        """JS rendering with Playwright"""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                try:
                    page.goto(url, wait_until='networkidle', timeout=15000)
                    html = page.content()
                    
                    # Extract using base scraper's extraction methods
                    emails, phones, leadership, pages, social = self.base_scraper._extract_from_html(url, html)
                    
                    from scraper import ScraperResult
                    result = ScraperResult(
                        url=url,
                        status="success" if emails or phones else "no_data",
                        emails=list(emails),
                        phones=list(phones),
                        pages_scanned=pages,
                        leadership_count=leadership,
                        email_list='; '.join(emails),
                        confidence_score=0.75,
                        reason="JS rendering successful",
                        load_time=0.0,
                        ssl_valid=True,
                        bot_protection=None,
                        scrape_mode="js_rendering",
                        fetch_mode="js_rendering",
                        retry_count=0,
                        social_links=str(social),
                        phone_list='; '.join(phones)
                    )
                    browser.close()
                    return result
                except PlaywrightTimeoutError:
                    browser.close()
                    logger.debug(f"JS rendering timeout for {url}")
                    return None
        except Exception as e:
            logger.debug(f"JS rendering failed: {str(e)}")
            return None
    
    def _scrape_hard_mode(self, url: str) -> 'ScraperResult':
        """Hard mode with anti-blocking"""
        try:
            # Use base scraper's hard mode
            result = self.base_scraper.scrape_url(url)
            return result
        except Exception as e:
            logger.debug(f"Hard mode failed: {str(e)}")
            return None
    
    def _scrape_aggressive_js(self, url: str) -> 'ScraperResult':
        """Aggressive JS rendering with longer waits"""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                try:
                    # Longer timeout and wait for all network requests
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for dynamic content
                    time.sleep(2)
                    
                    # Scroll to trigger lazy loading
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    html = page.content()
                    
                    # Extract using base scraper's extraction methods
                    emails, phones, leadership, pages, social = self.base_scraper._extract_from_html(url, html)
                    
                    from scraper import ScraperResult
                    result = ScraperResult(
                        url=url,
                        status="success" if emails or phones else "no_data",
                        emails=list(emails),
                        phones=list(phones),
                        pages_scanned=pages,
                        leadership_count=leadership,
                        email_list='; '.join(emails),
                        confidence_score=0.70,
                        reason="Aggressive JS rendering successful",
                        load_time=0.0,
                        ssl_valid=True,
                        bot_protection=None,
                        scrape_mode="aggressive_js",
                        fetch_mode="aggressive_js",
                        retry_count=0,
                        social_links=str(social),
                        phone_list='; '.join(phones)
                    )
                    browser.close()
                    return result
                except PlaywrightTimeoutError:
                    browser.close()
                    logger.debug(f"Aggressive JS timeout for {url}")
                    return None
        except Exception as e:
            logger.debug(f"Aggressive JS failed: {str(e)}")
            return None
    
    def _scrape_aggressive_hard(self, url: str) -> 'ScraperResult':
        """Aggressive hard mode with more retries and delays"""
        try:
            import requests
            from bs4 import BeautifulSoup
            from scraper import AntiBlockingHeaders, ScraperResult
            
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    headers = AntiBlockingHeaders.get_random_headers()
                    proxy = self.base_scraper.proxy_manager.get_next_proxy()
                    
                    # Longer delay between attempts
                    if attempt > 0:
                        delay = 2 + (attempt * 1.5)
                        logger.debug(f"Aggressive hard mode delay: {delay}s")
                        time.sleep(delay)
                    
                    response = requests.get(
                        url,
                        headers=headers,
                        proxies=proxy,
                        timeout=15,
                        allow_redirects=True,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        # Extract using base scraper's extraction methods
                        emails, phones, leadership, pages, social = self.base_scraper._extract_from_html(url, response.text)
                        
                        result = ScraperResult(
                            url=url,
                            status="success" if emails or phones else "no_data",
                            emails=list(emails),
                            phones=list(phones),
                            pages_scanned=pages,
                            leadership_count=leadership,
                            email_list='; '.join(emails),
                            confidence_score=0.65,
                            reason="Aggressive hard mode successful",
                            load_time=0.0,
                            ssl_valid=True,
                            bot_protection=None,
                            scrape_mode="aggressive_hard",
                            fetch_mode="aggressive_hard",
                            retry_count=attempt,
                            social_links=str(social),
                            phone_list='; '.join(phones)
                        )
                        return result
                    
                    logger.debug(f"Aggressive hard mode attempt {attempt + 1}: HTTP {response.status_code}")
                
                except requests.RequestException as e:
                    logger.debug(f"Aggressive hard mode attempt {attempt + 1} failed: {str(e)}")
                    continue
            
            logger.warning(f"Aggressive hard mode exhausted all retries for {url}")
            return None
        
        except Exception as e:
            logger.debug(f"Aggressive hard mode failed: {str(e)}")
            return None
    
    def get_strategy_stats(self) -> dict:
        """Get statistics on which strategies work best"""
        return {
            'domains_tracked': len(self.strategy_history),
            'strategies_used': {str(s.name): sum(1 for v in self.strategy_history.values() if v == s) 
                               for s in ScrapingStrategy}
        }


def create_aggressive_scraper(base_scraper):
    """Factory function to create aggressive scraper"""
    return AggressiveScraper(base_scraper)
