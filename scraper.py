import argparse
import csv
import json
import logging
import random
import re
import ssl
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Set, Tuple, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import cache module
from cache import http_cache

try:
    from advanced_scraper_features import AdvancedScraperPipeline
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

try:
    from aggressive_scraper import create_aggressive_scraper
    AGGRESSIVE_SCRAPER_AVAILABLE = True
except ImportError:
    AGGRESSIVE_SCRAPER_AVAILABLE = False

try:
    from phone_validator import create_validator as create_phone_validator
    PHONE_VALIDATOR_AVAILABLE = True
except ImportError:
    PHONE_VALIDATOR_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create detailed attempt logger for tracking each scraping attempt
attempt_logger = logging.getLogger('attempts')
attempt_handler = logging.FileHandler('scraper_attempts.log')
attempt_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
attempt_logger.addHandler(attempt_handler)
attempt_logger.setLevel(logging.INFO)

# Create failure logger for tracking failed URLs
failure_logger = logging.getLogger('failures')
failure_handler = logging.FileHandler('scraper_failures.log')
failure_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
failure_logger.addHandler(failure_handler)
failure_logger.setLevel(logging.INFO)


class FetchMode(Enum):
    """Fetch modes for different site types"""
    FAST_HTML = "fast_html"  # Standard requests.get
    JS_RENDERING = "js_rendering"  # Playwright headless browser
    HARD_MODE = "hard_mode"  # Anti-blocking techniques


class FailureReason(Enum):
    """Reasons for scraping failure"""
    TIMEOUT = "timeout"  # Request timeout
    BLOCKED = "blocked"  # Access blocked (403/429)
    SSL_ERROR = "ssl_error"  # SSL certificate error
    BOT_DETECTION = "bot_detection"  # Bot protection detected
    NO_CONTACT = "no_contact"  # No contact info found
    NETWORK_ERROR = "network_error"  # Network connectivity issue
    INVALID_URL = "invalid_url"  # Invalid URL format
    UNKNOWN = "unknown"  # Unknown error


class ScrapeMode(Enum):
    """Determines how to scrape based on pre-check results"""
    NORMAL = "normal"  # Standard HTML fetch
    BROWSER = "browser"  # Use headless browser
    SLOW_MODE = "slow_mode"  # Slow site, use browser with longer timeout
    SKIP = "skip"  # Skip due to protection or unreachability


@dataclass
class PreCheckResult:
    """Results from pre-check system"""
    url: str
    is_reachable: bool
    ssl_valid: bool
    bot_protection: Optional[str]  # None, "cloudflare", "403", "429", "captcha"
    load_time: float  # seconds
    is_slow: bool  # True if load_time > 6 seconds
    scrape_mode: ScrapeMode
    check_reason: str  # Explanation for the decision


@dataclass
class ScraperResult:
    url: str
    status: str
    emails: List[str]
    phones: List[str]
    pages_scanned: int
    leadership_count: int
    email_list: str
    confidence_score: float
    reason: str
    load_time: float
    ssl_valid: bool
    bot_protection: Optional[str]
    scrape_mode: str
    fetch_mode: str  # fast_html, js_rendering, hard_mode
    retry_count: int
    social_links: str  # JSON string of social links
    phone_list: str  # Semicolon-separated phones
    html: str = ""  # HTML content for extraction


class PreCheckSystem:
    """Lightweight pre-check system to assess site accessibility and protection"""
    
    CLOUDFLARE_INDICATORS = [
        'cloudflare',
        'cf-ray',
        'cf-cache-status',
        'cf-request-id',
        'ray=',
        'challenge'
    ]
    
    CAPTCHA_INDICATORS = [
        'captcha',
        'recaptcha',
        'hcaptcha',
        'challenge',
        'verify',
        'robot'
    ]
    
    SLOW_THRESHOLD = 6.0  # seconds

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()

    def check_url(self, url: str, proxy_manager: Optional['ProxyManager'] = None) -> PreCheckResult:
        """Run all pre-checks on a URL"""
        logger.info(f"Pre-checking {url}")
        
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        is_reachable = False
        ssl_valid = False
        bot_protection = None
        load_time = 0.0
        check_reason = ""
        scrape_mode = ScrapeMode.SKIP

        # Check SSL validity
        ssl_valid = self._check_ssl(url)
        if not ssl_valid:
            check_reason = "SSL certificate invalid"
            logger.warning(f"{url}: {check_reason}")
            return PreCheckResult(url, False, False, None, 0.0, False, ScrapeMode.SKIP, check_reason)

        # Check reachability and bot protection
        is_reachable, bot_protection, load_time = self._check_reachability(url, proxy_manager)

        if not is_reachable:
            check_reason = f"Site unreachable (bot protection: {bot_protection})"
            logger.warning(f"{url}: {check_reason}")
            return PreCheckResult(url, False, ssl_valid, bot_protection, load_time, False, ScrapeMode.SKIP, check_reason)

        is_slow = load_time > self.SLOW_THRESHOLD

        # Determine scrape mode
        if bot_protection:
            if bot_protection == "captcha":
                scrape_mode = ScrapeMode.BROWSER
                check_reason = "CAPTCHA detected, using browser mode"
            elif bot_protection == "cloudflare":
                scrape_mode = ScrapeMode.BROWSER
                check_reason = "Cloudflare detected, using browser mode"
            elif bot_protection in ["403", "429"]:
                scrape_mode = ScrapeMode.SKIP
                check_reason = f"HTTP {bot_protection} - access denied"
            else:
                scrape_mode = ScrapeMode.BROWSER
                check_reason = f"Bot protection detected ({bot_protection}), using browser mode"
        elif is_slow:
            scrape_mode = ScrapeMode.SLOW_MODE
            check_reason = f"Slow site ({load_time:.2f}s), using browser mode with extended timeout"
        else:
            scrape_mode = ScrapeMode.NORMAL
            check_reason = "Site accessible, using normal HTML fetch"

        logger.info(f"{url}: {check_reason} (load_time: {load_time:.2f}s)")
        return PreCheckResult(url, is_reachable, ssl_valid, bot_protection, load_time, is_slow, scrape_mode, check_reason)

    def _check_ssl(self, url: str) -> bool:
        """Verify SSL certificate validity"""
        try:
            parsed = urlparse(url)
            if parsed.scheme != 'https':
                return True  # HTTP doesn't have SSL
            
            context = ssl.create_default_context()
            with context.wrap_socket(
                __import__('socket').socket(),
                server_hostname=parsed.netloc
            ) as sock:
                sock.connect((parsed.netloc, 443))
            return True
        except (ssl.SSLError, ssl.CertificateError) as e:
            logger.debug(f"SSL check failed for {url}: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"SSL check error for {url}: {str(e)}")
            return True  # Assume valid if we can't verify

    def _check_reachability(self, url: str, proxy_manager: Optional['ProxyManager'] = None) -> Tuple[bool, Optional[str], float]:
        """Check if site is reachable and detect bot protection"""
        headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
        ]

        for headers in headers_list:
            try:
                start_time = time.time()
                proxy = proxy_manager.get_next_proxy() if proxy_manager else None
                
                response = self.session.head(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=False
                )
                
                load_time = time.time() - start_time

                # Check for bot protection indicators
                bot_protection = self._detect_bot_protection(response)

                if response.status_code == 403:
                    return False, "403", load_time
                elif response.status_code == 429:
                    return False, "429", load_time
                elif response.status_code == 200:
                    if bot_protection:
                        return True, bot_protection, load_time
                    return True, None, load_time
                elif response.status_code in [301, 302, 303, 307, 308]:
                    # Redirect - try to follow
                    return True, bot_protection, load_time
                else:
                    logger.debug(f"{url}: HTTP {response.status_code}")
                    return False, str(response.status_code), load_time

            except requests.Timeout:
                logger.debug(f"Timeout checking {url}")
                return False, "timeout", self.timeout
            except requests.RequestException as e:
                logger.debug(f"Request error for {url}: {str(e)}")
                time.sleep(0.5)

        return False, "unreachable", 0.0

    def _detect_bot_protection(self, response: requests.Response) -> Optional[str]:
        """Detect bot protection mechanisms"""
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        content = response.text.lower() if response.text else ""

        # Check for Cloudflare
        for indicator in self.CLOUDFLARE_INDICATORS:
            if indicator in headers or indicator in content:
                return "cloudflare"

        # Check for CAPTCHA
        for indicator in self.CAPTCHA_INDICATORS:
            if indicator in content:
                return "captcha"

        # Check for common bot protection headers
        if 'x-frame-options' in headers and headers['x-frame-options'] == 'deny':
            if 'x-content-type-options' in headers:
                return "protection"

        return None


