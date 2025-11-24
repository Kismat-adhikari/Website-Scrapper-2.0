"""
Role-Based Email Detection
Identifies and filters generic/role-based emails vs personal emails.
Helps find real decision-makers instead of generic inboxes.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
role_logger = logging.getLogger('role_detector')
role_logger.setLevel(logging.DEBUG)


class EmailType(Enum):
    """Classification of email types"""
    PERSONAL = "personal"  # firstname.lastname@, john.smith@, etc
    ROLE_BASED = "role_based"  # support@, info@, sales@, etc
    GENERIC = "generic"  # noreply@, no-reply@, automated@, etc
    UNKNOWN = "unknown"


@dataclass
class RoleDetectionResult:
    """Result of role-based email detection"""
    email: str
    email_type: EmailType
    role: Optional[str]  # The detected role (support, sales, etc)
    confidence: float  # 0.0-1.0
    is_personal: bool  # True if likely a real person
    is_generic: bool  # True if generic/automated
    local_part: str  # Part before @
    domain: str  # Part after @


class RoleDetector:
    """Detects role-based and generic emails"""
    
    # Generic/automated email patterns
    GENERIC_PATTERNS = {
        'noreply': r'^no-?reply',
        'donotreply': r'^do-?not-?reply',
        'notification': r'^notification',
        'automated': r'^automated',
        'mailer': r'^mailer-?daemon',
        'postmaster': r'^postmaster',
        'webmaster': r'^webmaster',
        'hostmaster': r'^hostmaster',
        'admin': r'^admin',
        'root': r'^root',
        'system': r'^system',
        'noreply_alt': r'noreply',
        'bounce': r'^bounce',
        'unsubscribe': r'^unsubscribe',
        'newsletter': r'^newsletter',
        'alert': r'^alert',
        'notification_alt': r'notification',
        'automated_alt': r'automated',
    }
    
    # Role-based email patterns (generic roles, not personal)
    ROLE_PATTERNS = {
        'support': r'^support',
        'help': r'^help',
        'contact': r'^contact',
        'info': r'^info',
        'sales': r'^sales',
        'billing': r'^billing',
        'accounting': r'^accounting',
        'finance': r'^finance',
        'hr': r'^hr',
        'human.?resources': r'^human.?resources',
        'recruitment': r'^recruitment',
        'careers': r'^careers',
        'jobs': r'^jobs',
        'press': r'^press',
        'media': r'^media',
        'marketing': r'^marketing',
        'business': r'^business',
        'partnerships': r'^partnerships',
        'legal': r'^legal',
        'compliance': r'^compliance',
        'security': r'^security',
        'abuse': r'^abuse',
        'feedback': r'^feedback',
        'hello': r'^hello',
        'team': r'^team',
        'office': r'^office',
        'reception': r'^reception',
        'general': r'^general',
        'inquiries': r'^inquiries',
        'inquiry': r'^inquiry',
        'request': r'^request',
        'service': r'^service',
        'customer': r'^customer',
        'client': r'^client',
        'orders': r'^orders',
        'shipping': r'^shipping',
        'delivery': r'^delivery',
        'returns': r'^returns',
        'complaints': r'^complaints',
        'quality': r'^quality',
        'operations': r'^operations',
        'logistics': r'^logistics',
        'procurement': r'^procurement',
        'vendor': r'^vendor',
        'supplier': r'^supplier',
        'events': r'^events',
        'conference': r'^conference',
        'webinar': r'^webinar',
        'training': r'^training',
        'education': r'^education',
        'development': r'^development',
        'tech': r'^tech',
        'it': r'^it',
        'infrastructure': r'^infrastructure',
        'devops': r'^devops',
        'engineering': r'^engineering',
        'product': r'^product',
        'design': r'^design',
        'ux': r'^ux',
        'ui': r'^ui',
        'creative': r'^creative',
        'content': r'^content',
        'social': r'^social',
        'community': r'^community',
        'partnerships': r'^partnerships',
        'business.?dev': r'^business.?dev',
    }
    
    # Personal email patterns (likely real people)
    PERSONAL_PATTERNS = {
        'firstname_lastname': r'^[a-z]+\.[a-z]+$',  # john.smith
        'firstname_lastname_alt': r'^[a-z]+_[a-z]+$',  # john_smith
        'firstname_lastname_num': r'^[a-z]+\.[a-z]+\d+$',  # john.smith1
        'firstlast': r'^[a-z]{2,}[a-z]{2,}$',  # johnsmith (2+ chars each)
        'first_initial_last': r'^[a-z]\.[a-z]+$',  # j.smith
        'first_last_initial': r'^[a-z]+\.[a-z]$',  # john.s
        'firstname_num': r'^[a-z]+\d{1,3}$',  # john123
        'firstname_year': r'^[a-z]+\d{4}$',  # john2024
    }
    
    def __init__(self):
        """Initialize role detector"""
        self.generic_compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.GENERIC_PATTERNS.items()}
        self.role_compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.ROLE_PATTERNS.items()}
        self.personal_compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.PERSONAL_PATTERNS.items()}
        role_logger.info("Initialized RoleDetector with 60+ patterns")
    
    def detect(self, email: str) -> RoleDetectionResult:
        """Detect email type and role"""
        email = email.strip().lower()
        
        if '@' not in email:
            return RoleDetectionResult(
                email=email,
                email_type=EmailType.UNKNOWN,
                role=None,
                confidence=0.0,
                is_personal=False,
                is_generic=False,
                local_part=email,
                domain=""
            )
        
        local_part, domain = email.split('@', 1)
        
        # Check generic patterns first (highest priority)
        for role, pattern in self.generic_compiled.items():
            if pattern.search(local_part):
                return RoleDetectionResult(
                    email=email,
                    email_type=EmailType.GENERIC,
                    role=role,
                    confidence=0.95,
                    is_personal=False,
                    is_generic=True,
                    local_part=local_part,
                    domain=domain
                )
        
        # Check role-based patterns
        for role, pattern in self.role_compiled.items():
            if pattern.search(local_part):
                return RoleDetectionResult(
                    email=email,
                    email_type=EmailType.ROLE_BASED,
                    role=role,
                    confidence=0.85,
                    is_personal=False,
                    is_generic=False,
                    local_part=local_part,
                    domain=domain
                )
        
        # Check personal patterns
        personal_matches = 0
        for pattern_name, pattern in self.personal_compiled.items():
            if pattern.search(local_part):
                personal_matches += 1
        
        if personal_matches > 0:
            confidence = min(0.95, 0.7 + (personal_matches * 0.1))
            return RoleDetectionResult(
                email=email,
                email_type=EmailType.PERSONAL,
                role=None,
                confidence=confidence,
                is_personal=True,
                is_generic=False,
                local_part=local_part,
                domain=domain
            )
        
        # Default to unknown
        return RoleDetectionResult(
            email=email,
            email_type=EmailType.UNKNOWN,
            role=None,
            confidence=0.5,
            is_personal=False,
            is_generic=False,
            local_part=local_part,
            domain=domain
        )
    
    def detect_batch(self, emails: List[str]) -> List[RoleDetectionResult]:
        """Detect multiple emails"""
        return [self.detect(email) for email in emails]
    
    def filter_personal_only(self, emails: List[str]) -> List[str]:
        """Filter to only personal emails"""
        results = self.detect_batch(emails)
        return [r.email for r in results if r.is_personal]
    
    def filter_exclude_generic(self, emails: List[str]) -> List[str]:
        """Filter out generic/automated emails"""
        results = self.detect_batch(emails)
        return [r.email for r in results if not r.is_generic]
    
    def filter_exclude_roles(self, emails: List[str]) -> List[str]:
        """Filter out role-based emails"""
        results = self.detect_batch(emails)
        return [r.email for r in results if r.email_type != EmailType.ROLE_BASED]
    
    def categorize(self, emails: List[str]) -> Dict[str, List[str]]:
        """Categorize emails by type"""
        results = self.detect_batch(emails)
        categorized = {
            'personal': [],
            'role_based': [],
            'generic': [],
            'unknown': []
        }
        
        for result in results:
            if result.email_type == EmailType.PERSONAL:
                categorized['personal'].append(result.email)
            elif result.email_type == EmailType.ROLE_BASED:
                categorized['role_based'].append(result.email)
            elif result.email_type == EmailType.GENERIC:
                categorized['generic'].append(result.email)
            else:
                categorized['unknown'].append(result.email)
        
        return categorized
    
    def get_summary(self, emails: List[str]) -> Dict:
        """Get summary statistics"""
        results = self.detect_batch(emails)
        
        personal_count = sum(1 for r in results if r.is_personal)
        generic_count = sum(1 for r in results if r.is_generic)
        role_count = sum(1 for r in results if r.email_type == EmailType.ROLE_BASED)
        unknown_count = sum(1 for r in results if r.email_type == EmailType.UNKNOWN)
        
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
        
        return {
            'total': len(results),
            'personal': personal_count,
            'role_based': role_count,
            'generic': generic_count,
            'unknown': unknown_count,
            'personal_percentage': round((personal_count / len(results) * 100), 1) if results else 0,
            'average_confidence': round(avg_confidence, 2),
            'quality_score': round((personal_count / len(results)), 2) if results else 0  # Higher = better
        }


def create_role_detector() -> RoleDetector:
    """Factory function to create role detector"""
    return RoleDetector()
