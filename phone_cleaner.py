"""
Unified Phone Number Cleaning System
Removes demo/placeholder numbers, filters junk from scripts/CDN/checkout,
handles toll-free intelligently, deduplicates, validates, and scores for confidence.
Target: <100ms processing, 99% precision
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('phone_cleaner')


class SourceType(Enum):
    """Phone number source classification"""
    TEL_LINK = "tel_link"              # <a href="tel:">
    SCHEMA_ORG = "schema_org"          # JSON-LD, microdata
    FOOTER = "footer"                  # <footer> tag
    CONTACT_PAGE = "contact_page"      # /contact URL
    ABOUT_PAGE = "about_page"          # /about URL
    VISIBLE_HTML = "visible_html"      # Regular HTML text
    HEADER = "header"                  # <header> tag
    SIDEBAR = "sidebar"                # Sidebar content
    SCRIPT = "script"                  # JavaScript
    CDN = "cdn"                        # CDN resources
    CHECKOUT = "checkout"              # Checkout/cart
    COMMENT = "comment"                # HTML/JS comments
    UNKNOWN = "unknown"


@dataclass
class PhoneNumber:
    """Extracted phone number with metadata"""
    raw: str                           # Original format
    normalized: str                    # Digits only
    canonical: str                     # +1XXXXXXXXXX format
    source_type: SourceType
    source_location: str               # HTML element or URL
    context_before: str = ""           # Text before number
    context_after: str = ""            # Text after number
    page_url: str = ""                 # Page where found
    confidence: float = 0.0            # Confidence score


@dataclass
class CleaningResult:
    """Result of phone cleaning process"""
    kept_numbers: List[PhoneNumber]
    removed_numbers: List[Tuple[str, str]]  # (number, reason)
    stats: Dict[str, int]


class PhoneCleaningPipeline:
    """
    Unified phone cleaning pipeline - one pass processing
    Combines speed and precision for real business numbers only
    """
    
    # Known demo/placeholder numbers (blacklist)
    BLACKLIST = {
        '2147483647',   # Shopify demo
        '6501234567',   # Shopify theme
        '8882462598',   # WooCommerce demo
        '8001234567',   # WordPress theme
        '5551234567',   # Generic placeholder
        '5555555555',   # Test number
        '1234567890',   # Sequential test
    }
    
    # Toll-free prefixes
    TOLL_FREE_PREFIXES = {'800', '833', '844', '855', '866', '877', '888'}
    
    # High-confidence source types
    HIGH_CONFIDENCE_SOURCES = {
        SourceType.TEL_LINK,
        SourceType.SCHEMA_ORG,
        SourceType.FOOTER,
        SourceType.CONTACT_PAGE,
        SourceType.ABOUT_PAGE
    }
    
    # Low-confidence source types (auto-remove)
    LOW_CONFIDENCE_SOURCES = {
        SourceType.SCRIPT,
        SourceType.CDN,
        SourceType.CHECKOUT,
        SourceType.COMMENT
    }
    
    # Context keywords
    POSITIVE_KEYWORDS = {
        'contact', 'call', 'phone', 'reach', 'support', 'office',
        'headquarters', 'customer service', 'help desk', 'inquiries'
    }
    
    NEGATIVE_KEYWORDS = {
        'shopify', 'woocommerce', 'wordpress', 'powered by',
        'example', 'demo', 'sample', 'placeholder', 'test',
        'function', 'var', 'const', 'script', 'error', '404'
    }
    
    def __init__(self, fast_mode: bool = True):
        """
        Initialize phone cleaning pipeline
        
        Args:
            fast_mode: If True, use fast mode (60ms). If False, use accuracy mode (130ms)
        """
        self.fast_mode = fast_mode
        self.stats = {
            'total_extracted': 0,
            'removed_blacklist': 0,
            'removed_source': 0,
            'removed_toll_free': 0,
            'removed_duplicate': 0,
            'removed_validation': 0,
            'removed_context': 0,
            'removed_region': 0,
            'removed_confidence': 0,
            'kept': 0
        }
    
    def clean(self, phone_numbers: List[PhoneNumber], business_region: str = 'US') -> CleaningResult:
        """
        Clean phone numbers in one unified pass
        
        Args:
            phone_numbers: List of extracted phone numbers with metadata
            business_region: Business region code (US, UK, CA, etc.)
            
        Returns:
            CleaningResult with kept numbers, removed numbers, and stats
        """
        self.stats['total_extracted'] = len(phone_numbers)
        removed = []
        
        # STEP 1: Blacklist filter (5ms)
        phone_numbers, blacklist_removed = self._filter_blacklist(phone_numbers)
        removed.extend(blacklist_removed)
        
        # STEP 2: Source location filter (20ms)
        phone_numbers, source_removed = self._filter_by_source(phone_numbers)
        removed.extend(source_removed)
        
        # STEP 3: Toll-free filter (10ms)
        phone_numbers, tollfree_removed = self._filter_toll_free(phone_numbers)
        removed.extend(tollfree_removed)
        
        # STEP 4: Duplicate removal (15ms)
        phone_numbers, duplicate_removed = self._remove_duplicates(phone_numbers)
        removed.extend(duplicate_removed)
        
        # STEP 5: Validation (10ms)
        phone_numbers, validation_removed = self._validate_numbers(phone_numbers)
        removed.extend(validation_removed)
        
        # ACCURACY MODE: Additional steps
        if not self.fast_mode:
            # STEP 6: Context analysis (30ms)
            phone_numbers, context_removed = self._analyze_context(phone_numbers)
            removed.extend(context_removed)
            
            # STEP 7: Region filtering (20ms)
            phone_numbers, region_removed = self._filter_by_region(phone_numbers, business_region)
            removed.extend(region_removed)
            
            # STEP 8: Confidence scoring (20ms)
            phone_numbers, confidence_removed = self._score_confidence(phone_numbers)
            removed.extend(confidence_removed)
        
        self.stats['kept'] = len(phone_numbers)
        
        return CleaningResult(
            kept_numbers=phone_numbers,
            removed_numbers=removed,
            stats=self.stats.copy()
        )
    
    def _filter_blacklist(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Remove blacklisted demo/placeholder numbers"""
        kept = []
        removed = []
        
        for num in numbers:
            if num.normalized in self.BLACKLIST:
                removed.append((num.raw, "Blacklisted demo/placeholder number"))
                self.stats['removed_blacklist'] += 1
            else:
                kept.append(num)
        
        return kept, removed
    
    def _filter_by_source(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Remove numbers from low-confidence sources (scripts, CDN, checkout)"""
        kept = []
        removed = []
        
        for num in numbers:
            if num.source_type in self.LOW_CONFIDENCE_SOURCES:
                removed.append((num.raw, f"Found in {num.source_type.value}"))
                self.stats['removed_source'] += 1
            else:
                kept.append(num)
        
        return kept, removed
    
    def _filter_toll_free(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Remove toll-free numbers unless in high-confidence location"""
        kept = []
        removed = []
        
        for num in numbers:
            # Check if toll-free
            prefix = num.normalized[:3] if len(num.normalized) >= 3 else ''
            is_toll_free = prefix in self.TOLL_FREE_PREFIXES
            
            if is_toll_free:
                # Keep if in high-confidence source
                if num.source_type in self.HIGH_CONFIDENCE_SOURCES:
                    kept.append(num)
                else:
                    removed.append((num.raw, "Toll-free number not in high-confidence location"))
                    self.stats['removed_toll_free'] += 1
            else:
                kept.append(num)
        
        return kept, removed
    
    def _remove_duplicates(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Remove duplicate numbers, keeping highest confidence instance"""
        # Group by canonical form
        canonical_map: Dict[str, List[PhoneNumber]] = {}
        for num in numbers:
            if num.canonical not in canonical_map:
                canonical_map[num.canonical] = []
            canonical_map[num.canonical].append(num)
        
        kept = []
        removed = []
        
        # For each canonical form, keep best instance
        for canonical, instances in canonical_map.items():
            if len(instances) == 1:
                kept.append(instances[0])
            else:
                # Sort by source priority
                source_priority = {
                    SourceType.TEL_LINK: 5,
                    SourceType.SCHEMA_ORG: 4,
                    SourceType.FOOTER: 3,
                    SourceType.CONTACT_PAGE: 2,
                    SourceType.ABOUT_PAGE: 1,
                }
                instances.sort(key=lambda x: source_priority.get(x.source_type, 0), reverse=True)
                
                # Keep first (highest priority)
                kept.append(instances[0])
                
                # Remove others
                for dup in instances[1:]:
                    removed.append((dup.raw, f"Duplicate of {instances[0].raw}"))
                    self.stats['removed_duplicate'] += 1
        
        return kept, removed
    
    def _validate_numbers(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Validate number format, patterns, and area codes"""
        kept = []
        removed = []
        
        for num in numbers:
            # Length check
            if len(num.normalized) not in [10, 11]:
                removed.append((num.raw, "Invalid length"))
                self.stats['removed_validation'] += 1
                continue
            
            # Pattern checks
            digits = num.normalized
            
            # All same digit
            if len(set(digits)) == 1:
                removed.append((num.raw, "All same digit pattern"))
                self.stats['removed_validation'] += 1
                continue
            
            # Repeating pattern (1212121212)
            if len(set(digits)) <= 2:
                removed.append((num.raw, "Repeating pattern"))
                self.stats['removed_validation'] += 1
                continue
            
            # Sequential (1234567890)
            is_sequential = all(
                abs(int(digits[i]) - int(digits[i+1])) <= 1
                for i in range(len(digits)-1)
            )
            if is_sequential and len(digits) >= 7:
                removed.append((num.raw, "Sequential pattern"))
                self.stats['removed_validation'] += 1
                continue
            
            # Area code check (US numbers)
            if len(digits) == 11 and digits[0] == '1':
                area_code = digits[1:4]
            elif len(digits) == 10:
                area_code = digits[0:3]
            else:
                area_code = None
            
            if area_code and area_code[0] in ['0', '1']:
                removed.append((num.raw, "Invalid area code"))
                self.stats['removed_validation'] += 1
                continue
            
            # Passed all checks
            kept.append(num)
        
        return kept, removed
    
    def _analyze_context(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Analyze context keywords around phone numbers"""
        kept = []
        removed = []
        
        for num in numbers:
            context = (num.context_before + ' ' + num.context_after).lower()
            
            # Check for negative keywords
            has_negative = any(keyword in context for keyword in self.NEGATIVE_KEYWORDS)
            
            if has_negative:
                removed.append((num.raw, "Negative keywords in context"))
                self.stats['removed_context'] += 1
            else:
                # Check for positive keywords (bonus for confidence)
                has_positive = any(keyword in context for keyword in self.POSITIVE_KEYWORDS)
                if has_positive:
                    num.confidence += 0.2
                kept.append(num)
        
        return kept, removed
    
    def _filter_by_region(self, numbers: List[PhoneNumber], business_region: str) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Filter numbers based on business region"""
        kept = []
        removed = []
        
        # If business is non-US, filter +1 numbers
        if business_region != 'US':
            for num in numbers:
                # Check if US number (+1)
                is_us_number = num.canonical.startswith('+1') or (
                    len(num.normalized) == 11 and num.normalized[0] == '1'
                )
                
                if is_us_number:
                    # Keep only if in high-confidence source
                    if num.source_type in self.HIGH_CONFIDENCE_SOURCES:
                        kept.append(num)
                    else:
                        removed.append((num.raw, f"US number for non-US business ({business_region})"))
                        self.stats['removed_region'] += 1
                else:
                    kept.append(num)
        else:
            # US business, keep all
            kept = numbers
        
        return kept, removed
    
    def _score_confidence(self, numbers: List[PhoneNumber]) -> Tuple[List[PhoneNumber], List[Tuple[str, str]]]:
        """Score numbers by confidence and filter low scores"""
        # Base scores by source
        base_scores = {
            SourceType.TEL_LINK: 1.0,
            SourceType.SCHEMA_ORG: 0.95,
            SourceType.FOOTER: 0.9,
            SourceType.CONTACT_PAGE: 0.85,
            SourceType.ABOUT_PAGE: 0.8,
            SourceType.VISIBLE_HTML: 0.6,
            SourceType.HEADER: 0.5,
            SourceType.SIDEBAR: 0.4,
        }
        
        kept = []
        removed = []
        
        for num in numbers:
            # Assign base score
            score = base_scores.get(num.source_type, 0.3)
            
            # Add context bonus (already added in context analysis)
            score += num.confidence
            
            # Check if toll-free (slight penalty)
            prefix = num.normalized[:3] if len(num.normalized) >= 3 else ''
            if prefix in self.TOLL_FREE_PREFIXES:
                score -= 0.1
            else:
                score += 0.05
            
            num.confidence = min(1.0, score)
            
            # Filter by threshold
            if num.confidence >= 0.7:
                kept.append(num)
            else:
                removed.append((num.raw, f"Low confidence score: {num.confidence:.2f}"))
                self.stats['removed_confidence'] += 1
        
        return kept, removed
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Strip all non-digits from phone number"""
        return re.sub(r'\D', '', phone)
    
    @staticmethod
    def to_canonical(normalized: str) -> str:
        """
        Convert normalized phone to canonical form
        10 digits → +1XXXXXXXXXX
        11 digits starting with 1 → +1XXXXXXXXXX
        """
        if len(normalized) == 10:
            return f"+1{normalized}"
        elif len(normalized) == 11 and normalized[0] == '1':
            return f"+{normalized}"
        else:
            return f"+{normalized}"
    
    @staticmethod
    def detect_source_type(html_element: str, source_url: str, page_url: str) -> SourceType:
        """
        Detect source type from HTML element and URLs
        
        Args:
            html_element: HTML element containing the number
            source_url: URL of the resource (for scripts, CDN)
            page_url: URL of the page
            
        Returns:
            SourceType enum
        """
        html_lower = html_element.lower()
        url_lower = source_url.lower() if source_url else ''
        page_lower = page_url.lower() if page_url else ''
        
        # Check for tel: link
        if 'href="tel:' in html_lower or "href='tel:" in html_lower:
            return SourceType.TEL_LINK
        
        # Check for Schema.org
        if 'application/ld+json' in html_lower or 'itemprop="telephone"' in html_lower:
            return SourceType.SCHEMA_ORG
        
        # Check for footer
        if '<footer' in html_lower or 'class="footer' in html_lower or 'id="footer' in html_lower:
            return SourceType.FOOTER
        
        # Check for contact page
        if '/contact' in page_lower or 'contact-us' in page_lower:
            return SourceType.CONTACT_PAGE
        
        # Check for about page
        if '/about' in page_lower or 'about-us' in page_lower:
            return SourceType.ABOUT_PAGE
        
        # Check for script
        if '<script' in html_lower or '.js' in url_lower:
            return SourceType.SCRIPT
        
        # Check for CDN
        if 'cdn.' in url_lower or '/cdn/' in url_lower:
            return SourceType.CDN
        
        # Check for checkout
        if 'checkout' in url_lower or 'cart' in url_lower or 'payment' in url_lower:
            return SourceType.CHECKOUT
        
        # Check for comment
        if '<!--' in html_element or '/*' in html_element or '//' in html_element:
            return SourceType.COMMENT
        
        # Check for header
        if '<header' in html_lower or 'class="header' in html_lower:
            return SourceType.HEADER
        
        # Check for sidebar
        if 'sidebar' in html_lower or 'widget' in html_lower:
            return SourceType.SIDEBAR
        
        # Default to visible HTML
        return SourceType.VISIBLE_HTML


def create_phone_cleaner(fast_mode: bool = True) -> PhoneCleaningPipeline:
    """
    Factory function to create phone cleaning pipeline
    
    Args:
        fast_mode: If True, use fast mode (60ms). If False, use accuracy mode (130ms)
        
    Returns:
        PhoneCleaningPipeline instance
    """
    return PhoneCleaningPipeline(fast_mode=fast_mode)
