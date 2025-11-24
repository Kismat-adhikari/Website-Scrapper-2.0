"""
Context-Aware Extractor - Phase 5 Implementation
Extracts data based on surrounding context and keywords
"""

import re
import logging
from typing import Set, List, Tuple
from bs4 import BeautifulSoup, NavigableString

logger = logging.getLogger(__name__)


class ContextExtractor:
    """Extract data using context clues"""
    
    # Keywords that indicate contact information nearby
    CONTACT_KEYWORDS = [
        'contact', 'email', 'reach', 'hello', 'info', 'support',
        'get in touch', 'write to', 'send us', 'message us'
    ]
    
    PHONE_KEYWORDS = [
        'call', 'phone', 'tel', 'telephone', 'mobile', 'cell',
        'call us', 'ring us', 'dial', 'hotline'
    ]
    
    ADDRESS_KEYWORDS = [
        'address', 'location', 'visit', 'find us', 'directions',
        'office', 'headquarters', 'hq', 'based in'
    ]
    
    def __init__(self):
        # Pre-compile regex patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b')
    
    def extract_emails_with_context(self, html: str) -> Set[str]:
        """Extract emails prioritizing those near contact keywords"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Priority 1: Emails in contact sections
        contact_emails = self._extract_from_sections(soup, self.CONTACT_KEYWORDS, self.email_pattern)
        
        # Priority 2: Emails in mailto links
        mailto_emails = set()
        for link in soup.find_all('a', href=re.compile(r'^mailto:', re.I)):
            email = link.get('href', '').replace('mailto:', '').split('?')[0]
            if email and '@' in email:
                mailto_emails.add(email.lower())
        
        # Priority 3: Emails in text near contact keywords
        text_emails = self._extract_near_keywords(soup, self.CONTACT_KEYWORDS, self.email_pattern)
        
        # Combine with priority order
        all_emails = list(contact_emails) + list(mailto_emails) + list(text_emails)
        
        # Remove duplicates while preserving order
        seen = set()
        ordered_emails = []
        for email in all_emails:
            email_lower = email.lower()
            if email_lower not in seen:
                seen.add(email_lower)
                ordered_emails.append(email)
        
        return set(ordered_emails)
    
    def extract_phones_with_context(self, html: str) -> Set[str]:
        """Extract phones prioritizing those near phone keywords"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Priority 1: Phones in contact sections
        contact_phones = self._extract_from_sections(soup, self.PHONE_KEYWORDS, self.phone_pattern)
        
        # Priority 2: Phones in tel: links
        tel_phones = set()
        for link in soup.find_all('a', href=re.compile(r'^tel:', re.I)):
            phone = link.get('href', '').replace('tel:', '').replace('+1', '')
            # Clean and format
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 10:
                tel_phones.add(f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}")
        
        # Priority 3: Phones in text near phone keywords
        text_phones = self._extract_near_keywords(soup, self.PHONE_KEYWORDS, self.phone_pattern)
        
        # Format phones
        formatted_phones = set()
        for phone_match in list(contact_phones) + list(tel_phones) + list(text_phones):
            if isinstance(phone_match, tuple):
                # From regex match groups
                formatted = f"{phone_match[0]}-{phone_match[1]}-{phone_match[2]}"
                formatted_phones.add(formatted)
            else:
                formatted_phones.add(phone_match)
        
        return formatted_phones
    
    def extract_addresses_with_context(self, html: str) -> List[str]:
        """Extract addresses using context clues"""
        soup = BeautifulSoup(html, 'html.parser')
        addresses = []
        
        # Find sections with address keywords
        for keyword in self.ADDRESS_KEYWORDS:
            # Find elements containing the keyword
            elements = soup.find_all(string=re.compile(keyword, re.I))
            
            for element in elements:
                # Get parent element
                parent = element.parent
                if parent:
                    # Look for address-like text in parent or siblings
                    text = parent.get_text(strip=True)
                    
                    # Simple address pattern (street number + street name + city/state/zip)
                    address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way)[,\s]+[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5}'
                    
                    matches = re.findall(address_pattern, text, re.I)
                    addresses.extend(matches)
        
        # Remove duplicates
        return list(set(addresses))
    
    def _extract_from_sections(self, soup: BeautifulSoup, keywords: List[str], pattern: re.Pattern) -> Set:
        """Extract data from sections containing keywords"""
        results = set()
        
        # Find sections with keywords in id or class
        for keyword in keywords:
            # Find by id
            sections = soup.find_all(id=re.compile(keyword, re.I))
            # Find by class
            sections.extend(soup.find_all(class_=re.compile(keyword, re.I)))
            
            for section in sections:
                text = section.get_text()
                matches = pattern.findall(text)
                results.update(matches)
        
        return results
    
    def _extract_near_keywords(self, soup: BeautifulSoup, keywords: List[str], pattern: re.Pattern, 
                               window: int = 200) -> Set:
        """Extract data near keywords (within window characters)"""
        results = set()
        text = soup.get_text()
        
        for keyword in keywords:
            # Find keyword positions
            for match in re.finditer(keyword, text, re.I):
                start = max(0, match.start() - window)
                end = min(len(text), match.end() + window)
                context = text[start:end]
                
                # Extract from context
                matches = pattern.findall(context)
                results.update(matches)
        
        return results
    
    def get_contact_section_text(self, html: str) -> str:
        """Get text from contact-related sections"""
        soup = BeautifulSoup(html, 'html.parser')
        contact_text = []
        
        # Find contact sections
        for keyword in self.CONTACT_KEYWORDS:
            sections = soup.find_all(id=re.compile(keyword, re.I))
            sections.extend(soup.find_all(class_=re.compile(keyword, re.I)))
            
            for section in sections:
                contact_text.append(section.get_text(strip=True))
        
        return ' '.join(contact_text)
    
    def score_email_quality(self, email: str, html: str) -> float:
        """
        Score email quality based on context
        
        Returns:
            Float between 0 and 1 (higher = better quality)
        """
        score = 0.5  # Base score
        
        email_lower = email.lower()
        html_lower = html.lower()
        
        # Bonus for being in mailto link
        if f'mailto:{email_lower}' in html_lower:
            score += 0.2
        
        # Bonus for being near contact keywords
        for keyword in self.CONTACT_KEYWORDS:
            if keyword in html_lower:
                # Check if email is near keyword
                keyword_pos = html_lower.find(keyword)
                email_pos = html_lower.find(email_lower)
                if abs(keyword_pos - email_pos) < 500:
                    score += 0.1
                    break
        
        # Bonus for common contact email patterns
        if any(prefix in email_lower for prefix in ['contact', 'info', 'hello', 'support', 'sales']):
            score += 0.15
        
        # Penalty for generic/spam patterns
        if any(pattern in email_lower for pattern in ['noreply', 'no-reply', 'donotreply']):
            score -= 0.3
        
        return min(1.0, max(0.0, score))


# Global instance
_context_extractor = None


def get_context_extractor() -> ContextExtractor:
    """Get or create the global context extractor"""
    global _context_extractor
    
    if _context_extractor is None:
        _context_extractor = ContextExtractor()
    
    return _context_extractor