class FetchModeSelector:
    """Intelligent fetch mode selection based on pre-check and failure history"""
    
    def __init__(self):
        self.failure_history: Dict[str, List[str]] = {}  # url -> list of failed modes
    
    def select_mode(self, url: str, precheck_result: PreCheckResult) -> FetchMode:
        """Select optimal fetch mode based on pre-check and history"""
        failed_modes = self.failure_history.get(url, [])
        
        # If no failures, use mode based on pre-check
        if not failed_modes:
            if precheck_result.bot_protection or precheck_result.is_slow:
                return FetchMode.JS_RENDERING
            return FetchMode.FAST_HTML
        
        # If fast HTML failed, try JS rendering
        if FetchMode.FAST_HTML.value in failed_modes and FetchMode.JS_RENDERING.value not in failed_modes:
            return FetchMode.JS_RENDERING
        
        # If JS rendering failed, use hard mode
        if FetchMode.JS_RENDERING.value in failed_modes and FetchMode.HARD_MODE.value not in failed_modes:
            return FetchMode.HARD_MODE
        
        # All modes failed, try hard mode again
        return FetchMode.HARD_MODE
    
    def record_failure(self, url: str, mode: FetchMode):
        """Record a failed fetch mode for a URL"""
        if url not in self.failure_history:
            self.failure_history[url] = []
        if mode.value not in self.failure_history[url]:
            self.failure_history[url].append(mode.value)
            logger.debug(f"Recorded failure for {url} in {mode.value} mode")


