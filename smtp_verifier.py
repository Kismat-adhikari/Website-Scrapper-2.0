"""
High-Performance SMTP Email Verification with Connection Pooling
Provides fast, accurate email verification with smart retry logic and caching.
"""

import smtplib
import socket
import dns.resolver
import logging
import threading
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Configure logging
smtp_logger = logging.getLogger('smtp_verifier')
smtp_logger.setLevel(logging.DEBUG)

_log_lock = threading.Lock()


class SMTPVerificationReason(Enum):
    """Reasons for SMTP verification results"""
    VERIFIED = "verified"
    INVALID_SYNTAX = "invalid_syntax"
    NO_MX_RECORD = "no_mx_record"
    SMTP_REJECTED = "smtp_rejected"
    SMTP_TIMEOUT = "smtp_timeout"
    SMTP_ERROR = "smtp_error"
    RATE_LIMITED = "rate_limited"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"


@dataclass
class SMTPVerificationResult:
    """Result of SMTP verification"""
    email: str
    is_valid: bool
    reason: SMTPVerificationReason
    mx_host: Optional[str] = None
    response_code: Optional[int] = None
    is_catch_all: bool = False
    verification_time: float = 0.0
    cached: bool = False


class SMTPConnectionPool:
    """Thread-safe connection pool for SMTP servers"""
    
    def __init__(self, max_connections_per_host: int = 3, connection_timeout: int = 5):
        self.max_connections_per_host = max_connections_per_host
        self.connection_timeout = connection_timeout
        self.pools: Dict[str, List[smtplib.SMTP]] = defaultdict(list)
        self.lock = threading.Lock()
        self.stats = {'created': 0, 'reused': 0, 'closed': 0}
    
    def get_connection(self, mx_host: str) -> Optional[smtplib.SMTP]:
        """Get or create SMTP connection to MX host"""
        with self.lock:
            # Try to reuse existing connection
            if mx_host in self.pools and self.pools[mx_host]:
                try:
                    conn = self.pools[mx_host].pop()
                    # Test if connection is still alive
                    conn.noop()
                    self.stats['reused'] += 1
                    return conn
                except (smtplib.SMTPException, socket.error):
                    pass
        
        # Create new connection
        try:
            conn = smtplib.SMTP(mx_host, timeout=self.connection_timeout)
            conn.helo(conn.local_hostname)
            with self.lock:
                self.stats['created'] += 1
            return conn
        except (socket.timeout, socket.error, smtplib.SMTPException) as e:
            _log(f"Failed to connect to {mx_host}: {str(e)}", logging.DEBUG)
            return None
    
    def return_connection(self, mx_host: str, conn: smtplib.SMTP):
        """Return connection to pool"""
        with self.lock:
            if len(self.pools[mx_host]) < self.max_connections_per_host:
                self.pools[mx_host].append(conn)
            else:
                try:
                    conn.quit()
                    self.stats['closed'] += 1
                except:
                    pass
    
    def close_all(self):
        """Close all pooled connections"""
        with self.lock:
            for host, conns in self.pools.items():
                for conn in conns:
                    try:
                        conn.quit()
                        self.stats['closed'] += 1
                    except:
                        pass
            self.pools.clear()
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        with self.lock:
            return self.stats.copy()


