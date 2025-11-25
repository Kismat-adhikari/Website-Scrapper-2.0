"""
Async Web Scraper - Phase 2 Implementation
Uses aiohttp for non-blocking HTTP requests and parallel multi-page fetching
"""

import asyncio
import logging
from typing import List, Set, Tuple, Dict, Optional
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup

from scraper import (
    ContactExtractor, DataValidator, AntiBlockingHeaders,
    FetchMode, ScraperResult, FailureReason
)
from cache import http_cache

logger = logging.getLogger(__name__)


class AsyncWebScraper:
    """Async version of WebScraper for better performance"""
    
    def __init__(self, proxy_manager=None, timeout: int = 4, max_pages: int = 1):
        self.proxy_manager = proxy_manager
        self.timeout = timeout
        self.max_pages = max_pages
        self.extractor = ContactExtractor()
        self.connector = None  # Will be created in async context
    
    async def scrape_url_async(self, url: str, fast_mode: bool = True) -> ScraperResult:
        """Async scrape a single URL"""
        import time
        start_time = time.time()
        
        # Create connector if not exists (must be done in async context)
        if self.connector is None:
            self.connector = aiohttp.TCPConnector(
                limit=100,              # Max total connections
                limit_per_host=10,      # Max connections per host
                ttl_dns_cache=300       # DNS cache TTL (5 minutes)
            )
        
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        try:
            # Create session for all requests
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout
            ) as session:
                # Fetch HTML (with caching)
                html = await self._fetch_html_async(url, session)
                
                if not html:
                    return self._create_failed_result(url, "Failed to fetch HTML")
                
                # Extract data in parallel
                emails, phones, leadership_count, social_links = await self._extract_all_async(html)
                
                # Skip additional pages for speed - let aggressive mode handle it if needed
                pages_scanned = 1
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(
                emails, phones, leadership_count, pages_scanned
            )
            
            # Format social links
            social_links_str = self._format_social_links(social_links)
            
            # Calculate load time
            load_time = time.time() - start_time
            
            return ScraperResult(
                url=url,
                status="success" if emails or phones else "no_data",
                emails=sorted(list(emails)),
                phones=sorted(list(phones)),
                pages_scanned=pages_scanned,
                leadership_count=leadership_count,
                email_list='; '.join(sorted(list(emails))),
                confidence_score=confidence_score,
                reason="Success",
                load_time=load_time,
                ssl_valid=True,
                bot_protection=None,
                scrape_mode="async",
                fetch_mode="async_http",
                retry_count=0,
                social_links=social_links_str,
                phone_list='; '.join(sorted(list(phones))),
                html=html
            )
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
            return self._create_failed_result(url, str(e))
    
    async def _fetch_html_async(self, url: str, session=None) -> Optional[str]:
        """Fetch HTML using aiohttp with caching"""
        # Check cache first
        cached_html = http_cache.get(url)
        if cached_html:
            logger.debug(f"Cache hit for {url}")
            return cached_html
        
        # Fetch with aiohttp
        headers = AntiBlockingHeaders.get_random_headers()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            # Use provided session or create new one
            if session:
                async with session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Cache the response
                        http_cache.set(url, html, ttl=3600)
                        logger.info(f"Async fetch succeeded for {url}")
                        return html
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
            else:
                # Create temporary session
                async with aiohttp.ClientSession(
                    connector=self.connector,
                    timeout=timeout
                ) as temp_session:
                    async with temp_session.get(url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Cache the response
                            http_cache.set(url, html, ttl=3600)
                            logger.info(f"Async fetch succeeded for {url}")
                            return html
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    async def _extract_all_async(self, html: str) -> Tuple[Set[str], Set[str], int, Dict]:
        """Extract all data in parallel using asyncio"""
        # Run extraction in thread pool (CPU-bound work)
        loop = asyncio.get_event_loop()
        
        # Create tasks for parallel execution
        email_task = loop.run_in_executor(None, self.extractor.extract_emails, html)
        phone_task = loop.run_in_executor(None, self.extractor.extract_phones, html)
        leadership_task = loop.run_in_executor(None, self.extractor.extract_leadership, html)
        social_task = loop.run_in_executor(None, self.extractor.extract_social_links, html)
        
        # Wait for all tasks to complete
        emails, phones, leadership_count, social_links = await asyncio.gather(
            email_task, phone_task, leadership_task, social_task
        )
        
        return emails, phones, leadership_count, social_links
    
    async def _fetch_additional_pages_async(self, base_url: str, html: str, session) -> Optional[Dict]:
        """Discover and fetch additional pages in parallel"""
        # Discover contact/about/team pages
        discovered_urls = self._discover_pages(base_url, html)
        
        if not discovered_urls:
            return None
        
        # Limit to max_pages
        discovered_urls = list(discovered_urls)[:self.max_pages]
        
        # Fetch all pages in parallel using the same session
        tasks = [self._fetch_html_async(url, session) for url in discovered_urls]
        htmls = await asyncio.gather(*tasks)
        
        # Extract from all pages in parallel
        emails = set()
        phones = set()
        leadership_count = 0
        social_links = {}
        pages_scanned = 0
        
        for html in htmls:
            if html:
                e, p, l, s = await self._extract_all_async(html)
                emails.update(e)
                phones.update(p)
                leadership_count += l
                for platform, links in s.items():
                    if platform not in social_links:
                        social_links[platform] = set()
                    social_links[platform].update(links)
                pages_scanned += 1
        
        return {
            'emails': emails,
            'phones': phones,
            'leadership': leadership_count,
            'social': social_links,
            'pages_scanned': pages_scanned
        }
    
    def _discover_pages(self, base_url: str, html: str) -> Set[str]:
        """Discover contact/about/team pages"""
        soup = BeautifulSoup(html, 'html.parser')
        discovered = set()
        
        keywords = ['contact', 'about', 'team', 'support', 'help', 'location']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if any(kw in href for kw in keywords):
                try:
                    full_url = urljoin(base_url, link['href'])
                    # Allow same domain or subdomain
                    from urllib.parse import urlparse
                    base_domain = urlparse(base_url).netloc
                    full_domain = urlparse(full_url).netloc
                    if base_domain in full_domain or full_domain in base_domain:
                        discovered.add(full_url)
                        logger.debug(f"Discovered page: {full_url}")
                except Exception as e:
                    logger.debug(f"Error parsing link: {e}")
                    pass
        
        logger.info(f"Discovered {len(discovered)} additional pages for {base_url}")
        return discovered
    
    def _calculate_confidence(self, emails: Set, phones: Set, leadership: int, pages: int) -> float:
        """Calculate confidence score"""
        score = 0.0
        
        if emails or phones:
            score += 0.15
        
        if len(emails) >= 2:
            score += 0.30
        elif len(emails) == 1:
            score += 0.15
        
        if len(phones) >= 2:
            score += 0.25
        elif len(phones) == 1:
            score += 0.12
        
        if pages >= 2:
            score += 0.15
        elif pages >= 1:
            score += 0.08
        
        score += min(leadership / 5.0, 1.0) * 0.10
        score += 0.10  # Async fetch bonus
        
        return min(score, 1.0)
    
    def _format_social_links(self, social_links: Dict) -> str:
        """Format social links as JSON string"""
        import json
        return json.dumps({k: list(v) for k, v in social_links.items()}) if social_links else ""
    
    def _create_failed_result(self, url: str, reason: str) -> ScraperResult:
        """Create a failed result"""
        return ScraperResult(
            url=url,
            status="failed",
            emails=[],
            phones=[],
            pages_scanned=0,
            leadership_count=0,
            email_list="",
            confidence_score=0.0,
            reason=reason,
            load_time=0.0,
            ssl_valid=False,
            bot_protection=None,
            scrape_mode="async",
            fetch_mode="async_http",
            retry_count=0,
            social_links="",
            phone_list="",
            html=""
        )
    
    async def close(self):
        """Close connector"""
        if self.connector:
            await self.connector.close()


# Helper function to run async scraper from sync code
def scrape_url_async_wrapper(url: str, proxy_manager=None, fast_mode: bool = True) -> ScraperResult:
    """Wrapper to run async scraper from synchronous code (Flask-safe)"""
    scraper = AsyncWebScraper(proxy_manager=proxy_manager)
    
    # Always create a new event loop for Flask threads
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async scraper
        result = loop.run_until_complete(scraper.scrape_url_async(url, fast_mode=fast_mode))
        loop.run_until_complete(scraper.close())
        return result
    except Exception as e:
        logger.error(f"Error in async wrapper for {url}: {str(e)}", exc_info=True)
        # Fallback to sync scraper if async fails
        try:
            from scraper import WebScraper
            sync_scraper = WebScraper(proxy_manager=proxy_manager)
            return sync_scraper.scrape_url(url, fast_mode=fast_mode)
        except Exception as e2:
            logger.error(f"Fallback sync scraper also failed for {url}: {str(e2)}")
            return scraper._create_failed_result(url, f"Async error: {str(e)}, Sync error: {str(e2)}")
    finally:
        # Always close the loop we created
        try:
            loop.close()
        except:
            pass


# Batch scraping with async
async def scrape_urls_batch_async(urls: List[str], proxy_manager=None, fast_mode: bool = True) -> List[ScraperResult]:
    """Scrape multiple URLs in parallel using async"""
    scraper = AsyncWebScraper(proxy_manager=proxy_manager)
    
    # Create tasks for all URLs
    tasks = [scraper.scrape_url_async(url, fast_mode=fast_mode) for url in urls]
    
    # Run all tasks in parallel
    results = await asyncio.gather(*tasks)
    
    # Close connector
    await scraper.close()
    
    return results


def scrape_urls_batch_wrapper(urls: List[str], proxy_manager=None, fast_mode: bool = True) -> List[ScraperResult]:
    """Wrapper to run batch async scraper from synchronous code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(scrape_urls_batch_async(urls, proxy_manager, fast_mode))
    finally:
        loop.close()