class RetryStrategy:
    """Manages retry logic and failure tracking"""
    
    def __init__(self, max_retries: int = 5, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.failure_history: Dict[str, List[Tuple[str, str]]] = {}  # url -> [(mode, reason)]
        self.problematic_sites: Set[str] = set()  # Sites that need reduced concurrency

    def record_failure(self, url: str, mode: str, reason: FailureReason):
        """Record a failure for a URL"""
        if url not in self.failure_history:
            self.failure_history[url] = []
        self.failure_history[url].append((mode, reason.value))
        
        # Mark as problematic if multiple failures
        if len(self.failure_history[url]) >= 2:
            self.problematic_sites.add(url)
            logger.warning(f"Marked {url} as problematic (failures: {len(self.failure_history[url])})")

    def get_failure_count(self, url: str) -> int:
        """Get number of failures for a URL"""
        return len(self.failure_history.get(url, []))

    def get_failure_reasons(self, url: str) -> List[str]:
        """Get all failure reasons for a URL"""
        return [reason for _, reason in self.failure_history.get(url, [])]

    def is_problematic(self, url: str) -> bool:
        """Check if URL is marked as problematic"""
        return url in self.problematic_sites

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt (exponential backoff)"""
        return min(self.backoff_factor ** attempt, 30.0)  # Cap at 30 seconds

    def should_retry(self, url: str) -> bool:
        """Check if URL should be retried"""
        return self.get_failure_count(url) < self.max_retries

    def get_last_failure_reason(self, url: str) -> Optional[str]:
        """Get the last failure reason for a URL"""
        reasons = self.get_failure_reasons(url)
        return reasons[-1] if reasons else None


class ProxyManager:
    """Thread-safe proxy manager with rotation support"""
    
    # Rotate to next proxy every 14 requests (helps avoid detection)
    ROTATION_INTERVAL = 14
    
    def __init__(self, proxy_file: Optional[str] = None):
        self.proxies = []
        self.current_index = 0
        self.request_count = 0  # Track requests for periodic rotation
        self.lock = threading.Lock()  # Thread-safe lock for proxy rotation
        if proxy_file:
            self.load_proxies(proxy_file)

    def load_proxies(self, proxy_file: str):
        """Load proxies from file"""
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.proxies.append(line)
            logger.info(f"Loaded {len(self.proxies)} proxies")
        except FileNotFoundError:
            logger.warning(f"Proxy file {proxy_file} not found")

    def get_next_proxy(self) -> Optional[dict]:
        """Get next proxy in rotation with periodic rotation every 14 requests (thread-safe)"""
        if not self.proxies:
            return None
        
        with self.lock:
            # Rotate to next proxy every 14 requests (regardless of success/failure)
            if self.request_count > 0 and self.request_count % self.ROTATION_INTERVAL == 0:
                self.current_index += 1
                logger.debug(f"Periodic proxy rotation at request {self.request_count}: switching to proxy {self.current_index % len(self.proxies)}")
            
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.request_count += 1
        
        return self._parse_proxy(proxy)

    def get_random_proxy(self) -> Optional[dict]:
        """Get random proxy (thread-safe)"""
        if not self.proxies:
            return None
        
        with self.lock:
            self.request_count += 1
        
        proxy = random.choice(self.proxies)
        return self._parse_proxy(proxy)

    def get_request_count(self) -> int:
        """Get total request count (thread-safe)"""
        with self.lock:
            return self.request_count

    def reset_request_count(self):
        """Reset request counter (thread-safe)"""
        with self.lock:
            self.request_count = 0

    @staticmethod
    def _parse_proxy(proxy_str: str) -> dict:
        """Parse proxy string to dict format"""
        parts = proxy_str.split(':')
        if len(parts) == 2:
            return {'http': f'http://{proxy_str}', 'https': f'http://{proxy_str}'}
        elif len(parts) == 4:
            ip, port, user, password = parts
            proxy_url = f'http://{user}:{password}@{ip}:{port}'
            return {'http': proxy_url, 'https': proxy_url}
        return {}


class AntiBlockingHeaders:
    """Rotating headers and techniques to avoid blocking"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    @staticmethod
    def get_random_headers() -> Dict[str, str]:
        """Get randomized headers to avoid detection"""
        return {
            'User-Agent': random.choice(AntiBlockingHeaders.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }


class PageDiscovery:
    """Intelligent page discovery with keyword matching and deduplication"""
    
    # Contact page keywords
    CONTACT_KEYWORDS = [
        'contact', 'support', 'help', 'reach', 'get-in-touch', 'hello', 'talk',
        'contact-us', 'contact_us', 'contactus', 'get-in-touch', 'getintouch',
        'inquiry', 'inquiries', 'message', 'email-us', 'call-us'
    ]
    
    # Team/Leadership page keywords
    TEAM_KEYWORDS = [
        'team', 'about', 'people', 'leadership', 'executives', 'management', 'founders',
        'about-us', 'about_us', 'aboutus', 'our-team', 'our_team', 'ourteam',
        'staff', 'employees', 'team-members', 'leadership-team', 'executive-team',
        'meet-the-team', 'our-people', 'company'
    ]
    
    # Exclude patterns (to avoid false positives)
    EXCLUDE_PATTERNS = [
        r'\.pdf$', r'\.jpg$', r'\.png$', r'\.gif$', r'\.zip$',
        r'javascript:', r'mailto:', r'tel:', r'#',
        r'/search', r'/results', r'/404', r'/error',
        r'/admin', r'/login', r'/register', r'/account'
    ]
    
    # Maximum discovery depth
    MAX_DISCOVERY_DEPTH = 2
    
    def __init__(self, max_pages: int = 10):
        self.max_pages = max_pages
        self.discovered_urls: Set[str] = set()
        self.url_cache: Dict[str, Set[str]] = {}

    def discover_pages(self, base_url: str, html: str, page_type: str = 'all') -> Set[str]:
        """
        Discover relevant pages from HTML
        
        Args:
            base_url: Base URL to resolve relative links
            html: HTML content to parse
            page_type: 'contact', 'team', or 'all'
        
        Returns:
            Set of discovered URLs
        """
        if base_url in self.url_cache:
            return self.url_cache[base_url]
        
        discovered = set()
        soup = BeautifulSoup(html, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            
            # Skip invalid links
            if not href or self._should_exclude(href):
                continue
            
            # Resolve relative URLs
            try:
                full_url = urljoin(base_url, href)
            except Exception:
                continue
            
            # Verify same domain
            if not self._is_same_domain(base_url, full_url):
                continue
            
            # Normalize URL (remove fragments, query params)
            normalized_url = self._normalize_url(full_url)
            
            # Check if URL matches page type
            if self._matches_page_type(normalized_url, page_type):
                discovered.add(normalized_url)
        
        # Deduplicate and limit
        discovered = self._deduplicate_urls(discovered)
        discovered = discovered - self.discovered_urls  # Remove already discovered
        self.discovered_urls.update(discovered)
        
        # Limit to max pages
        discovered = set(list(discovered)[:self.max_pages])
        
        self.url_cache[base_url] = discovered
        logger.debug(f"Discovered {len(discovered)} pages from {base_url}")
        
        return discovered

    def discover_all_pages(self, base_url: str, html: str) -> Tuple[Set[str], Set[str]]:
        """
        Discover both contact and team pages
        
        Returns:
            Tuple of (contact_urls, team_urls)
        """
        contact_urls = self.discover_pages(base_url, html, 'contact')
        team_urls = self.discover_pages(base_url, html, 'team')
        return contact_urls, team_urls

    @staticmethod
    def _should_exclude(href: str) -> bool:
        """Check if URL should be excluded"""
        href_lower = href.lower()
        
        for pattern in PageDiscovery.EXCLUDE_PATTERNS:
            if re.search(pattern, href_lower):
                return True
        
        return False

    @staticmethod
    def _is_same_domain(base_url: str, full_url: str) -> bool:
        """Verify URLs are on same domain"""
        try:
            base_domain = urlparse(base_url).netloc
            full_domain = urlparse(full_url).netloc
            return base_domain == full_domain
        except Exception:
            return False

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for deduplication"""
        parsed = urlparse(url)
        # Remove fragment and normalize query params
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash for consistency
        if normalized.endswith('/') and len(normalized) > len(f"{parsed.scheme}://{parsed.netloc}"):
            normalized = normalized.rstrip('/')
        return normalized

    @staticmethod
    def _deduplicate_urls(urls: Set[str]) -> Set[str]:
        """Remove duplicate URLs with different cases/formats"""
        deduplicated = set()
        seen_normalized = set()
        
        for url in urls:
            normalized = PageDiscovery._normalize_url(url).lower()
            if normalized not in seen_normalized:
                deduplicated.add(url)
                seen_normalized.add(normalized)
        
        return deduplicated

    @staticmethod
    def _matches_page_type(url: str, page_type: str) -> bool:
        """Check if URL matches the specified page type"""
        url_lower = url.lower()
        
        if page_type in ['contact', 'all']:
            for keyword in PageDiscovery.CONTACT_KEYWORDS:
                if keyword in url_lower:
                    return True
        
        if page_type in ['team', 'all']:
            for keyword in PageDiscovery.TEAM_KEYWORDS:
                if keyword in url_lower:
                    return True
        
        return False


class DataValidator:
    """Validate extracted data to ensure it's real and not fake"""
    
    # Common fake/test emails and system emails
    FAKE_EMAILS = {
        'test@', 'fake@', 'demo@', 'example@', 'sample@',
        'noreply@', 'no-reply@', 'donotreply@', 'notification@',
        'automated@', 'mailer-daemon@', 'postmaster@',
        'admin@localhost', 'root@localhost', 'test@test',
        'user@test', 'admin@admin', 'info@info',
        'user@domain', 'test@domain', 'admin@example', 'info@example',
        'contact@example', 'support@example', 'hello@example',
        'placeholder@', 'dummy@', 'temp@', 'temporary@',
        '@example.com', '@example.org', '@test.com', '@test.org',
        '@domain.com', '@localhost', '@sample.com', '@demo.com',
        # System/tracking emails
        '@sentry.io', '@sentry.wixpress.com', '@sentry-next.wixpress.com',
        '@wixpress.com', '@segment.com', '@mixpanel.com', '@amplitude.com',
        '@bugsnag.com', '@rollbar.com', '@raygun.com', '@airbrake.io'
    }
    
    # Common fake/test phone patterns (be specific to avoid false positives)
    FAKE_PHONES = {
        '555-0100', '555-0199',  # Reserved fictional numbers
        '000-000-0000', '111-111-1111', '222-222-2222', '333-333-3333',
        '444-444-4444', '666-666-6666', '777-777-7777', '888-888-8888', '999-999-9999',
        '123-456-7890', '111-111', '000-000'
    }
    
    # Valid domain TLDs (basic check) - expanded list
    VALID_TLDS = {
        'com', 'org', 'net', 'edu', 'gov', 'mil', 'co', 'uk', 'de', 'fr', 'it', 'es',
        'ca', 'au', 'jp', 'cn', 'in', 'br', 'ru', 'io', 'app', 'dev', 'info', 'biz',
        'us', 'tv', 'cc', 'ws', 'name', 'pro', 'mobi', 'asia', 'tel', 'travel',
        # Modern/city TLDs
        'miami', 'nyc', 'london', 'tokyo', 'paris', 'berlin', 'sydney', 'la',
        # New generic TLDs
        'tech', 'store', 'online', 'site', 'website', 'space', 'club', 'xyz',
        'top', 'shop', 'live', 'today', 'world', 'email', 'digital', 'studio',
        'agency', 'company', 'solutions', 'services', 'group', 'center', 'cafe',
        'restaurant', 'bar', 'pizza', 'coffee', 'kitchen', 'menu', 'food'
    }

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email is real, not fake"""
        email_lower = email.lower()
        
        # Check against fake patterns
        for fake in DataValidator.FAKE_EMAILS:
            if fake in email_lower:
                return False
        
        # Check for hash-like emails (e.g., 605a7baede844d278b89dc95ae0a9123@sentry.io)
        if '@' in email:
            local_part = email.split('@')[0]
            # If local part is 32+ chars and all hex (likely a hash/ID)
            if len(local_part) >= 32 and all(c in '0123456789abcdefABCDEF' for c in local_part):
                return False
        
        # Check domain has valid TLD
        if '@' in email:
            domain = email.split('@')[1]
            tld = domain.split('.')[-1].lower()
            if tld not in DataValidator.VALID_TLDS:
                return False
        
        # Check for suspicious patterns
        if email.count('@') != 1:
            return False
        if '..' in email:
            return False
        if email.startswith('.') or email.endswith('.'):
            return False
        
        return True

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone is real, not fake"""
        # Remove non-digits for checking
        digits = re.sub(r'\D', '', phone)
        
        # Minimum 10 digits for valid phone (US standard)
        if len(digits) < 10:
            return False
        
        # Maximum 15 digits (international standard)
        if len(digits) > 15:
            return False
        
        # For US numbers (10 digits), validate area code
        if len(digits) == 10:
            area_code = digits[:3]
            # Invalid US area codes
            if area_code[0] in ('0', '1'):  # Area codes can't start with 0 or 1
                return False
        
        # Check against fake patterns
        for fake in DataValidator.FAKE_PHONES:
            if fake in phone:
                return False
        
        # Check for repeating digits (fake pattern)
        if len(set(digits)) == 1:  # All same digit
            return False
        
        # Check for sequential digits (123456789, 987654321)
        if digits in '0123456789' or digits in '9876543210':
            return False
        
        # Check for too many repeating digits (e.g., 1111111111)
        for digit in '0123456789':
            if digit * 7 in digits:  # 7 or more of same digit
                return False
        
        return True

    @staticmethod
    def validate_emails(emails: Set[str]) -> Set[str]:
        """Filter emails to only valid ones"""
        return {e for e in emails if DataValidator.is_valid_email(e)}

    @staticmethod
    def validate_phones(phones: Set[str]) -> Set[str]:
        """Filter phones to only valid ones"""
        return {p for p in phones if DataValidator.is_valid_phone(p)}


class ContactExtractor:
    """Extract contact information from HTML"""
    
    # Pre-compiled regex patterns (compiled once at module load)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    US_PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b')
    INTL_PHONE_PATTERN = re.compile(r'\+[0-9]{1,3}[-.\s]?(?:\(?[0-9]{2,4}\)?[-.\s]?)?[0-9]{3,4}[-.\s]?[0-9]{3,4}(?:[-.\s]?[0-9]{1,4})?')
    
    # Expanded leadership keywords
    LEADERSHIP_KEYWORDS = [
        'ceo', 'cto', 'cmo', 'coo', 'cfo', 'cro',
        'founder', 'co-founder', 'cofounder',
        'president', 'vice president', 'vp',
        'director', 'executive director',
        'manager', 'general manager',
        'lead', 'head', 'chief',
        'partner', 'principal'
    ]
    
    # Pre-compiled leadership patterns
    LEADERSHIP_PATTERNS = {kw: re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in LEADERSHIP_KEYWORDS}
    
    # Social media patterns (pre-compiled)
    SOCIAL_PATTERNS = {
        'linkedin': re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in|profile)?/?[\w-]+', re.IGNORECASE),
        'twitter': re.compile(r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/[\w]+', re.IGNORECASE),
        'facebook': re.compile(r'(?:https?://)?(?:www\.)?facebook\.com/[\w.-]+', re.IGNORECASE),
        'instagram': re.compile(r'(?:https?://)?(?:www\.)?instagram\.com/[\w.]+', re.IGNORECASE),
        'github': re.compile(r'(?:https?://)?(?:www\.)?github\.com/[\w-]+', re.IGNORECASE),
        'youtube': re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/(?:c|channel|user|@)?[\w-]+', re.IGNORECASE),
        'tiktok': re.compile(r'(?:https?://)?(?:www\.)?tiktok\.com/@[\w.-]+', re.IGNORECASE),
    }
    
    # No-reply email patterns (pre-compiled)
    NO_REPLY_PATTERNS = [
        re.compile(r'noreply', re.IGNORECASE),
        re.compile(r'no-reply', re.IGNORECASE),
        re.compile(r'do-not-reply', re.IGNORECASE),
        re.compile(r'donotreply', re.IGNORECASE),
        re.compile(r'no_reply', re.IGNORECASE),
        re.compile(r'notification', re.IGNORECASE),
        re.compile(r'notifications', re.IGNORECASE),
        re.compile(r'automated', re.IGNORECASE),
        re.compile(r'auto-reply', re.IGNORECASE),
        re.compile(r'autoreply', re.IGNORECASE),
        re.compile(r'mailer-daemon', re.IGNORECASE),
        re.compile(r'postmaster', re.IGNORECASE)
    ]

    @staticmethod
    def extract_emails(text: str) -> Set[str]:
        """Extract emails, filtering out no-reply and fake addresses"""
        # Use pre-compiled pattern
        emails = set(ContactExtractor.EMAIL_PATTERN.findall(text))
        
        # Filter out invalid formats and no-reply addresses
        filtered_emails = set()
        for email in emails:
            # Skip file extensions
            if email.endswith(('.png', '.jpg', '.gif', '.pdf')):
                continue
            
            # Validate email is real (not fake/test)
            if not DataValidator.is_valid_email(email):
                continue
            
            filtered_emails.add(email)
        
        return filtered_emails

    @staticmethod
    def extract_phones(text: str) -> Set[str]:
        """Extract and normalize phone numbers (minimum 10 digits), filtering fake ones"""
        phones = set()
        
        # US format: Use pre-compiled pattern
        us_matches = ContactExtractor.US_PHONE_PATTERN.findall(text)
        for match in us_matches:
            phone = f"{match[0]}-{match[1]}-{match[2]}"
            # Validate before adding
            if DataValidator.is_valid_phone(phone):
                phones.add(phone)
            else:
                # Debug: log rejected phones
                import logging
                logging.debug(f"Rejected phone (US): {phone}")
        
        # International format: Use pre-compiled pattern
        intl_matches = ContactExtractor.INTL_PHONE_PATTERN.findall(text)
        for phone in intl_matches:
            # Extract only digits
            digits = re.sub(r'\D', '', phone)
            # Only include if 10-15 digits (reasonable phone length)
            if 10 <= len(digits) <= 15:
                # Validate before adding
                if DataValidator.is_valid_phone(phone):
                    phones.add(phone)
        
        # Additional filtering: Remove phones that look like dates, prices, etc.
        filtered_phones = set()
        for phone in phones:
            digits = re.sub(r'\D', '', phone)
            
            # CRITICAL: Final check - must have at least 10 digits
            if len(digits) < 10:
                continue
            
            # Skip if looks like a year (19xx, 20xx)
            if digits.startswith('19') or digits.startswith('20'):
                if len(digits) == 4:
                    continue
            
            # Skip if looks like a price (ends with 00, 99, etc.)
            if len(digits) <= 6 and digits.endswith(('00', '99', '50')):
                continue
            
            # Skip if all digits are the same or sequential
            if len(set(digits)) <= 2:
                continue
            
            # Final validation check
            if not DataValidator.is_valid_phone(phone):
                continue
            
            filtered_phones.add(phone)
        
        return filtered_phones

    @staticmethod
    def extract_leadership(html: str) -> int:
        """Count leadership mentions with expanded keywords"""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        count = 0
        
        # Use pre-compiled patterns
        for keyword, pattern in ContactExtractor.LEADERSHIP_PATTERNS.items():
            matches = pattern.findall(text)
            count += len(matches)
        
        # Normalize to reasonable range
        return min(count, 50)

    @staticmethod
    def extract_social_links(html: str) -> Dict[str, Set[str]]:
        """Extract social media links"""
        social_links = {platform: set() for platform in ContactExtractor.SOCIAL_PATTERNS.keys()}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract from links (use pre-compiled patterns)
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            for platform, pattern in ContactExtractor.SOCIAL_PATTERNS.items():
                if pattern.search(href):
                    social_links[platform].add(link['href'])
        
        # Extract from text (use pre-compiled patterns)
        text = soup.get_text()
        for platform, pattern in ContactExtractor.SOCIAL_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches:
                social_links[platform].add(match)
        
        # Remove empty platforms
        return {k: v for k, v in social_links.items() if v}


class WebScraper:
    def __init__(self, proxy_manager: ProxyManager, timeout: int = 10, enable_precheck: bool = True, hard_mode_delay: float = 0.5, max_pages_per_site: int = 10, enable_email_validation: bool = True):
        self.proxy_manager = proxy_manager
        self.timeout = timeout
        self.session = requests.Session()
        self.extractor = ContactExtractor()
        self.page_discovery = PageDiscovery(max_pages=max_pages_per_site)
        self.precheck = PreCheckSystem(timeout=3) if enable_precheck else None  # Reduced timeout for speed
        self.mode_selector = FetchModeSelector()
        self.retry_strategy = RetryStrategy(max_retries=5)
        self.hard_mode_delay = hard_mode_delay  # Delay between requests in hard mode
        
        # Initialize email validator if available
        self.email_validator = None
        if enable_email_validation:
            try:
                from email_validator import create_validator
                self.email_validator = create_validator(enable_smtp=True, enable_role_detection=True)
                logger.info("Email validator initialized with SMTP verification")
            except ImportError:
                logger.warning("Email validator not available")

    def _detect_failure_reason(self, error: Exception, response_code: Optional[int] = None) -> FailureReason:
        """Detect the reason for failure from exception or response code"""
        error_str = str(error).lower()
        
        # Check response codes
        if response_code == 403 or response_code == 429:
            return FailureReason.BLOCKED
        
        # Check error types
        if isinstance(error, TimeoutException) or 'timeout' in error_str:
            return FailureReason.TIMEOUT
        elif isinstance(error, ssl.SSLError) or 'ssl' in error_str or 'certificate' in error_str:
            return FailureReason.SSL_ERROR
        elif 'cloudflare' in error_str or 'captcha' in error_str or 'bot' in error_str:
            return FailureReason.BOT_DETECTION
        elif 'connection' in error_str or 'network' in error_str or 'refused' in error_str:
            return FailureReason.NETWORK_ERROR
        elif 'invalid' in error_str or 'malformed' in error_str:
            return FailureReason.INVALID_URL
        
        return FailureReason.UNKNOWN

    def scrape_url(self, url: str, auto_aggressive: bool = True, fast_mode: bool = False) -> ScraperResult:
        """
        Scrape URL with optional auto-aggressive mode detection
        
        Args:
            url: URL to scrape
            auto_aggressive: If True, automatically escalate to aggressive strategies if normal fails
            fast_mode: If True, skip fallback modes and return quickly with FAST_HTML only
        """
        # Set fast_mode for this scrape
        self.fast_mode = fast_mode
        
        logger.info(f"Starting scrape for {url} (auto_aggressive: {auto_aggressive})")
        
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        emails = set()
        phones = set()
        pages_scanned = 0
        leadership_count = 0
        confidence_score = 0.0
        reason = "Success"
        status = "failed"
        load_time = 0.0
        ssl_valid = True
        bot_protection = None
        scrape_mode = ScrapeMode.NORMAL.value
        fetch_mode = FetchMode.FAST_HTML.value
        retry_count = 0
        used_aggressive = False

        try:
            precheck_result = None
            
            # Run pre-check if enabled
            if self.precheck:
                precheck_result = self.precheck.check_url(url, self.proxy_manager)
                load_time = precheck_result.load_time
                ssl_valid = precheck_result.ssl_valid
                bot_protection = precheck_result.bot_protection
                scrape_mode = precheck_result.scrape_mode.value
                reason = precheck_result.check_reason

                # Skip if pre-check indicates to skip
                if precheck_result.scrape_mode == ScrapeMode.SKIP:
                    logger.warning(f"Skipping {url}: {reason}")
                    return ScraperResult(
                        url=url,
                        status="skipped",
                        emails=[],
                        phones=[],
                        pages_scanned=0,
                        leadership_count=0,
                        email_list="",
                        confidence_score=0.0,
                        reason=reason,
                        load_time=load_time,
                        ssl_valid=ssl_valid,
                        bot_protection=bot_protection,
                        scrape_mode=scrape_mode,
                        fetch_mode=fetch_mode,
                        retry_count=retry_count,
                        social_links="",
                        phone_list="",
                        html=""
                    )

            # Select fetch mode based on pre-check and history
            if precheck_result:
                selected_mode = self.mode_selector.select_mode(url, precheck_result)
            else:
                selected_mode = FetchMode.FAST_HTML

            # Try fetch modes in sequence with retry logic
            html = None
            success = False
            last_failure_reason = FailureReason.UNKNOWN
            
            # Try selected mode first
            html, success, fetch_mode, retries, failure_reason = self._fetch_with_mode_and_retry(url, selected_mode)
            retry_count = retries
            
            if not success:
                last_failure_reason = failure_reason
                self.mode_selector.record_failure(url, selected_mode)
                self.retry_strategy.record_failure(url, selected_mode, failure_reason)
                
                # Fallback to JS Rendering if Fast HTML failed
                if selected_mode == FetchMode.FAST_HTML:
                    logger.info(f"Fast HTML failed for {url}, trying JS rendering")
                    html, success, fetch_mode, retries, failure_reason = self._fetch_with_mode_and_retry(url, FetchMode.JS_RENDERING)
                    retry_count += retries
                    if not success:
                        last_failure_reason = failure_reason
                        self.retry_strategy.record_failure(url, FetchMode.JS_RENDERING.value, failure_reason)
                
                # Fallback to Hard Mode if JS Rendering failed
                if not success and selected_mode != FetchMode.HARD_MODE:
                    self.mode_selector.record_failure(url, FetchMode.JS_RENDERING if selected_mode == FetchMode.FAST_HTML else selected_mode)
                    logger.info(f"JS rendering failed for {url}, trying hard mode")
                    html, success, fetch_mode, retries, failure_reason = self._fetch_with_mode_and_retry(url, FetchMode.HARD_MODE)
                    retry_count += retries
                    if not success:
                        last_failure_reason = failure_reason
                        self.retry_strategy.record_failure(url, FetchMode.HARD_MODE.value, failure_reason)
                
                # Auto-escalate to aggressive mode if enabled and still failing
                if not success and auto_aggressive:
                    logger.info(f"All standard modes failed for {url}, auto-escalating to aggressive scraper")
                    used_aggressive = True
                    try:
                        from aggressive_scraper import create_aggressive_scraper
                        aggressive_scraper = create_aggressive_scraper(self)
                        aggressive_result = aggressive_scraper.scrape_aggressive(url)
                        if aggressive_result and aggressive_result.status == "success":
                            return aggressive_result
                    except Exception as e:
                        logger.debug(f"Aggressive scraper failed: {str(e)}")

            if success and html:
                emails, phones, leadership_count, pages_scanned, social_links = self._extract_from_html(url, html)
                status = "success"
                reason = "Success"
                
                # Determine fetch method score (1=Fast HTML, 2=JS Rendering, 3=Hard Mode)
                fetch_method_score = 1 if fetch_mode == FetchMode.FAST_HTML.value else (2 if fetch_mode == FetchMode.JS_RENDERING.value else 3)
                confidence_score = self._calculate_confidence(emails, phones, leadership_count, pages_scanned, fetch_method_score, retry_count)
            else:
                # Mark as problematic if multiple failures
                if self.retry_strategy.get_failure_count(url) >= 2:
                    logger.warning(f"Marked {url} as problematic after {retry_count} retries")
                
                reason = f"All fetch modes failed: {last_failure_reason.value} (retries: {retry_count})"
                social_links = {}

        except Exception as e:
            reason = f"Exception: {str(e)}"
            logger.error(f"Error scraping {url}: {reason}")
            social_links = {}

        # Format social links as JSON string
        social_links_str = json.dumps({k: list(v) for k, v in social_links.items()}) if social_links else ""
        if social_links_str:
            logger.info(f"Found social links: {social_links_str}")
        
        # Format phone list
        phone_list_str = '; '.join(sorted(list(phones)))

        # Log detailed attempt information
        attempt_log = (
            f"URL: {url} | "
            f"Status: {status} | "
            f"Mode: {fetch_mode} | "
            f"Retries: {retry_count} | "
            f"Pages: {pages_scanned} | "
            f"Emails: {len(emails)} | "
            f"Phones: {len(phones)} | "
            f"Confidence: {confidence_score:.2f} | "
            f"LoadTime: {load_time:.2f}s | "
            f"Reason: {reason}"
        )
        attempt_logger.info(attempt_log)

        # Log failures separately for analysis
        if status == "failed":
            failure_log = (
                f"URL: {url} | "
                f"Reason: {reason} | "
                f"Mode: {fetch_mode} | "
                f"Retries: {retry_count} | "
                f"BotProtection: {bot_protection} | "
                f"SSLValid: {ssl_valid}"
            )
            failure_logger.info(failure_log)

        # Validate phones to filter out junk numbers
        if PHONE_VALIDATOR_AVAILABLE and phones:
            try:
                phone_validator = create_phone_validator(default_country='US', enable_library_check=False)
                validated_results, _ = phone_validator.validate_phones(list(phones), url)
                phones = {r.normalized_phone for r in validated_results if r.is_valid}
                logger.debug(f"Phone validation: {len(list(phones))} valid phones out of {len(list(phones))}")
            except Exception as e:
                logger.debug(f"Phone validation error: {str(e)}")
        
        return ScraperResult(
            url=url,
            status=status,
            emails=sorted(list(emails)),
            phones=sorted(list(phones)),
            pages_scanned=pages_scanned,
            leadership_count=leadership_count,
            email_list='; '.join(sorted(list(emails))),
            confidence_score=confidence_score,
            reason=reason,
            load_time=load_time,
            ssl_valid=ssl_valid,
            bot_protection=bot_protection,
            scrape_mode=scrape_mode,
            fetch_mode=fetch_mode,
            retry_count=retry_count,
            social_links=social_links_str,
            phone_list='; '.join(sorted(list(phones))),
            html=html if html else ""
        )

    def _fetch_with_mode_and_retry(self, url: str, mode: FetchMode) -> Tuple[Optional[str], bool, str, int, FailureReason]:
        """Fetch with retry logic, returns (html, success, mode_used, retry_count, failure_reason)"""
        html = None
        success = False
        total_retries = 0
        failure_reason = FailureReason.UNKNOWN
        
        # Determine max retries based on mode (reduced for speed)
        max_attempts = 2 if mode == FetchMode.FAST_HTML else (1 if mode == FetchMode.JS_RENDERING else 1)
        
        for attempt in range(max_attempts):
            try:
                if mode == FetchMode.FAST_HTML:
                    html, success, retries = self._fetch_fast_html(url)
                elif mode == FetchMode.JS_RENDERING:
                    html, success, retries = self._fetch_js_rendering(url)
                elif mode == FetchMode.HARD_MODE:
                    html, success, retries = self._fetch_hard_mode(url)
                else:
                    html, success, retries = None, False, 0
                
                total_retries += retries
                
                if success:
                    return html, True, mode.value, total_retries, FailureReason.UNKNOWN
                
                # Detect failure reason
                failure_reason = FailureReason.UNKNOWN
                
            except TimeoutException as e:
                failure_reason = FailureReason.TIMEOUT
                logger.debug(f"Timeout in {mode.value} mode for {url} (attempt {attempt + 1}/{max_attempts})")
                total_retries += 1
            except ssl.SSLError as e:
                failure_reason = FailureReason.SSL_ERROR
                logger.debug(f"SSL error in {mode.value} mode for {url}: {str(e)}")
                return None, False, mode.value, total_retries, failure_reason
            except requests.ConnectionError as e:
                failure_reason = FailureReason.NETWORK_ERROR
                logger.debug(f"Connection error in {mode.value} mode for {url} (attempt {attempt + 1}/{max_attempts})")
                total_retries += 1
            except Exception as e:
                failure_reason = self._detect_failure_reason(e)
                logger.debug(f"Error in {mode.value} mode for {url}: {str(e)}")
                total_retries += 1
            
            # Add delay before retry
            if attempt < max_attempts - 1:
                delay = self.retry_strategy.get_retry_delay(attempt)
                logger.debug(f"Retrying {url} in {delay:.1f}s (attempt {attempt + 2}/{max_attempts})")
                time.sleep(delay)
        
        return html, False, mode.value, total_retries, failure_reason

    def _fetch_with_mode(self, url: str, mode: FetchMode) -> Tuple[Optional[str], bool, str, int]:
        """Fetch using specified mode, returns (html, success, mode_used, retry_count)"""
        if mode == FetchMode.FAST_HTML:
            html, success, retries = self._fetch_fast_html(url)
        elif mode == FetchMode.JS_RENDERING:
            html, success, retries = self._fetch_js_rendering(url)
        elif mode == FetchMode.HARD_MODE:
            html, success, retries = self._fetch_hard_mode(url)
        else:
            html, success, retries = None, False, 0
        
        return html, success, mode.value, retries

    def _fetch_fast_html(self, url: str) -> Tuple[Optional[str], bool, int]:
        """Fast HTML fetch using standard requests with header rotation and caching"""
        # PHASE 1 OPTIMIZATION: Check cache first
        cached_html = http_cache.get(url)
        if cached_html:
            logger.debug(f"Cache hit for {url}")
            return cached_html, True, 0
        
        retries = 0
        headers_list = [
            AntiBlockingHeaders.get_random_headers(),
            AntiBlockingHeaders.get_random_headers(),
            AntiBlockingHeaders.get_random_headers(),
        ]

        for attempt, headers in enumerate(headers_list, 1):
            try:
                proxy = self.proxy_manager.get_next_proxy()
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=False
                )
                if response.status_code == 200:
                    logger.info(f"Fast HTML fetch succeeded for {url} on attempt {attempt}")
                    # PHASE 1 OPTIMIZATION: Cache the response
                    http_cache.set(url, response.text, ttl=3600)  # 1 hour TTL
                    return response.text, True, attempt - 1
                elif response.status_code in [403, 429]:
                    logger.debug(f"Fast HTML got {response.status_code} for {url}, will retry")
                    retries = attempt
                else:
                    logger.debug(f"Fast HTML got {response.status_code} for {url}")
                    retries = attempt
            except requests.Timeout:
                logger.debug(f"Fast HTML timeout for {url} (attempt {attempt})")
                retries = attempt
                time.sleep(0.5)
            except requests.ConnectionError as e:
                logger.debug(f"Fast HTML connection error for {url} (attempt {attempt}): {str(e)}")
                retries = attempt
                time.sleep(0.5)
            except requests.RequestException as e:
                logger.debug(f"Fast HTML request error for {url} (attempt {attempt}): {str(e)}")
                retries = attempt
                time.sleep(0.5)

        return None, False, retries

    def _fetch_js_rendering(self, url: str) -> Tuple[Optional[str], bool, int]:
        """JS rendering using Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, falling back to Selenium")
            return self._fetch_with_selenium(url, self.timeout)
        
        retries = 0
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(AntiBlockingHeaders.USER_AGENTS),
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                try:
                    page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
                    html = page.content()
                    logger.info(f"JS rendering succeeded for {url}")
                    browser.close()
                    return html, True, 0
                except PlaywrightTimeoutError:
                    logger.debug(f"JS rendering timeout for {url}")
                    retries = 1
                finally:
                    browser.close()
        except Exception as e:
            logger.debug(f"JS rendering failed for {url}: {str(e)}")
            retries = 1

        return None, False, retries

    def _fetch_hard_mode(self, url: str) -> Tuple[Optional[str], bool, int]:
        """Hard mode with anti-blocking techniques"""
        retries = 0
        max_retries = 5
        
        for attempt in range(1, max_retries + 1):
            try:
                # Rotating headers and proxies
                headers = AntiBlockingHeaders.get_random_headers()
                proxy = self.proxy_manager.get_next_proxy()
                
                # Add delay to avoid rate limiting
                if attempt > 1:
                    delay = self.hard_mode_delay * (attempt - 1) + random.uniform(0, 1)
                    logger.debug(f"Hard mode delay: {delay:.2f}s before attempt {attempt}")
                    time.sleep(delay)
                
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    logger.info(f"Hard mode succeeded for {url} on attempt {attempt}")
                    return response.text, True, attempt - 1
                elif response.status_code in [429, 403]:
                    logger.debug(f"Hard mode got {response.status_code} for {url}, retrying...")
                    retries = attempt
                    continue
                else:
                    logger.debug(f"Hard mode got {response.status_code} for {url}")
                    retries = attempt
                    
            except requests.RequestException as e:
                logger.debug(f"Hard mode attempt {attempt} failed for {url}: {str(e)}")
                retries = attempt
                if attempt < max_retries:
                    continue

        return None, False, retries

    def _fetch_html(self, url: str) -> Tuple[Optional[str], bool]:
        headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'},
        ]

        for attempt, headers in enumerate(headers_list, 1):
            try:
                proxy = self.proxy_manager.get_next_proxy()
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                if response.status_code == 200:
                    logger.info(f"Successfully fetched {url} on attempt {attempt}")
                    return response.text, True
            except requests.RequestException as e:
                logger.debug(f"Attempt {attempt} failed for {url}: {str(e)}")
                time.sleep(1)

        return None, False

    def _fetch_with_selenium(self, url: str, timeout: Optional[int] = None) -> Tuple[Optional[str], bool]:
        driver = None
        try:
            if timeout is None:
                timeout = self.timeout
                
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
            )
            html = driver.page_source
            logger.info(f"Successfully fetched {url} with Selenium")
            return html, True
        except (TimeoutException, WebDriverException) as e:
            logger.debug(f"Selenium fetch failed for {url}: {str(e)}")
            return None, False
        finally:
            if driver:
                driver.quit()

    def _extract_from_html(self, base_url: str, html: str) -> Tuple[Set[str], Set[str], int, int, Dict]:
        """Extract all data from HTML using parallel extraction"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # PHASE 1 OPTIMIZATION: Parallel extraction with ThreadPoolExecutor
        emails = set()
        phones = set()
        leadership_count = 0
        social_links = {}
        pages_scanned = 1
        
        # Extract from main page in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            email_future = executor.submit(self.extractor.extract_emails, html)
            phone_future = executor.submit(self.extractor.extract_phones, html)
            leadership_future = executor.submit(self.extractor.extract_leadership, html)
            social_future = executor.submit(self.extractor.extract_social_links, html)
            
            # Gather results
            emails = email_future.result()
            phones = phone_future.result()
            leadership_count = leadership_future.result()
            social_links = social_future.result()

        # Discover contact and team pages
        contact_pages, team_pages = self.page_discovery.discover_all_pages(base_url, html)
        all_discovered_pages = contact_pages | team_pages
        
        logger.debug(f"Discovered {len(contact_pages)} contact pages and {len(team_pages)} team pages")

        # Scan discovered pages (limit to prevent excessive scraping)
        for discovered_url in list(all_discovered_pages)[:2]:  # Limit to 2 discovered pages for speed
            try:
                discovered_html, success, _, _ = self._fetch_with_mode(discovered_url, FetchMode.FAST_HTML)
                if success and discovered_html:
                    # Parallel extraction for discovered pages too
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        d_email_future = executor.submit(self.extractor.extract_emails, discovered_html)
                        d_phone_future = executor.submit(self.extractor.extract_phones, discovered_html)
                        d_leadership_future = executor.submit(self.extractor.extract_leadership, discovered_html)
                        d_social_future = executor.submit(self.extractor.extract_social_links, discovered_html)
                        
                        emails.update(d_email_future.result())
                        phones.update(d_phone_future.result())
                        leadership_count += d_leadership_future.result()
                        
                        # Merge social links
                        discovered_social = d_social_future.result()
                        for platform, links in discovered_social.items():
                            if platform not in social_links:
                                social_links[platform] = set()
                            social_links[platform].update(links)
                    
                    pages_scanned += 1
                    logger.debug(f"Successfully scanned discovered page: {discovered_url}")
            except Exception as e:
                logger.debug(f"Failed to scan discovered page {discovered_url}: {str(e)}")

        # Validate emails if validator is available
        if self.email_validator and emails:
            try:
                logger.debug(f"Validating {len(emails)} emails from {base_url}")
                validated_results, summary = self.email_validator.validate_emails(list(emails), base_url, use_batch_smtp=True)
                # Keep only valid emails
                emails = {r.email for r in validated_results if r.is_valid}
                logger.info(f"Email validation complete: {len(emails)} valid emails out of {len(list(emails))}")
            except Exception as e:
                logger.debug(f"Email validation error: {str(e)}")

        return emails, phones, leadership_count, pages_scanned, social_links

    @staticmethod
    def _calculate_confidence(emails: Set[str], phones: Set[str], leadership_count: int, pages_scanned: int, fetch_method: int, retry_count: int = 0) -> float:
        """
        Calculate confidence score 0-1 based on:
        - Number of emails found (0.30)
        - Number of phones found (0.25)
        - Number of pages scanned (0.15)
        - Leadership mentions (0.10)
        - Fetch method (0.10)
        - Retry count (0.10)
        """
        score = 0.0
        
        # Base score for finding ANY data
        has_data = len(emails) > 0 or len(phones) > 0
        if has_data:
            score += 0.15
        
        # Email score (0-0.30)
        # More generous: 1 email = 0.15, 2+ = 0.30
        if len(emails) >= 2:
            email_score = 0.30
        elif len(emails) == 1:
            email_score = 0.15
        else:
            email_score = 0.0
        score += email_score
        
        # Phone score (0-0.25)
        # More generous: 1 phone = 0.12, 2+ = 0.25
        if len(phones) >= 2:
            phone_score = 0.25
        elif len(phones) == 1:
            phone_score = 0.12
        else:
            phone_score = 0.0
        score += phone_score
        
        # Pages scanned score (0-0.15)
        # More generous: 1 page = 0.08, 2+ = 0.15
        if pages_scanned >= 2:
            pages_score = 0.15
        elif pages_scanned >= 1:
            pages_score = 0.08
        else:
            pages_score = 0.0
        score += pages_score
        
        # Leadership mentions score (0-0.10)
        leadership_score = min(leadership_count / 5.0, 1.0) * 0.10
        score += leadership_score
        
        # Fetch method score (0-0.10)
        # Fast HTML (1) = 0.10, JS Rendering (2) = 0.08, Hard Mode (3) = 0.05
        fetch_score = {1: 0.10, 2: 0.08, 3: 0.05}.get(fetch_method, 0.05)
        score += fetch_score
        
        # Retry penalty (0-0.10)
        # No retries = 0.10, 1-2 retries = 0.07, 3+ retries = 0.03
        retry_score = max(0.10 - (retry_count * 0.03), 0.03)
        score += retry_score
        
        return min(score, 1.0)


def _apply_keyword_blocking(result: ScraperResult, block_keywords: List[str]) -> ScraperResult:
    """Filter out emails, phones, and pages that contain blocked keywords"""
    
    # Filter emails - remove if any blocked keyword is in the email
    filtered_emails = []
    for email in result.emails:
        email_lower = email.lower()
        if not any(keyword in email_lower for keyword in block_keywords):
            filtered_emails.append(email)
    
    # Filter phones - remove if any blocked keyword is in the phone
    filtered_phones = []
    for phone in result.phones:
        phone_lower = phone.lower()
        if not any(keyword in phone_lower for keyword in block_keywords):
            filtered_phones.append(phone)
    
    # Update result with filtered data
    result.emails = filtered_emails
    result.phones = filtered_phones
    result.email_list = '; '.join(filtered_emails)
    result.phone_list = '; '.join(filtered_phones)
    
    # Update status if all data was blocked
    if not filtered_emails and not filtered_phones and result.status == "success":
        result.status = "blocked"
        result.reason = f"All results blocked by keywords: {', '.join(block_keywords)}"
    
    return result


def _apply_keyword_blocking_advanced(result, block_keywords: List[str]):
    """Filter out emails, phones, and addresses that contain blocked keywords (for advanced mode)"""
    
    # Filter emails
    if result.emails:
        filtered_emails = []
        for email in result.emails:
            email_lower = email.lower()
            if not any(keyword in email_lower for keyword in block_keywords):
                filtered_emails.append(email)
        result.emails = filtered_emails
    
    # Filter phones
    if result.phones:
        filtered_phones = []
        for phone in result.phones:
            phone_lower = phone.lower()
            if not any(keyword in phone_lower for keyword in block_keywords):
                filtered_phones.append(phone)
        result.phones = filtered_phones
    
    # Filter addresses - convert to string first
    if result.addresses:
        filtered_addresses = []
        for address in result.addresses:
            # Convert address object to string
            address_str = str(address).lower()
            if not any(keyword in address_str for keyword in block_keywords):
                filtered_addresses.append(address)
        result.addresses = filtered_addresses
    
    # Update status if all data was blocked
    if not result.emails and not result.phones and not result.addresses and result.status == "success":
        result.status = "blocked"
    
    return result


def load_urls(input_source: str) -> List[str]:
    if input_source.startswith('http://') or input_source.startswith('https://'):
        return [input_source]
    
    try:
        with open(input_source, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"File {input_source} not found")
        return []


def interactive_mode(scraper: 'WebScraper', output_file: str):
    """Interactive mode - scrape ONE URL and save to CSV"""
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_file == 'results.csv':
        output_file = f"results_{timestamp}.csv"
    else:
        # Insert timestamp before extension
        name, ext = output_file.rsplit('.', 1) if '.' in output_file else (output_file, 'csv')
        output_file = f"{name}_{timestamp}.{ext}"
    
    print("\n" + "="*60)
    print("WEB SCRAPER - Basic Mode")
    print("="*60)
    
    try:
        # Get ONE URL from user
        url = input("Enter URL to scrape: ").strip()
        
        if not url:
            print("No URL provided. Exiting.")
            return
        
        # Add https if not present
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Get blocking keywords from user
        print("\nEnter keywords to BLOCK (comma-separated):")
        print("Examples: 'team, contact, @outlook, outlook'")
        print("Press ENTER to block nothing")
        block_input = input("Block keywords: ").strip()
        
        # Parse blocking keywords
        block_keywords = []
        if block_input:
            block_keywords = [kw.strip().lower() for kw in block_input.split(',') if kw.strip()]
        
        # Scrape the URL with timeout
        print(f"\nScraping {url}...")
        if block_keywords:
            print(f"Blocking: {', '.join(block_keywords)}")
        print("-" * 60)
        
        # Use threading to add timeout
        result_container = [None]
        def scrape_with_timeout():
            result_container[0] = scraper.scrape_url(url)
        
        scrape_thread = threading.Thread(target=scrape_with_timeout, daemon=True)
        scrape_thread.start()
        scrape_thread.join(timeout=60)  # 60 second timeout
        
        if scrape_thread.is_alive():
            print(f"✗ Timeout: Scraping took too long (>60s)")
            print(f"  Try a different URL or check your connection")
            return
        
        result = result_container[0]
        if result is None:
            print(f"✗ Failed: No result returned")
            return
        
        # Apply blocking keywords to filter results
        if block_keywords:
            result = _apply_keyword_blocking(result, block_keywords)
        
        # Show result
        print(f"✓ Status: {result.status}")
        print(f"  Emails: {result.emails if result.emails else 'Not found'}")
        print(f"  Phones: {result.phones if result.phones else 'Not found'}")
        print(f"  Confidence: {result.confidence_score:.2f}")
        print("-" * 60)
        
        # Save to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(result).keys())
            writer.writeheader()
            writer.writerow(asdict(result))
        
        print(f"\n✓ Results saved to: {output_file}")
        print("Done!")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"Error: {e}")


def advanced_interactive_mode(scraper: 'WebScraper', output_file: str):
    """Advanced interactive mode - scrape ONE URL and save to CSV"""
    from advanced_scraper_features import AdvancedScraperPipeline
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_file == 'results.csv':
        output_file = f"results_{timestamp}.csv"
    else:
        name, ext = output_file.rsplit('.', 1) if '.' in output_file else (output_file, 'csv')
        output_file = f"{name}_{timestamp}.{ext}"
    
    print("\n" + "="*70)
    print("WEB SCRAPER - Advanced Mode")
    print("="*70)
    
    # Initialize advanced pipeline
    pipeline = AdvancedScraperPipeline(
        base_scraper=scraper,
        max_workers=5,
        max_pages_per_site=5,
        enable_address_extraction=True,
        enable_company_info=True
    )
    
    try:
        # Get ONE URL from user
        url = input("Enter URL to scrape: ").strip()
        
        if not url:
            print("No URL provided. Exiting.")
            return
        
        # Add https if not present
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Get blocking keywords from user
        print("\nEnter keywords to BLOCK (comma-separated):")
        print("Examples: 'team, contact, @outlook, outlook'")
        print("Press ENTER to block nothing")
        block_input = input("Block keywords: ").strip()
        
        # Parse blocking keywords
        block_keywords = []
        if block_input:
            block_keywords = [kw.strip().lower() for kw in block_input.split(',') if kw.strip()]
        
        # Scrape with advanced features
        print(f"\nScraping {url}...")
        if block_keywords:
            print(f"Blocking: {', '.join(block_keywords)}")
        print("-" * 70)
        
        # Use threading to add timeout
        result_container = [None]
        def scrape_with_timeout():
            result_container[0] = pipeline.scrape_url_advanced(url)
        
        scrape_thread = threading.Thread(target=scrape_with_timeout, daemon=True)
        scrape_thread.start()
        scrape_thread.join(timeout=120)  # 120 second timeout for advanced scraping
        
        if scrape_thread.is_alive():
            print(f"✗ Timeout: Scraping took too long (>120s)")
            print(f"  Try a different URL or check your connection")
            return
        
        result = result_container[0]
        if result is None:
            print(f"✗ Failed: No result returned")
            return
        
        # Apply blocking keywords to filter results
        if block_keywords:
            result = _apply_keyword_blocking_advanced(result, block_keywords)
        
        # Show result
        print(f"✓ Status: {result.status}")
        print(f"  Company: {result.company_name or 'Not found'}")
        print(f"  Emails: {result.emails if result.emails else 'Not found'}")
        print(f"  Phones: {result.phones if result.phones else 'Not found'}")
        print(f"  Addresses: {result.addresses if result.addresses else 'Not found'}")
        print(f"  Quality Score: {result.data_quality_score:.2f}/1.0")
        print(f"  Pages Scraped: {sum(1 for v in result.pages_scraped.values() if v)}")
        print("-" * 70)
        
        # Save to CSV
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=result.to_dict().keys())
            writer.writeheader()
            writer.writerow(result.to_dict())
        
        print(f"\n✓ Results saved to: {output_file}")
        print("Done!")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Web Scraper for Contact Information')
    parser.add_argument('urls', nargs='*', help='URLs or file path containing URLs (optional for interactive mode)')
    parser.add_argument('--proxy-file', help='File containing proxies (ip:port or ip:port:user:pass)')
    parser.add_argument('--output', default='results.csv', help='Output CSV file')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--no-precheck', action='store_true', help='Disable pre-check system')
    parser.add_argument('--hard-mode-delay', type=float, default=0.5, help='Delay between requests in hard mode (seconds)')
    parser.add_argument('--max-pages', type=int, default=10, help='Maximum pages to discover per site')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode: paste URLs one at a time')
    parser.add_argument('--basic', action='store_true', help='Basic mode: disable advanced features (emails & phones only)')
    parser.add_argument('--aggressive', action='store_true', help='Aggressive mode: try multiple strategies to scrape any website (JS, hard mode, etc)')

    args = parser.parse_args()
    
    # Initialize components
    proxy_manager = ProxyManager(args.proxy_file)
    
    # Disable precheck for interactive mode to avoid hangs
    is_interactive = args.interactive or not args.urls
    enable_precheck = not args.no_precheck and not is_interactive
    
    scraper = WebScraper(proxy_manager, args.timeout, enable_precheck=enable_precheck, hard_mode_delay=args.hard_mode_delay, max_pages_per_site=args.max_pages)
    
    # Advanced mode is DEFAULT (unless --basic flag is used)
    use_advanced = not args.basic
    
    # Advanced mode (interactive with advanced features)
    if use_advanced and is_interactive:
        if not ADVANCED_FEATURES_AVAILABLE:
            logger.error("Advanced features not available. Make sure advanced_scraper_features.py is in the project.")
            sys.exit(1)
        advanced_interactive_mode(scraper, args.output)
        return
    
    # Interactive mode
    if is_interactive:
        interactive_mode(scraper, args.output)
        return

    # Load URLs
    urls = []
    for url_input in args.urls:
        urls.extend(load_urls(url_input))

    if not urls:
        logger.error("No URLs provided")
        sys.exit(1)

    logger.info(f"Loaded {len(urls)} URLs to scrape")

    # Use advanced features by default for batch mode too
    if use_advanced and ADVANCED_FEATURES_AVAILABLE:
        from advanced_scraper_features import AdvancedScraperPipeline
        logger.info("Using advanced features (multi-page scraping, quality scoring, address extraction)")
        
        pipeline = AdvancedScraperPipeline(
            base_scraper=scraper,
            max_workers=args.threads,
            max_pages_per_site=args.max_pages,
            enable_address_extraction=True,
            enable_company_info=True
        )
        
        results = pipeline.scrape_urls_parallel(urls)
    else:
        # Basic mode - standard scraping
        logger.info("Using basic features (emails & phones only)")
        
        # Use aggressive scraper if requested
        if args.aggressive and AGGRESSIVE_SCRAPER_AVAILABLE:
            logger.info("Using AGGRESSIVE mode - will try multiple strategies per site")
            aggressive_scraper = create_aggressive_scraper(scraper)
            results = []
            with ThreadPoolExecutor(max_workers=args.threads) as executor:
                futures = {executor.submit(aggressive_scraper.scrape_aggressive, url): url for url in urls}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed: {result.url} - Status: {result.status}")
                    except Exception as e:
                        logger.error(f"Error processing {futures[future]}: {str(e)}")
            logger.info(f"Aggressive scraper stats: {aggressive_scraper.get_strategy_stats()}")
        else:
            # Standard scraping with auto-aggressive enabled by default
            logger.info("Using standard scraping with auto-aggressive mode (will escalate if needed)")
            results = []
            with ThreadPoolExecutor(max_workers=args.threads) as executor:
                # auto_aggressive=True by default - will escalate if normal modes fail
                futures = {executor.submit(scraper.scrape_url, url, auto_aggressive=True): url for url in urls}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed: {result.url} - Status: {result.status}")
                    except Exception as e:
                        logger.error(f"Error processing {futures[future]}: {str(e)}")

    # Write results to CSV with timestamp
    if results:
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.output == 'results.csv':
            output_file = f"results_{timestamp}.csv"
        else:
            # Insert timestamp before extension
            name, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'csv')
            output_file = f"{name}_{timestamp}.{ext}"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # Handle both basic and advanced results
            if hasattr(results[0], 'to_dict'):
                # Advanced results (EnhancedScraperResult)
                fieldnames = results[0].to_dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([r.to_dict() for r in results])
            else:
                # Basic results (ScraperResult)
                fieldnames = asdict(results[0]).keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([asdict(r) for r in results])
        logger.info(f"Results saved to {output_file}")
    else:
        logger.error("No results to save")


if __name__ == '__main__':
    main()