class SMTPVerificationCache:
    """In-memory cache for verification results"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[SMTPVerificationResult, float]] = {}
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.stats = {'hits': 0, 'misses': 0, 'expired': 0}
    
    def get(self, email: str) -> Optional[SMTPVerificationResult]:
        """Get cached result if valid"""
        with self.lock:
            if email in self.cache:
                result, timestamp = self.cache[email]
                if time.time() - timestamp < self.ttl_seconds:
                    self.stats['hits'] += 1
                    return result
                else:
                    del self.cache[email]
                    self.stats['expired'] += 1
            self.stats['misses'] += 1
        return None
    
    def set(self, email: str, result: SMTPVerificationResult):
        """Cache verification result"""
        with self.lock:
            self.cache[email] = (result, time.time())
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'expired': self.stats['expired']
            }


class SMTPVerifier:
    """High-performance SMTP email verifier with connection pooling"""
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 3, 5]  # Exponential backoff in seconds
    
    # SMTP timeout per attempt
    SMTP_TIMEOUT = 5
    
    # Rate limit detection
    RATE_LIMIT_CODES = {421, 450, 451}
    
    def __init__(
        self,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        max_workers: int = 5,
        max_connections_per_host: int = 3
    ):
        """
        Initialize SMTP verifier
        
        Args:
            enable_cache: Enable result caching
            cache_ttl: Cache time-to-live in seconds
            max_workers: Max parallel verification threads
            max_connections_per_host: Max SMTP connections per MX host
        """
        self.enable_cache = enable_cache
        self.cache = SMTPVerificationCache(ttl_seconds=cache_ttl) if enable_cache else None
        self.pool = SMTPConnectionPool(max_connections_per_host=max_connections_per_host)
        self.max_workers = max_workers
        self.verified_domains: Set[str] = set()  # Domains we've verified work
        self.failed_domains: Set[str] = set()  # Domains that consistently fail
    
    def verify_email(self, email: str) -> SMTPVerificationResult:
        """Verify single email with retry logic"""
        email = email.strip().lower()
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(email)
            if cached:
                cached.cached = True
                return cached
        
        # Basic syntax check
        if '@' not in email or len(email) > 254:
            result = SMTPVerificationResult(
                email=email,
                is_valid=False,
                reason=SMTPVerificationReason.INVALID_SYNTAX
            )
            if self.cache:
                self.cache.set(email, result)
            return result
        
        domain = email.split('@')[1]
        
        # Get MX records
        mx_hosts = self._get_mx_hosts(domain)
        if not mx_hosts:
            result = SMTPVerificationResult(
                email=email,
                is_valid=False,
                reason=SMTPVerificationReason.NO_MX_RECORD
            )
            if self.cache:
                self.cache.set(email, result)
            return result
        
        # Try verification with retry logic
        start_time = time.time()
        result = self._verify_with_retry(email, mx_hosts)
        result.verification_time = time.time() - start_time
        
        # Cache result
        if self.cache:
            self.cache.set(email, result)
        
        return result
    
    def verify_emails_batch(self, emails: List[str], max_workers: Optional[int] = None) -> List[SMTPVerificationResult]:
        """Verify multiple emails in parallel"""
        if max_workers is None:
            max_workers = self.max_workers
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.verify_email, email): email for email in emails}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    email = futures[future]
                    _log(f"Error verifying {email}: {str(e)}", logging.ERROR)
                    results.append(SMTPVerificationResult(
                        email=email,
                        is_valid=False,
                        reason=SMTPVerificationReason.UNKNOWN
                    ))
        
        return results
    
    def _get_mx_hosts(self, domain: str) -> List[str]:
        """Get MX hosts for domain, sorted by priority"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            hosts = []
            for mx in sorted(mx_records, key=lambda x: x.preference):
                host = str(mx.exchange).rstrip('.')
                hosts.append(host)
            return hosts[:3]  # Limit to top 3 MX hosts
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
            return []
        except Exception as e:
            _log(f"MX lookup error for {domain}: {str(e)}", logging.DEBUG)
            return []
    
    def _verify_with_retry(self, email: str, mx_hosts: List[str]) -> SMTPVerificationResult:
        """Verify email with exponential backoff retry"""
        domain = email.split('@')[1]
        
        for attempt in range(self.MAX_RETRIES):
            for mx_host in mx_hosts:
                result = self._verify_smtp(email, mx_host)
                
                # Success
                if result.is_valid:
                    self.verified_domains.add(domain)
                    return result
                
                # Rate limited - retry with backoff
                if result.reason == SMTPVerificationReason.RATE_LIMITED:
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAYS[attempt]
                        _log(f"Rate limited for {email}, retrying in {delay}s", logging.DEBUG)
                        time.sleep(delay)
                        break  # Try next MX host
                    continue
                
                # Other errors - try next MX host
                if result.reason in [SMTPVerificationReason.SMTP_ERROR, SMTPVerificationReason.SMTP_TIMEOUT]:
                    continue
                
                # Rejected - return immediately
                if result.reason == SMTPVerificationReason.SMTP_REJECTED:
                    self.failed_domains.add(domain)
                    return result
        
        # All attempts failed
        return SMTPVerificationResult(
            email=email,
            is_valid=False,
            reason=SMTPVerificationReason.SMTP_ERROR
        )
    
    def _verify_smtp(self, email: str, mx_host: str) -> SMTPVerificationResult:
        """Perform SMTP verification against specific MX host"""
        conn = None
        try:
            conn = self.pool.get_connection(mx_host)
            if not conn:
                return SMTPVerificationResult(
                    email=email,
                    is_valid=False,
                    reason=SMTPVerificationReason.SMTP_ERROR,
                    mx_host=mx_host
                )
            
            # MAIL FROM
            conn.mail('verify@example.com')
            
            # RCPT TO
            code, message = conn.rcpt(email)
            
            # Analyze response
            if code == 250:
                # Email accepted
                return SMTPVerificationResult(
                    email=email,
                    is_valid=True,
                    reason=SMTPVerificationReason.VERIFIED,
                    mx_host=mx_host,
                    response_code=code
                )
            elif code == 550 or code == 551:
                # User doesn't exist
                return SMTPVerificationResult(
                    email=email,
                    is_valid=False,
                    reason=SMTPVerificationReason.SMTP_REJECTED,
                    mx_host=mx_host,
                    response_code=code
                )
            elif code in self.RATE_LIMIT_CODES:
                # Rate limited
                return SMTPVerificationResult(
                    email=email,
                    is_valid=False,
                    reason=SMTPVerificationReason.RATE_LIMITED,
                    mx_host=mx_host,
                    response_code=code
                )
            else:
                # Catch-all or unknown
                return SMTPVerificationResult(
                    email=email,
                    is_valid=True,
                    reason=SMTPVerificationReason.CATCH_ALL,
                    mx_host=mx_host,
                    response_code=code,
                    is_catch_all=True
                )
        
        except socket.timeout:
            return SMTPVerificationResult(
                email=email,
                is_valid=False,
                reason=SMTPVerificationReason.SMTP_TIMEOUT,
                mx_host=mx_host
            )
        except smtplib.SMTPException as e:
            return SMTPVerificationResult(
                email=email,
                is_valid=False,
                reason=SMTPVerificationReason.SMTP_ERROR,
                mx_host=mx_host
            )
        except Exception as e:
            _log(f"SMTP verification error for {email}: {str(e)}", logging.DEBUG)
            return SMTPVerificationResult(
                email=email,
                is_valid=False,
                reason=SMTPVerificationReason.UNKNOWN,
                mx_host=mx_host
            )
        finally:
            if conn:
                self.pool.return_connection(mx_host, conn)
    
    def get_stats(self) -> Dict:
        """Get verification statistics"""
        stats = {
            'pool': self.pool.get_stats(),
            'verified_domains': len(self.verified_domains),
            'failed_domains': len(self.failed_domains)
        }
        if self.cache:
            stats['cache'] = self.cache.get_stats()
        return stats
    
    def close(self):
        """Close all connections and cleanup"""
        self.pool.close_all()
        if self.cache:
            self.cache.clear()


def _log(message: str, level: int = logging.INFO):
    """Thread-safe logging"""
    with _log_lock:
        smtp_logger.log(level, message)


def create_smtp_verifier(
    enable_cache: bool = True,
    cache_ttl: int = 3600,
    max_workers: int = 5
) -> SMTPVerifier:
    """Factory function to create configured SMTP verifier"""
    return SMTPVerifier(
        enable_cache=enable_cache,
        cache_ttl=cache_ttl,
        max_workers=max_workers
    )
