"""
Phone Number Validation Module for Web Scraper
Provides multi-stage phone validation with confidence scoring.
"""

import re
import logging
import threading
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Try to import phonenumbers library (optional)
try:
    import phonenumbers
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

# Configure logging
phone_validator_logger = logging.getLogger('phone_validator')
phone_validator_logger.setLevel(logging.DEBUG)

# Thread-safe lock for logging
_log_lock = threading.Lock()


class ValidationReason(Enum):
    """Reasons for phone validation results"""
    VALID = "valid"
    INVALID_SYNTAX = "invalid_syntax"
    INVALID_LENGTH = "invalid_length"
    INVALID_COUNTRY = "invalid_country"
    DISPOSABLE_VOIP = "disposable_voip"
    UNVERIFIED = "unverified"
    BLACKLISTED = "blacklisted"
    UNKNOWN_ERROR = "unknown_error"


class PhoneType(Enum):
    """Phone number types"""
    MOBILE = "mobile"
    FIXED_LINE = "fixed_line"
    VOIP = "voip"
    UNKNOWN = "unknown"


@dataclass
class PhoneValidationResult:
    """Result of phone validation"""
    phone: str
    normalized_phone: str
    is_valid: bool
    confidence_score: float
    reason: ValidationReason
    phone_type: PhoneType = PhoneType.UNKNOWN
    country_code: Optional[str] = None
    syntax_valid: bool = False
    length_valid: bool = False
    country_valid: bool = False
    library_verified: bool = False
    is_voip: bool = False
    validation_timestamp: str = None
    
    def __post_init__(self):
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary for CSV output"""
        return {
            'phone': self.phone,
            'normalized_phone': self.normalized_phone,
            'is_valid': self.is_valid,
            'confidence_score': round(self.confidence_score, 2),
            'reason': self.reason.value,
            'phone_type': self.phone_type.value,
            'country_code': self.country_code or 'unknown',
            'syntax_valid': self.syntax_valid,
            'length_valid': self.length_valid,
            'country_valid': self.country_valid,
            'library_verified': self.library_verified,
            'is_voip': self.is_voip,
            'validation_timestamp': self.validation_timestamp
        }


@dataclass
class ValidationSummary:
    """Summary statistics for a batch of phone numbers"""
    total_phones: int
    valid_phones: int
    invalid_phones: int
    average_confidence: float
    high_confidence_phones: List[str]  # confidence >= 0.8
    medium_confidence_phones: List[str]  # 0.5 <= confidence < 0.8
    low_confidence_phones: List[str]  # confidence < 0.5
    mobile_count: int
    fixed_line_count: int
    voip_count: int


class PhoneValidator:
    """Multi-stage phone validation with confidence scoring"""
    
    # Known VoIP/disposable phone providers
    VOIP_PREFIXES = {
        '1800', '1888', '1877', '1866',  # US toll-free
        '0800', '0808', '0844', '0845',  # UK
        '1300', '1800', '1900',  # Australia
    }
    
    # Country-specific rules (area codes, prefixes)
    COUNTRY_RULES = {
        'US': {
            'country_code': '+1',
            'min_length': 10,
            'max_length': 11,
            'area_code_length': 3,
            'patterns': [r'^\+?1?\d{10}$', r'^\+?1\d{10}$']
        },
        'UK': {
            'country_code': '+44',
            'min_length': 10,
            'max_length': 13,
            'patterns': [r'^\+?44\d{9,11}$', r'^0\d{9,11}$']
        },
        'CA': {
            'country_code': '+1',
            'min_length': 10,
            'max_length': 11,
            'area_code_length': 3,
            'patterns': [r'^\+?1?\d{10}$']
        },
        'AU': {
            'country_code': '+61',
            'min_length': 9,
            'max_length': 12,
            'patterns': [r'^\+?61\d{8,10}$', r'^0\d{8,10}$']
        },
        'DE': {
            'country_code': '+49',
            'min_length': 10,
            'max_length': 13,
            'patterns': [r'^\+?49\d{9,11}$', r'^0\d{9,11}$']
        },
        'FR': {
            'country_code': '+33',
            'min_length': 9,
            'max_length': 12,
            'patterns': [r'^\+?33\d{8,10}$', r'^0\d{8,10}$']
        },
        'JP': {
            'country_code': '+81',
            'min_length': 10,
            'max_length': 12,
            'patterns': [r'^\+?81\d{9,11}$', r'^0\d{9,11}$']
        },
        'IN': {
            'country_code': '+91',
            'min_length': 10,
            'max_length': 12,
            'patterns': [r'^\+?91\d{10}$', r'^0\d{10}$']
        },
    }
    
    def __init__(
        self,
        default_country: str = 'US',
        country_whitelist: Optional[Set[str]] = None,
        country_blacklist: Optional[Set[str]] = None,
        min_length: int = 6,
        max_length: int = 15,
        enable_library_check: bool = True,
        enable_voip_check: bool = True,
        reject_voip: bool = False,
        scraper_confidence: float = 0.5
    ):
        """
        Initialize phone validator
        
        Args:
            default_country: Default country code (e.g., 'US', 'UK')
            country_whitelist: Set of allowed country codes
            country_blacklist: Set of blocked country codes
            min_length: Minimum phone number length
            max_length: Maximum phone number length
            enable_library_check: Use phonenumbers library if available
            enable_voip_check: Check for VoIP numbers
            reject_voip: Reject VoIP numbers
            scraper_confidence: Base confidence from scraper (0.0-1.0)
        """
        self.default_country = default_country
        self.country_whitelist = country_whitelist or set()
        self.country_blacklist = country_blacklist or set()
        self.min_length = min_length
        self.max_length = max_length
        self.enable_library_check = enable_library_check and PHONENUMBERS_AVAILABLE
        self.enable_voip_check = enable_voip_check
        self.reject_voip = reject_voip
        self.scraper_confidence = max(0.0, min(1.0, scraper_confidence))
        
        self._log(
            f"Initialized PhoneValidator (library: {self.enable_library_check}, "
            f"voip_check: {self.enable_voip_check}, reject_voip: {self.reject_voip})",
            logging.INFO
        )
    
    def validate_phones(
        self,
        phones: List[str],
        website_url: str = "unknown",
        country_hint: Optional[str] = None
    ) -> Tuple[List[PhoneValidationResult], ValidationSummary]:
        """
        Validate a list of phone numbers with multi-stage checks
        
        Args:
            phones: List of phone numbers to validate
            website_url: Source website for logging context
            country_hint: Country code hint for validation
            
        Returns:
            Tuple of (validation results, summary statistics)
        """
        if not phones:
            self._log(f"No phones to validate for {website_url}", logging.DEBUG)
            return [], ValidationSummary(0, 0, 0, 0.0, [], [], [], 0, 0, 0)
        
        results = []
        for phone in phones:
            result = self.validate_phone(phone, website_url, country_hint)
            results.append(result)
        
        summary = self._generate_summary(results)
        self._log_summary(website_url, summary)
        
        return results, summary
    
    def validate_phone(
        self,
        phone: str,
        website_url: str = "unknown",
        country_hint: Optional[str] = None
    ) -> PhoneValidationResult:
        """
        Validate a single phone number through multi-stage checks
        
        Args:
            phone: Phone number to validate
            website_url: Source website for logging context
            country_hint: Country code hint for validation
            
        Returns:
            PhoneValidationResult with confidence score
        """
        phone = str(phone).strip()
        country = country_hint or self.default_country
        confidence = 0.0
        
        # Stage 1: Normalize and Syntax Check
        normalized, syntax_valid = self._normalize_and_check_syntax(phone)
        
        if not syntax_valid:
            self._log(
                f"Syntax invalid: {phone} from {website_url}",
                logging.DEBUG
            )
            return PhoneValidationResult(
                phone=phone,
                normalized_phone=phone,
                is_valid=False,
                confidence_score=0.0,
                reason=ValidationReason.INVALID_SYNTAX,
                syntax_valid=False
            )
        
        confidence += 0.4
        
        # Stage 2: Length Check
        length_valid = self._check_length(normalized)
        if not length_valid:
            self._log(
                f"Invalid length: {phone} (normalized: {normalized}) from {website_url}",
                logging.DEBUG
            )
            return PhoneValidationResult(
                phone=phone,
                normalized_phone=normalized,
                is_valid=False,
                confidence_score=confidence * 0.5,  # Partial credit
                reason=ValidationReason.INVALID_LENGTH,
                syntax_valid=True,
                length_valid=False
            )
        
        confidence += 0.3
        
        # Stage 3: Country/Region Check
        country_valid = self._check_country(normalized, country)
        if not country_valid and self.country_whitelist:
            self._log(
                f"Country not in whitelist: {phone} from {website_url}",
                logging.DEBUG
            )
            return PhoneValidationResult(
                phone=phone,
                normalized_phone=normalized,
                is_valid=False,
                confidence_score=confidence * 0.5,
                reason=ValidationReason.INVALID_COUNTRY,
                syntax_valid=True,
                length_valid=True,
                country_valid=False,
                country_code=country
            )
        
        # Stage 4: VoIP Check
        is_voip = False
        if self.enable_voip_check:
            is_voip = self._check_voip(normalized)
            if is_voip and self.reject_voip:
                self._log(
                    f"VoIP number rejected: {phone} from {website_url}",
                    logging.DEBUG
                )
                return PhoneValidationResult(
                    phone=phone,
                    normalized_phone=normalized,
                    is_valid=False,
                    confidence_score=confidence * 0.5,
                    reason=ValidationReason.DISPOSABLE_VOIP,
                    syntax_valid=True,
                    length_valid=True,
                    country_valid=country_valid,
                    is_voip=True,
                    country_code=country
                )
        
        # Stage 5: Library Verification (optional)
        library_verified = False
        phone_type = PhoneType.UNKNOWN
        
        if self.enable_library_check:
            library_verified, phone_type = self._verify_with_library(normalized, country)
            if library_verified:
                confidence += 0.3
        
        # Final result
        is_valid = confidence >= 0.6
        
        result = PhoneValidationResult(
            phone=phone,
            normalized_phone=normalized,
            is_valid=is_valid,
            confidence_score=min(1.0, confidence),
            reason=ValidationReason.VALID if is_valid else ValidationReason.UNVERIFIED,
            phone_type=phone_type,
            country_code=country,
            syntax_valid=True,
            length_valid=True,
            country_valid=country_valid,
            library_verified=library_verified,
            is_voip=is_voip
        )
        
        if is_valid:
            self._log(
                f"Valid phone: {normalized} (confidence: {result.confidence_score:.2f}, "
                f"type: {phone_type.value}) from {website_url}",
                logging.INFO
            )
        
        return result
    
    def _normalize_and_check_syntax(self, phone: str) -> Tuple[str, bool]:
        """Normalize phone number and check syntax"""
        # Remove common separators
        normalized = re.sub(r'[\s\-\(\)\.\+]', '', phone)
        
        # Allow + prefix
        if phone.strip().startswith('+'):
            normalized = '+' + normalized
        
        # Check if only digits (and optional +)
        if not re.match(r'^\+?\d+$', normalized):
            return phone, False
        
        # Remove + for length check
        digits_only = normalized.lstrip('+')
        
        # Check minimum length
        if len(digits_only) < self.min_length:
            return normalized, False
        
        # STRICT: Reject numbers with all repeating digits (1111111111, 0000000000, etc.)
        if len(set(digits_only)) == 1:
            return normalized, False
        
        # STRICT: Reject numbers with too many repeating patterns (1414141414, etc.)
        if len(set(digits_only)) <= 2:
            return normalized, False
        
        # STRICT: Reject numbers that look like IDs (too many zeros or ones)
        zero_count = digits_only.count('0')
        one_count = digits_only.count('1')
        if zero_count > len(digits_only) * 0.6 or one_count > len(digits_only) * 0.6:
            return normalized, False
        
        # STRICT: Reject sequential numbers (123456789, 987654321)
        is_sequential = True
        for i in range(len(digits_only) - 1):
            if abs(int(digits_only[i]) - int(digits_only[i+1])) > 1:
                is_sequential = False
                break
        if is_sequential and len(digits_only) >= 7:
            return normalized, False
        
        # STRICT: Reject numbers with invalid US area codes (starting with 0 or 1)
        if len(digits_only) >= 10:
            # Check if it's a US/CA number (10-11 digits)
            if len(digits_only) in [10, 11]:
                # Get area code (first 3 digits after country code)
                area_code_start = 1 if len(digits_only) == 11 and digits_only[0] == '1' else 0
                area_code = digits_only[area_code_start:area_code_start+3]
                
                # Area codes can't start with 0 or 1
                if area_code[0] in ['0', '1']:
                    return normalized, False
        
        # STRICT: Reject numbers that are too short to be real
        if len(digits_only) < 10:
            return normalized, False
        
        return normalized, True
    
    def _check_length(self, normalized: str) -> bool:
        """Check if phone number has valid length"""
        digits_only = normalized.lstrip('+')
        return self.min_length <= len(digits_only) <= self.max_length
    
    def _check_country(self, normalized: str, country: str) -> bool:
        """Check if phone number matches country rules"""
        if country not in self.COUNTRY_RULES:
            return True  # Unknown country, assume valid
        
        if country in self.country_blacklist:
            return False
        
        if self.country_whitelist and country not in self.country_whitelist:
            return False
        
        rules = self.COUNTRY_RULES[country]
        
        # Check against patterns if available
        if 'patterns' in rules:
            for pattern in rules['patterns']:
                if re.match(pattern, normalized):
                    return True
        
        return True
    
    def _check_voip(self, normalized: str) -> bool:
        """Check if number is likely VoIP"""
        digits_only = normalized.lstrip('+')
        
        # Check against known VoIP prefixes
        for prefix in self.VOIP_PREFIXES:
            if digits_only.startswith(prefix):
                return True
        
        return False
    
    def _verify_with_library(self, normalized: str, country: str) -> Tuple[bool, PhoneType]:
        """Verify phone number using phonenumbers library"""
        if not self.enable_library_check:
            return False, PhoneType.UNKNOWN
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(normalized, country)
            
            # Check if valid
            if not phonenumbers.is_valid_number(parsed):
                return False, PhoneType.UNKNOWN
            
            # Determine phone type
            phone_type = PhoneType.UNKNOWN
            number_type = phonenumbers.number_type(parsed)
            
            if number_type == phonenumbers.phonenumberutil.NumberType.MOBILE:
                phone_type = PhoneType.MOBILE
            elif number_type == phonenumbers.phonenumberutil.NumberType.FIXED_LINE:
                phone_type = PhoneType.FIXED_LINE
            elif number_type == phonenumbers.phonenumberutil.NumberType.VOIP:
                phone_type = PhoneType.VOIP
            
            return True, phone_type
        
        except Exception as e:
            self._log(f"Library verification error: {str(e)}", logging.DEBUG)
            return False, PhoneType.UNKNOWN
    
    def _generate_summary(self, results: List[PhoneValidationResult]) -> ValidationSummary:
        """Generate summary statistics from validation results"""
        if not results:
            return ValidationSummary(0, 0, 0, 0.0, [], [], [], 0, 0, 0)
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        
        high_conf = [r.normalized_phone for r in results if r.confidence_score >= 0.8]
        med_conf = [r.normalized_phone for r in results if 0.5 <= r.confidence_score < 0.8]
        low_conf = [r.normalized_phone for r in results if r.confidence_score < 0.5]
        
        mobile_count = sum(1 for r in results if r.phone_type == PhoneType.MOBILE)
        fixed_count = sum(1 for r in results if r.phone_type == PhoneType.FIXED_LINE)
        voip_count = sum(1 for r in results if r.phone_type == PhoneType.VOIP)
        
        return ValidationSummary(
            total_phones=len(results),
            valid_phones=valid_count,
            invalid_phones=invalid_count,
            average_confidence=round(avg_confidence, 2),
            high_confidence_phones=high_conf,
            medium_confidence_phones=med_conf,
            low_confidence_phones=low_conf,
            mobile_count=mobile_count,
            fixed_line_count=fixed_count,
            voip_count=voip_count
        )
    
    def _log(self, message: str, level: int = logging.INFO):
        """Thread-safe logging"""
        with _log_lock:
            phone_validator_logger.log(level, message)
    
    def _log_summary(self, website_url: str, summary: ValidationSummary):
        """Log validation summary for a website"""
        self._log(
            f"Validation Summary for {website_url}: "
            f"Total={summary.total_phones}, Valid={summary.valid_phones}, "
            f"Invalid={summary.invalid_phones}, AvgConfidence={summary.average_confidence}, "
            f"Mobile={summary.mobile_count}, FixedLine={summary.fixed_line_count}, "
            f"VoIP={summary.voip_count}",
            logging.INFO
        )


class PhoneValidationPipeline:
    """
    Integration pipeline for phone validation with scraper
    Handles batch processing and CSV integration
    """
    
    def __init__(self, validator: PhoneValidator):
        """Initialize pipeline with validator instance"""
        self.validator = validator
        self._log = validator._log
    
    def process_scraper_result(
        self,
        phones: List[str],
        website_url: str,
        country_hint: Optional[str] = None,
        scraper_confidence: float = 0.5
    ) -> Dict:
        """
        Process phones from scraper result
        
        Args:
            phones: List of phones extracted by scraper
            website_url: Source website URL
            country_hint: Country code hint for validation
            scraper_confidence: Confidence score from scraper
            
        Returns:
            Dictionary with validated phones and metadata
        """
        results, summary = self.validator.validate_phones(
            phones, website_url, country_hint
        )
        
        # Separate by confidence level
        validated_phones = [r for r in results if r.is_valid]
        rejected_phones = [r for r in results if not r.is_valid]
        
        return {
            'website_url': website_url,
            'country_hint': country_hint or self.validator.default_country,
            'scraper_confidence': scraper_confidence,
            'validated_phones': validated_phones,
            'rejected_phones': rejected_phones,
            'summary': summary,
            'validation_results': results
        }
    
    def export_to_csv_format(
        self,
        validation_results: List[PhoneValidationResult]
    ) -> List[Dict]:
        """
        Convert validation results to CSV-compatible format
        
        Args:
            validation_results: List of PhoneValidationResult objects
            
        Returns:
            List of dictionaries for CSV writing
        """
        return [r.to_dict() for r in validation_results]
    
    def get_best_phones(
        self,
        validation_results: List[PhoneValidationResult],
        min_confidence: float = 0.8,
        phone_type_filter: Optional[PhoneType] = None
    ) -> List[str]:
        """
        Get highest-confidence phone numbers for outreach
        
        Args:
            validation_results: List of validation results
            min_confidence: Minimum confidence threshold
            phone_type_filter: Filter by phone type (mobile, fixed_line, etc.)
            
        Returns:
            List of high-confidence phone numbers
        """
        phones = [
            r.normalized_phone for r in validation_results
            if r.is_valid and r.confidence_score >= min_confidence
        ]
        
        if phone_type_filter:
            phones = [
                r.normalized_phone for r in validation_results
                if r.is_valid and r.confidence_score >= min_confidence
                and r.phone_type == phone_type_filter
            ]
        
        return phones
    
    def get_mobile_phones(
        self,
        validation_results: List[PhoneValidationResult],
        min_confidence: float = 0.8
    ) -> List[str]:
        """
        Get high-confidence mobile phone numbers
        
        Args:
            validation_results: List of validation results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of mobile phone numbers
        """
        return [
            r.normalized_phone for r in validation_results
            if r.is_valid and r.confidence_score >= min_confidence
            and r.phone_type == PhoneType.MOBILE
        ]


def create_validator(
    default_country: str = 'US',
    country_whitelist: Optional[List[str]] = None,
    country_blacklist: Optional[List[str]] = None,
    min_length: int = 6,
    max_length: int = 15,
    enable_library_check: bool = True,
    enable_voip_check: bool = True,
    reject_voip: bool = False
) -> PhoneValidator:
    """
    Factory function to create configured validator
    
    Args:
        default_country: Default country code
        country_whitelist: List of allowed countries
        country_blacklist: List of blocked countries
        min_length: Minimum phone length
        max_length: Maximum phone length
        enable_library_check: Use phonenumbers library
        enable_voip_check: Check for VoIP numbers
        reject_voip: Reject VoIP numbers
        
    Returns:
        Configured PhoneValidator instance
    """
    return PhoneValidator(
        default_country=default_country,
        country_whitelist=set(country_whitelist) if country_whitelist else None,
        country_blacklist=set(country_blacklist) if country_blacklist else None,
        min_length=min_length,
        max_length=max_length,
        enable_library_check=enable_library_check,
        enable_voip_check=enable_voip_check,
        reject_voip=reject_voip
    )
