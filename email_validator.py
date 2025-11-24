"""
Email Validation Module for Web Scraper
Provides multi-stage email validation with confidence scoring.
"""

import re
import logging
import threading
import smtplib
import socket
import dns.resolver
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Configure logging
email_validator_logger = logging.getLogger('email_validator')
email_validator_logger.setLevel(logging.DEBUG)

# Thread-safe lock for logging
_log_lock = threading.Lock()


class ValidationReason(Enum):
    """Reasons for email validation results"""
    VALID = "valid"
    INVALID_SYNTAX = "invalid_syntax"
    NO_MX_RECORD = "no_mx_record"
    DISPOSABLE_DOMAIN = "disposable_domain"
    SMTP_FAILED = "smtp_failed"
    BLACKLISTED = "blacklisted"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class EmailValidationResult:
    """Result of email validation"""
    email: str
    is_valid: bool
    confidence_score: float
    reason: ValidationReason
    syntax_valid: bool = False
    mx_exists: bool = False
    is_disposable: bool = False
    smtp_verified: bool = False
    validation_timestamp: str = None
    
    def __post_init__(self):
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary for CSV output"""
        return {
            'email': self.email,
            'is_valid': self.is_valid,
            'confidence_score': round(self.confidence_score, 2),
            'reason': self.reason.value,
            'syntax_valid': self.syntax_valid,
            'mx_exists': self.mx_exists,
            'is_disposable': self.is_disposable,
            'smtp_verified': self.smtp_verified,
            'validation_timestamp': self.validation_timestamp
        }


@dataclass
class ValidationSummary:
    """Summary statistics for a batch of emails"""
    total_emails: int
    valid_emails: int
    invalid_emails: int
    average_confidence: float
    high_confidence_emails: List[str]  # confidence >= 0.8
    medium_confidence_emails: List[str]  # 0.5 <= confidence < 0.8
    low_confidence_emails: List[str]  # confidence < 0.5


class EmailValidator:
    """Multi-stage email validation with confidence scoring"""
    
    # Known disposable email domains
    DISPOSABLE_DOMAINS = {
        'mailinator.com', '10minutemail.com', 'tempmail.com', 'guerrillamail.com',
        'throwaway.email', 'maildrop.cc', 'temp-mail.org', 'yopmail.com',
        'fakeinbox.com', 'trashmail.com', 'sharklasers.com', 'spam4.me',
        'tempmail.us', 'mailnesia.com', 'maildrop.cc', 'mintemail.com',
        'temp-mail.io', 'throwawaymail.com', 'guerrillamail.info', 'mailinator.net'
    }
    
    # Email syntax pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )
    
    def __init__(
        self,
        enable_smtp_check: bool = False,
        smtp_timeout: int = 5,
        domain_whitelist: Optional[Set[str]] = None,
        domain_blacklist: Optional[Set[str]] = None,
        custom_disposable_domains: Optional[Set[str]] = None,
        scraper_confidence: float = 0.5
    ):
        """
        Initialize email validator
        
        Args:
            enable_smtp_check: Enable SMTP verification (slower, may trigger rate limits)
            smtp_timeout: Timeout for SMTP connections in seconds
            domain_whitelist: Set of domains to always accept
            domain_blacklist: Set of domains to always reject
            custom_disposable_domains: Additional disposable domains to check
            scraper_confidence: Base confidence from scraper (0.0-1.0)
        """
        self.enable_smtp_check = enable_smtp_check
        self.smtp_timeout = smtp_timeout
        self.domain_whitelist = domain_whitelist or set()
        self.domain_blacklist = domain_blacklist or set()
        self.scraper_confidence = max(0.0, min(1.0, scraper_confidence))
        
        # Merge custom disposable domains
        self.disposable_domains = self.DISPOSABLE_DOMAINS.copy()
        if custom_disposable_domains:
            self.disposable_domains.update(custom_disposable_domains)
        
        self._log("Initialized EmailValidator", logging.INFO)
    
    def validate_emails(
        self,
        emails: List[str],
        website_url: str = "unknown"
    ) -> Tuple[List[EmailValidationResult], ValidationSummary]:
        """
        Validate a list of emails with multi-stage checks
        
        Args:
            emails: List of email addresses to validate
            website_url: Source website for logging context
            
        Returns:
            Tuple of (validation results, summary statistics)
        """
        if not emails:
            self._log(f"No emails to validate for {website_url}", logging.DEBUG)
            return [], ValidationSummary(0, 0, 0, 0.0, [], [], [])
        
        results = []
        for email in emails:
            result = self.validate_email(email, website_url)
            results.append(result)
        
        summary = self._generate_summary(results)
        self._log_summary(website_url, summary)
        
        return results, summary
    
    def validate_email(
        self,
        email: str,
        website_url: str = "unknown"
    ) -> EmailValidationResult:
        """
        Validate a single email through multi-stage checks
        
        Args:
            email: Email address to validate
            website_url: Source website for logging context
            
        Returns:
            EmailValidationResult with confidence score
        """
        email = email.strip().lower()
        confidence = 0.0
        
        # Stage 1: Syntax Check
        syntax_valid = self._check_syntax(email)
        if not syntax_valid:
            self._log(
                f"Syntax invalid: {email} from {website_url}",
                logging.DEBUG
            )
            return EmailValidationResult(
                email=email,
                is_valid=False,
                confidence_score=0.0,
                reason=ValidationReason.INVALID_SYNTAX,
                syntax_valid=False
            )
        
        confidence += 0.4
        domain = email.split('@')[1]
        
        # Check whitelist/blacklist
        if domain in self.domain_blacklist:
            self._log(
                f"Domain blacklisted: {email} from {website_url}",
                logging.DEBUG
            )
            return EmailValidationResult(
                email=email,
                is_valid=False,
                confidence_score=0.0,
                reason=ValidationReason.BLACKLISTED,
                syntax_valid=True
            )
        
        if self.domain_whitelist and domain not in self.domain_whitelist:
            self._log(
                f"Domain not in whitelist: {email} from {website_url}",
                logging.DEBUG
            )
            return EmailValidationResult(
                email=email,
                is_valid=False,
                confidence_score=0.0,
                reason=ValidationReason.BLACKLISTED,
                syntax_valid=True
            )
        
        # Stage 2: Disposable Domain Check
        is_disposable = self._check_disposable(domain)
        if is_disposable:
            self._log(
                f"Disposable domain: {email} from {website_url}",
                logging.DEBUG
            )
            return EmailValidationResult(
                email=email,
                is_valid=False,
                confidence_score=0.2,
                reason=ValidationReason.DISPOSABLE_DOMAIN,
                syntax_valid=True,
                is_disposable=True
            )
        
        confidence += 0.2
        
        # Stage 3: MX Record Check
        mx_exists = self._check_mx_record(domain)
        if not mx_exists:
            self._log(
                f"No MX record: {email} from {website_url}",
                logging.DEBUG
            )
            return EmailValidationResult(
                email=email,
                is_valid=False,
                confidence_score=confidence,
                reason=ValidationReason.NO_MX_RECORD,
                syntax_valid=True,
                mx_exists=False,
                is_disposable=False
            )
        
        confidence += 0.4
        
        # Stage 4: Optional SMTP Check
        smtp_verified = False
        if self.enable_smtp_check:
            smtp_verified = self._check_smtp(email, domain)
            if smtp_verified:
                confidence = min(1.0, confidence + 0.2)
        
        # Final result
        is_valid = confidence >= 0.6  # Threshold for valid email
        
        result = EmailValidationResult(
            email=email,
            is_valid=is_valid,
            confidence_score=min(1.0, confidence),
            reason=ValidationReason.VALID if is_valid else ValidationReason.UNKNOWN_ERROR,
            syntax_valid=True,
            mx_exists=True,
            is_disposable=False,
            smtp_verified=smtp_verified
        )
        
        if is_valid:
            self._log(
                f"Valid email: {email} (confidence: {result.confidence_score:.2f}) from {website_url}",
                logging.INFO
            )
        
        return result
    
    def _check_syntax(self, email: str) -> bool:
        """Check if email has valid syntax"""
        if not email or '@' not in email:
            return False
        
        if len(email) > 254:  # RFC 5321
            return False
        
        return bool(self.EMAIL_PATTERN.match(email))
    
    def _check_disposable(self, domain: str) -> bool:
        """Check if domain is a known disposable email provider"""
        return domain.lower() in self.disposable_domains
    
    def _check_mx_record(self, domain: str) -> bool:
        """Check if domain has valid MX records"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
            return False
        except Exception as e:
            self._log(f"MX lookup error for {domain}: {str(e)}", logging.DEBUG)
            return False
    
    def _check_smtp(self, email: str, domain: str) -> bool:
        """
        Perform non-intrusive SMTP check (RCPT TO)
        
        Note: This is rate-limited and may fail on strict servers.
        Use sparingly.
        """
        try:
            # Get MX server
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            # Connect to SMTP server
            with smtplib.SMTP(mx_host, timeout=self.smtp_timeout) as server:
                server.helo(server.local_hostname)
                server.mail('test@example.com')
                code, message = server.rcpt(email)
                
                # 250 = accepted, 450/550 = rejected
                return code == 250
        except smtplib.SMTPServerDisconnected:
            return False
        except socket.timeout:
            return False
        except Exception as e:
            self._log(f"SMTP check error for {email}: {str(e)}", logging.DEBUG)
            return False
    
    def _generate_summary(self, results: List[EmailValidationResult]) -> ValidationSummary:
        """Generate summary statistics from validation results"""
        if not results:
            return ValidationSummary(0, 0, 0, 0.0, [], [], [])
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        
        high_conf = [r.email for r in results if r.confidence_score >= 0.8]
        med_conf = [r.email for r in results if 0.5 <= r.confidence_score < 0.8]
        low_conf = [r.email for r in results if r.confidence_score < 0.5]
        
        return ValidationSummary(
            total_emails=len(results),
            valid_emails=valid_count,
            invalid_emails=invalid_count,
            average_confidence=round(avg_confidence, 2),
            high_confidence_emails=high_conf,
            medium_confidence_emails=med_conf,
            low_confidence_emails=low_conf
        )
    
    def _log(self, message: str, level: int = logging.INFO):
        """Thread-safe logging"""
        with _log_lock:
            email_validator_logger.log(level, message)
    
    def _log_summary(self, website_url: str, summary: ValidationSummary):
        """Log validation summary for a website"""
        self._log(
            f"Validation Summary for {website_url}: "
            f"Total={summary.total_emails}, Valid={summary.valid_emails}, "
            f"Invalid={summary.invalid_emails}, AvgConfidence={summary.average_confidence}",
            logging.INFO
        )


