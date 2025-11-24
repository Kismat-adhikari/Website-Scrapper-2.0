"""
Advanced Scraper Features Module
Extends web scraper with multi-page scraping, parallel processing, 
enhanced validation, and address extraction.
"""

import re
import logging
import threading
import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Configure logging
advanced_logger = logging.getLogger('advanced_scraper')
advanced_logger.setLevel(logging.DEBUG)

# Thread-safe lock for logging
_log_lock = threading.Lock()


class PageType(Enum):
    """Types of pages to scrape"""
    HOMEPAGE = "homepage"
    CONTACT = "contact"
    ABOUT = "about"
    TEAM = "team"
    CAREERS = "careers"
    SERVICES = "services"
    BLOG = "blog"


@dataclass
class Address:
    """Extracted address information"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    full_address: Optional[str] = None
    confidence_score: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)
    
    def __str__(self):
        """String representation"""
        if self.full_address:
            return self.full_address
        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)


@dataclass
class EnhancedScraperResult:
    """Enhanced scraper result with multi-page data"""
    url: str
    status: str
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    addresses: List[Address] = field(default_factory=list)
    social_links: Dict[str, List[str]] = field(default_factory=dict)
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    pages_scraped: Dict[str, bool] = field(default_factory=dict)
    data_quality_score: float = 0.0
    confidence_score: float = 0.0
    pages_scanned: int = 0
    leadership_count: int = 0
    retry_count: int = 0
    fetch_mode: str = "unknown"
    reason: str = "Unknown"
    load_time: float = 0.0
    validation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for CSV"""
        return {
            'url': self.url,
            'status': self.status,
            'emails': '; '.join(self.emails) if self.emails else 'Not found',
            'phones': '; '.join(self.phones) if self.phones else 'Not found',
            'addresses': '; '.join(str(a) for a in self.addresses) if self.addresses else 'Not found',
            'company_name': self.company_name if self.company_name else 'Not found',
            'company_description': self.company_description if self.company_description else 'Not found',
            'pages_scraped': str(self.pages_scraped),
            'data_quality_score': round(self.data_quality_score, 2),
            'confidence_score': round(self.confidence_score, 2),
            'pages_scanned': self.pages_scanned,
            'leadership_count': self.leadership_count,
            'retry_count': self.retry_count,
            'fetch_mode': self.fetch_mode,
            'reason': self.reason,
            'load_time': round(self.load_time, 2),
            'validation_timestamp': self.validation_timestamp
        }


class AddressExtractor:
    """Extract and parse address information"""
    
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    def __init__(self):
        """Initialize address extractor"""
        self._log("Initialized AddressExtractor", logging.INFO)
    
    def extract_addresses(self, html: str) -> List[Address]:
        """Extract all addresses from HTML"""
        addresses = []
        seen_addresses = set()
        
        if not html:
            return addresses
        
        # Clean HTML
        html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Pattern 1: Full address with street, city, state, zip
        pattern1 = r'(\d+\s+[\w\s&.,#-]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Pkwy|Parkway|Terrace|Ter|Circle|Cir|Square|Sq|Apt|Suite|Ste)\.?)\s*,?\s*([A-Za-z\s]+),?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        
        for match in re.finditer(pattern1, html_clean):
            full_addr = match.group(0).strip()
            if full_addr not in seen_addresses:
                try:
                    street, city, state, postal = match.groups()
                    addr = Address(
                        street=street.strip(),
                        city=city.strip(),
                        state=state.strip(),
                        postal_code=postal.strip(),
                        full_address=full_addr,
                        confidence_score=0.9
                    )
                    if self._validate_address(addr):
                        addresses.append(addr)
                        seen_addresses.add(full_addr)
                except:
                    pass
        
        # Pattern 2: City, State, Zip
        pattern2 = r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        
        for match in re.finditer(pattern2, html_clean):
            full_addr = match.group(0).strip()
            if full_addr not in seen_addresses and len(full_addr) > 10:
                try:
                    city, state, postal = match.groups()
                    if state in self.US_STATES:
                        addr = Address(
                            city=city.strip(),
                            state=state.strip(),
                            postal_code=postal.strip(),
                            full_address=full_addr,
                            confidence_score=0.75
                        )
                        addresses.append(addr)
                        seen_addresses.add(full_addr)
                except:
                    pass
        
        return addresses[:5]
    
    def _validate_address(self, address: Address) -> bool:
        """Validate address components"""
        if not address.state or address.state not in self.US_STATES:
            return False
        if not address.city or len(address.city) < 2:
            return False
        if address.postal_code and not re.match(r'^\d{5}(?:-\d{4})?$', address.postal_code):
            return False
        return True
    
    def _log(self, message: str, level: int = logging.INFO):
        """Thread-safe logging"""
        with _log_lock:
            advanced_logger.log(level, message)



