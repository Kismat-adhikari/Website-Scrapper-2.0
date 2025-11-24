"""
Improved extraction for address and company name
Replaces the broken extraction in advanced_scraper_features.py
"""

import re
from typing import List, Optional
from bs4 import BeautifulSoup


class ImprovedAddressExtractor:
    """Improved address extraction with flexible patterns"""
    
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    def extract_addresses(self, html: str) -> List[str]:
        """Extract addresses from HTML with flexible patterns"""
        addresses = []
        seen = set()
        
        # Clean HTML
        html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Pattern 1: Full address with street, city, state, zip
        pattern1 = r'(\d+\s+[\w\s&.,#-]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Pkwy|Parkway|Terrace|Ter|Circle|Cir|Square|Sq|Apt|Suite|Ste)\.?)\s*,?\s*([A-Za-z\s]+),?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        
        for match in re.finditer(pattern1, html_clean):
            addr = match.group(0).strip()
            if addr not in seen and self._validate_address(addr):
                addresses.append(addr)
                seen.add(addr)
        
        # Pattern 2: City, State, Zip (less specific)
        pattern2 = r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        
        for match in re.finditer(pattern2, html_clean):
            addr = match.group(0).strip()
            if addr not in seen and len(addr) > 10:  # Avoid short matches
                if self._validate_city_state_zip(addr):
                    addresses.append(addr)
                    seen.add(addr)
        
        return addresses[:5]  # Return top 5 addresses
    
    def _validate_address(self, addr: str) -> bool:
        """Validate address has proper format"""
        # Must have state abbreviation
        state_match = re.search(r'\b([A-Z]{2})\b', addr)
        if not state_match:
            return False
        
        state = state_match.group(1)
        if state not in self.US_STATES:
            return False
        
        # Must have zip code
        if not re.search(r'\d{5}', addr):
            return False
        
        return True
    
    def _validate_city_state_zip(self, addr: str) -> bool:
        """Validate city, state, zip format"""
        parts = addr.split(',')
        if len(parts) < 2:
            return False
        
        # Check for state and zip
        state_zip = parts[-1].strip()
        state_match = re.search(r'([A-Z]{2})\s+(\d{5})', state_zip)
        
        if not state_match:
            return False
        
        state = state_match.group(1)
        return state in self.US_STATES


class ImprovedCompanyExtractor:
    """Improved company name extraction"""
    
    def extract_company_name(self, html: str) -> Optional[str]:
        """Extract company name from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try title tag first
        title = soup.find('title')
        if title and title.string:
            name = title.string.strip()
            name = self._clean_company_name(name)
            if len(name) > 2:
                return name
        
        # Try og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            name = og_title.get('content').strip()
            name = self._clean_company_name(name)
            if len(name) > 2:
                return name
        
        # Try h1 tag
        h1 = soup.find('h1')
        if h1 and h1.string:
            name = h1.string.strip()
            if len(name) > 2 and len(name) < 100:
                return name
        
        # Try meta description as fallback
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = meta_desc.get('content').strip()
            # Extract first part before dash or pipe
            name = re.split(r'[-|]', content)[0].strip()
            if len(name) > 2 and len(name) < 100:
                return name
        
        return None
    
    def _clean_company_name(self, name: str) -> str:
        """Clean company name by removing common suffixes"""
        # Remove common suffixes
        name = re.sub(r'\s*[-|]\s*(Home|Website|Official|Site|Web|Online|Portal)$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\|\s*.*$', '', name)  # Remove everything after pipe
        name = re.sub(r'\s*-\s*.*$', '', name)   # Remove everything after dash
        
        return name.strip()