class EmailValidationPipeline:
    """
    Integration pipeline for email validation with scraper
    Handles batch processing and CSV integration
    """
    
    def __init__(self, validator: EmailValidator):
        """Initialize pipeline with validator instance"""
        self.validator = validator
        self._log = validator._log
    
    def process_scraper_result(
        self,
        emails: List[str],
        website_url: str,
        scraper_confidence: float = 0.5
    ) -> Dict:
        """
        Process emails from scraper result
        
        Args:
            emails: List of emails extracted by scraper
            website_url: Source website URL
            scraper_confidence: Confidence score from scraper
            
        Returns:
            Dictionary with validated emails and metadata
        """
        results, summary = self.validator.validate_emails(emails, website_url)
        
        # Separate by confidence level
        validated_emails = [r for r in results if r.is_valid]
        rejected_emails = [r for r in results if not r.is_valid]
        
        return {
            'website_url': website_url,
            'scraper_confidence': scraper_confidence,
            'validated_emails': validated_emails,
            'rejected_emails': rejected_emails,
            'summary': summary,
            'validation_results': results
        }
    
    def export_to_csv_format(
        self,
        validation_results: List[EmailValidationResult]
    ) -> List[Dict]:
        """
        Convert validation results to CSV-compatible format
        
        Args:
            validation_results: List of EmailValidationResult objects
            
        Returns:
            List of dictionaries for CSV writing
        """
        return [r.to_dict() for r in validation_results]
    
    def get_best_emails(
        self,
        validation_results: List[EmailValidationResult],
        min_confidence: float = 0.8
    ) -> List[str]:
        """
        Get highest-confidence emails for outreach
        
        Args:
            validation_results: List of validation results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of high-confidence email addresses
        """
        return [
            r.email for r in validation_results
            if r.is_valid and r.confidence_score >= min_confidence
        ]


def create_validator(
    enable_smtp: bool = False,
    domain_whitelist: Optional[List[str]] = None,
    domain_blacklist: Optional[List[str]] = None,
    custom_disposable: Optional[List[str]] = None
) -> EmailValidator:
    """
    Factory function to create configured validator
    
    Args:
        enable_smtp: Enable SMTP verification
        domain_whitelist: List of allowed domains
        domain_blacklist: List of blocked domains
        custom_disposable: Additional disposable domains
        
    Returns:
        Configured EmailValidator instance
    """
    return EmailValidator(
        enable_smtp_check=enable_smtp,
        domain_whitelist=set(domain_whitelist) if domain_whitelist else None,
        domain_blacklist=set(domain_blacklist) if domain_blacklist else None,
        custom_disposable_domains=set(custom_disposable) if custom_disposable else None
    )