class MultiPageScraper:
    """Scrape multiple pages from a website"""
    
    PAGE_PATTERNS = {
        PageType.CONTACT: [
            r'/contact', r'/contact-us', r'/get-in-touch', r'/reach-us',
            r'/contact-info', r'/contact-page', r'/contact-form'
        ],
        PageType.ABOUT: [
            r'/about', r'/about-us', r'/our-story', r'/company',
            r'/who-we-are', r'/about-company'
        ],
        PageType.TEAM: [
            r'/team', r'/our-team', r'/staff', r'/people',
            r'/leadership', r'/management', r'/team-members'
        ],
        PageType.CAREERS: [
            r'/careers', r'/jobs', r'/join-us', r'/work-with-us',
            r'/employment', r'/hiring'
        ],
    }
    
    def __init__(self, max_pages: int = 5, timeout: int = 10):
        self.max_pages = max_pages
        self.timeout = timeout
        self._log("Initialized MultiPageScraper", logging.INFO)
    
    def discover_pages(self, base_url: str, html: str) -> Dict[PageType, str]:
        """Discover related pages from website"""
        discovered = {}
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        
        for link in links:
            try:
                absolute_url = urljoin(base_url, link)
                parsed = urlparse(absolute_url)
                path = parsed.path.lower()
                
                for page_type, patterns in self.PAGE_PATTERNS.items():
                    if page_type not in discovered:
                        for pattern in patterns:
                            if re.search(pattern, path):
                                discovered[page_type] = absolute_url
                                break
            except Exception as e:
                self._log(f"Error processing link {link}: {str(e)}", logging.DEBUG)
        
        return discovered
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)


class DataQualityScorer:
    """Score data quality based on completeness and validation"""
    
    def __init__(self):
        self._log("Initialized DataQualityScorer", logging.INFO)
    
    def calculate_quality_score(
        self,
        emails: List[str],
        phones: List[str],
        addresses: List[Address],
        company_name: Optional[str],
        company_description: Optional[str],
        pages_scanned: int
    ) -> float:
        """Calculate overall data quality score (0.0-1.0)"""
        score = 0.0
        max_score = 0.0
        
        # Email score (0-0.25)
        max_score += 0.25
        if emails:
            email_score = min(len(emails) / 3.0, 1.0) * 0.25
            score += email_score
        
        # Phone score (0-0.20)
        max_score += 0.20
        if phones:
            phone_score = min(len(phones) / 2.0, 1.0) * 0.20
            score += phone_score
        
        # Address score (0-0.15)
        max_score += 0.15
        if addresses:
            address_score = min(len(addresses) / 1.0, 1.0) * 0.15
            score += address_score
        
        # Company info score (0-0.20)
        max_score += 0.20
        if company_name:
            score += 0.10
        if company_description:
            score += 0.10
        
        # Pages scanned score (0-0.20)
        max_score += 0.20
        if pages_scanned > 0:
            pages_score = min(pages_scanned / 5.0, 1.0) * 0.20
            score += pages_score
        
        if max_score > 0:
            return min(score / max_score, 1.0)
        
        return 0.0
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)


