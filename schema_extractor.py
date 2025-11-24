"""
Schema.org Extractor - Phase 5 Implementation
Extracts structured data from JSON-LD, Microdata, and RDFa
"""

import json
import logging
import re
from typing import Dict, List, Set, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extract structured data from Schema.org markup"""
    
    def __init__(self):
        self.supported_types = [
            'Organization', 'LocalBusiness', 'Restaurant', 'Store',
            'Corporation', 'Person', 'ContactPoint'
        ]
    
    def extract_all(self, html: str) -> Dict:
        """
        Extract all structured data from HTML
        
        Returns:
            Dict with emails, phones, company_name, address, etc.
        """
        result = {
            'emails': set(),
            'phones': set(),
            'company_name': None,
            'address': None,
            'social_links': {},
            'description': None
        }
        
        # Try JSON-LD first (most reliable)
        jsonld_data = self.extract_jsonld(html)
        if jsonld_data:
            self._merge_data(result, jsonld_data)
        
        # Try Microdata
        microdata = self.extract_microdata(html)
        if microdata:
            self._merge_data(result, microdata)
        
        # Try Open Graph tags
        og_data = self.extract_opengraph(html)
        if og_data:
            self._merge_data(result, og_data)
        
        return result
    
    def extract_jsonld(self, html: str) -> Optional[Dict]:
        """Extract data from JSON-LD scripts"""
        soup = BeautifulSoup(html, 'html.parser')
        result = {
            'emails': set(),
            'phones': set(),
            'company_name': None,
            'address': None,
            'social_links': {},
            'description': None
        }
        
        # Find all JSON-LD script tags
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Handle @graph format
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        self._extract_from_schema(item, result)
                # Handle array format
                elif isinstance(data, list):
                    for item in data:
                        self._extract_from_schema(item, result)
                # Handle single object
                elif isinstance(data, dict):
                    self._extract_from_schema(data, result)
                    
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")
                continue
            except Exception as e:
                logger.debug(f"Error extracting JSON-LD: {e}")
                continue
        
        return result if any(result.values()) else None
    
    def _extract_from_schema(self, data: Dict, result: Dict):
        """Extract data from a Schema.org object"""
        if not isinstance(data, dict):
            return
        
        schema_type = data.get('@type', '')
        
        # Extract name
        if 'name' in data and not result['company_name']:
            result['company_name'] = data['name']
        
        # Extract description
        if 'description' in data and not result['description']:
            result['description'] = data['description']
        
        # Extract email
        if 'email' in data:
            email = data['email']
            if isinstance(email, str):
                # Remove mailto: prefix
                email = email.replace('mailto:', '')
                result['emails'].add(email)
        
        # Extract telephone
        if 'telephone' in data:
            phone = data['telephone']
            if isinstance(phone, str):
                result['phones'].add(phone)
        
        # Extract from contactPoint
        if 'contactPoint' in data:
            contact = data['contactPoint']
            if isinstance(contact, dict):
                if 'email' in contact:
                    result['emails'].add(contact['email'].replace('mailto:', ''))
                if 'telephone' in contact:
                    result['phones'].add(contact['telephone'])
            elif isinstance(contact, list):
                for c in contact:
                    if isinstance(c, dict):
                        if 'email' in c:
                            result['emails'].add(c['email'].replace('mailto:', ''))
                        if 'telephone' in c:
                            result['phones'].add(c['telephone'])
        
        # Extract address
        if 'address' in data and not result['address']:
            address = data['address']
            if isinstance(address, dict):
                # Format address from components
                parts = []
                for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode']:
                    if key in address:
                        parts.append(str(address[key]))
                if parts:
                    result['address'] = ', '.join(parts)
            elif isinstance(address, str):
                result['address'] = address
        
        # Extract social media links
        for key in ['sameAs', 'url']:
            if key in data:
                urls = data[key]
                if isinstance(urls, str):
                    urls = [urls]
                if isinstance(urls, list):
                    for url in urls:
                        if isinstance(url, str):
                            self._categorize_social_link(url, result['social_links'])
    
    def extract_microdata(self, html: str) -> Optional[Dict]:
        """Extract data from Microdata attributes"""
        soup = BeautifulSoup(html, 'html.parser')
        result = {
            'emails': set(),
            'phones': set(),
            'company_name': None,
            'address': None,
            'social_links': {},
            'description': None
        }
        
        # Find elements with itemtype
        items = soup.find_all(attrs={'itemtype': True})
        
        for item in items:
            itemtype = item.get('itemtype', '')
            
            # Check if it's a relevant schema type
            if not any(t in itemtype for t in self.supported_types):
                continue
            
            # Extract properties
            props = item.find_all(attrs={'itemprop': True})
            
            for prop in props:
                itemprop = prop.get('itemprop', '')
                
                if itemprop == 'name' and not result['company_name']:
                    result['company_name'] = prop.get_text(strip=True)
                
                elif itemprop == 'description' and not result['description']:
                    result['description'] = prop.get_text(strip=True)
                
                elif itemprop == 'email':
                    email = prop.get('href', '') or prop.get_text(strip=True)
                    email = email.replace('mailto:', '')
                    if email:
                        result['emails'].add(email)
                
                elif itemprop == 'telephone':
                    phone = prop.get('href', '') or prop.get_text(strip=True)
                    phone = phone.replace('tel:', '')
                    if phone:
                        result['phones'].add(phone)
                
                elif itemprop == 'address':
                    address = prop.get_text(strip=True)
                    if address and not result['address']:
                        result['address'] = address
        
        return result if any(result.values()) else None
    
    def extract_opengraph(self, html: str) -> Optional[Dict]:
        """Extract data from Open Graph meta tags"""
        soup = BeautifulSoup(html, 'html.parser')
        result = {
            'emails': set(),
            'phones': set(),
            'company_name': None,
            'address': None,
            'social_links': {},
            'description': None
        }
        
        # Find Open Graph meta tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        
        for tag in og_tags:
            prop = tag.get('property', '')
            content = tag.get('content', '')
            
            if prop == 'og:site_name' and not result['company_name']:
                result['company_name'] = content
            
            elif prop == 'og:description' and not result['description']:
                result['description'] = content
            
            elif prop == 'og:email':
                result['emails'].add(content.replace('mailto:', ''))
            
            elif prop == 'og:phone_number':
                result['phones'].add(content.replace('tel:', ''))
        
        return result if any(result.values()) else None
    
    def _categorize_social_link(self, url: str, social_links: Dict):
        """Categorize a URL as a social media link"""
        url_lower = url.lower()
        
        platforms = {
            'facebook': ['facebook.com', 'fb.com'],
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'instagram': ['instagram.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'tiktok': ['tiktok.com'],
            'pinterest': ['pinterest.com']
        }
        
        for platform, domains in platforms.items():
            if any(domain in url_lower for domain in domains):
                if platform not in social_links:
                    social_links[platform] = set()
                social_links[platform].add(url)
                break
    
    def _merge_data(self, target: Dict, source: Dict):
        """Merge source data into target"""
        # Merge sets
        for key in ['emails', 'phones']:
            if key in source and source[key]:
                target[key].update(source[key])
        
        # Merge single values (prefer non-None)
        for key in ['company_name', 'address', 'description']:
            if key in source and source[key] and not target[key]:
                target[key] = source[key]
        
        # Merge social links
        if 'social_links' in source:
            for platform, links in source['social_links'].items():
                if platform not in target['social_links']:
                    target['social_links'][platform] = set()
                target['social_links'][platform].update(links)


# Global instance
_schema_extractor: Optional[SchemaExtractor] = None


def get_schema_extractor() -> SchemaExtractor:
    """Get or create the global schema extractor"""
    global _schema_extractor
    
    if _schema_extractor is None:
        _schema_extractor = SchemaExtractor()
    
    return _schema_extractor