class ParallelScraper:
    """Parallel scraper for handling up to 150 concurrent URLs"""
    
    def __init__(self, max_workers: int = 50, timeout: int = 30):
        self.max_workers = min(max_workers, 150)
        self.timeout = timeout
        self._log(f"Initialized ParallelScraper with {self.max_workers} workers", logging.INFO)
    
    def scrape_urls_parallel(
        self,
        urls: List[str],
        scraper_func,
        progress_callback=None
    ) -> List[EnhancedScraperResult]:
        """Scrape multiple URLs in parallel"""
        results = []
        completed = 0
        
        self._log(f"Starting parallel scraping of {len(urls)} URLs with {self.max_workers} workers", logging.INFO)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(scraper_func, url): url
                for url in urls
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(urls))
                    
                    self._log(f"Completed {completed}/{len(urls)} URLs", logging.DEBUG)
                
                except Exception as e:
                    url = futures[future]
                    self._log(f"Error scraping {url}: {str(e)}", logging.ERROR)
                    completed += 1
        
        self._log(f"Parallel scraping completed: {completed}/{len(urls)} successful", logging.INFO)
        return results
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)


class AdvancedRetryStrategy:
    """Advanced retry logic with proxy rotation and backoff"""
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.failure_history = {}
        self._log("Initialized AdvancedRetryStrategy", logging.INFO)
    
    def should_retry(self, url: str) -> bool:
        """Check if URL should be retried"""
        if url not in self.failure_history:
            return True
        return self.failure_history[url]['count'] < self.max_retries
    
    def get_retry_delay(self, url: str) -> float:
        """Get delay before next retry"""
        if url not in self.failure_history:
            return self.initial_delay
        
        retry_count = self.failure_history[url]['count']
        delay = self.initial_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)
    
    def record_failure(self, url: str, reason: str):
        """Record a failure"""
        if url not in self.failure_history:
            self.failure_history[url] = {
                'count': 0,
                'reasons': [],
                'last_attempt': None
            }
        
        self.failure_history[url]['count'] += 1
        self.failure_history[url]['reasons'].append(reason)
        self.failure_history[url]['last_attempt'] = datetime.now().isoformat()
        
        self._log(
            f"Recorded failure for {url} (attempt {self.failure_history[url]['count']}/{self.max_retries}): {reason}",
            logging.DEBUG
        )
    
    def record_success(self, url: str):
        """Record a success"""
        if url in self.failure_history:
            del self.failure_history[url]
        self._log(f"Recorded success for {url}", logging.DEBUG)
    
    def get_failure_count(self, url: str) -> int:
        """Get failure count for URL"""
        if url not in self.failure_history:
            return 0
        return self.failure_history[url]['count']
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)


class CompanyInfoExtractor:
    """Extract company information from HTML"""
    
    def __init__(self):
        self._log("Initialized CompanyInfoExtractor", logging.INFO)
    
    def extract_company_name(self, html: str) -> Optional[str]:
        """Extract company name from HTML"""
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try title tag first
            title = soup.find('title')
            if title and title.string:
                name = title.string.strip()
                name = self._clean_name(name)
                if len(name) > 2:
                    return name
            
            # Try og:title meta tag
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                name = og_title.get('content').strip()
                name = self._clean_name(name)
                if len(name) > 2:
                    return name
            
            # Try h1 tag
            h1 = soup.find('h1')
            if h1 and h1.string:
                name = h1.string.strip()
                if len(name) > 2 and len(name) < 100:
                    return name
        
        except Exception as e:
            self._log(f"Error extracting company name: {str(e)}", logging.DEBUG)
        
        return None
    
    def _clean_name(self, name: str) -> str:
        """Clean company name"""
        name = re.sub(r'\s*[-|]\s*(Home|Website|Official|Site|Web|Online)$', '', name, flags=re.IGNORECASE)
        return name.strip()
    
    def extract_company_description(self, html: str) -> Optional[str]:
        """Extract company description from HTML"""
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc = meta_desc.get('content').strip()
                if len(desc) > 20:
                    return desc
            
            # Try og:description
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                desc = og_desc.get('content').strip()
                if len(desc) > 20:
                    return desc
        
        except Exception as e:
            self._log(f"Error extracting company description: {str(e)}", logging.DEBUG)
        
        return None
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)


class AdvancedScraperPipeline:
    """Complete advanced scraping pipeline"""
    
    def __init__(
        self,
        base_scraper,
        max_workers: int = 50,
        max_pages_per_site: int = 5,
        enable_address_extraction: bool = True,
        enable_company_info: bool = True
    ):
        self.base_scraper = base_scraper
        self.parallel_scraper = ParallelScraper(max_workers=max_workers)
        self.multi_page_scraper = MultiPageScraper(max_pages=max_pages_per_site)
        self.address_extractor = AddressExtractor()
        self.company_extractor = CompanyInfoExtractor()
        self.quality_scorer = DataQualityScorer()
        self.retry_strategy = AdvancedRetryStrategy()
        self.enable_address_extraction = enable_address_extraction
        self.enable_company_info = enable_company_info
        
        self._log("Initialized AdvancedScraperPipeline", logging.INFO)
    
    def scrape_url_advanced(self, url: str) -> EnhancedScraperResult:
        """Scrape URL with advanced features"""
        start_time = time.time()
        
        try:
            # Initial scrape
            result = self.base_scraper.scrape_url(url)
            
            # Convert to enhanced result
            enhanced = EnhancedScraperResult(
                url=url,
                status=result.status,
                emails=result.emails,
                phones=result.phones,
                pages_scanned=result.pages_scanned,
                leadership_count=result.leadership_count,
                confidence_score=result.confidence_score,
                fetch_mode=result.fetch_mode,
                reason=result.reason,
                load_time=result.load_time,
                retry_count=result.retry_count
            )
            
            # Extract company info
            html = getattr(result, 'html', '')
            if self.enable_company_info and html:
                enhanced.company_name = self.company_extractor.extract_company_name(html)
                enhanced.company_description = self.company_extractor.extract_company_description(html)
            
            # Extract addresses
            if self.enable_address_extraction and html:
                enhanced.addresses = self.address_extractor.extract_addresses(html)
            
            # Discover and scrape additional pages
            if html:
                discovered_pages = self.multi_page_scraper.discover_pages(url, html)
                enhanced.pages_scraped = {page_type.value: False for page_type in PageType}
                
                for page_type, page_url in discovered_pages.items():
                    try:
                        page_result = self.base_scraper.scrape_url(page_url)
                        enhanced.pages_scraped[page_type.value] = True
                        
                        enhanced.emails.extend(page_result.emails)
                        enhanced.phones.extend(page_result.phones)
                        enhanced.pages_scanned += page_result.pages_scanned
                        
                        if self.enable_address_extraction:
                            page_html = getattr(page_result, 'html', '')
                            if page_html:
                                enhanced.addresses.extend(
                                    self.address_extractor.extract_addresses(page_html)
                                )
                    
                    except Exception as e:
                        self._log(f"Error scraping {page_type.value} page: {str(e)}", logging.DEBUG)
            
            # Remove duplicates
            enhanced.emails = list(set(enhanced.emails))
            enhanced.phones = list(set(enhanced.phones))
            
            # Calculate quality score
            enhanced.data_quality_score = self.quality_scorer.calculate_quality_score(
                emails=enhanced.emails,
                phones=enhanced.phones,
                addresses=enhanced.addresses,
                company_name=enhanced.company_name,
                company_description=enhanced.company_description,
                pages_scanned=enhanced.pages_scanned
            )
            
            self.retry_strategy.record_success(url)
            enhanced.load_time = time.time() - start_time
            
            self._log(
                f"Advanced scrape completed for {url}: "
                f"Quality={enhanced.data_quality_score:.2f}, "
                f"Emails={len(enhanced.emails)}, "
                f"Phones={len(enhanced.phones)}, "
                f"Addresses={len(enhanced.addresses)}, "
                f"Company={enhanced.company_name}",
                logging.INFO
            )
            
            return enhanced
        
        except Exception as e:
            self._log(f"Error in advanced scrape for {url}: {str(e)}", logging.ERROR)
            self.retry_strategy.record_failure(url, str(e))
            
            return EnhancedScraperResult(
                url=url,
                status="failed",
                reason=str(e),
                load_time=time.time() - start_time
            )
    
    def scrape_urls_parallel(
        self,
        urls: List[str],
        progress_callback=None
    ) -> List[EnhancedScraperResult]:
        """Scrape multiple URLs in parallel with advanced features"""
        return self.parallel_scraper.scrape_urls_parallel(
            urls,
            self.scrape_url_advanced,
            progress_callback
        )
    
    def _log(self, message: str, level: int = logging.INFO):
        with _log_lock:
            advanced_logger.log(level, message)
