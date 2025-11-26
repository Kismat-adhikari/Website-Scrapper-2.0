#!/usr/bin/env python3
"""
Apify Actor - Web Contact Scraper
Extracts emails, phones, company info, addresses, and social links from websites
"""

import asyncio
import logging
from typing import List, Dict, Any
from apify import Actor

# Import scraper modules
from async_scraper import scrape_url_async_wrapper, scrape_urls_batch_wrapper
from scraper import ProxyManager
from advanced_scraper_features import CompanyInfoExtractor, AddressExtractor
from context_extractor import ContextExtractor
from schema_extractor import SchemaExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main Apify actor entry point"""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f'Actor input: {actor_input}')
        
        # Parse URLs from input
        urls = []
        
        # Support both startUrls (Apify format) and urls (simple list)
        start_urls = actor_input.get('startUrls', [])
        simple_urls = actor_input.get('urls', [])
        
        # Parse startUrls format
        for item in start_urls:
            if isinstance(item, dict):
                url = item.get('url')
                if url:
                    urls.append(url)
            elif isinstance(item, str):
                urls.append(item)
        
        # Add simple URLs
        urls.extend(simple_urls)
        
        if not urls:
            Actor.log.error('No URLs provided in input')
            return
        
        Actor.log.info(f'Starting scrape for {len(urls)} URLs')
        
        # Get options
        fast_mode = actor_input.get('fastMode', True)
        max_pages = actor_input.get('maxPages', 1)
        enable_validation = actor_input.get('enableValidation', False)
        max_concurrency = actor_input.get('maxConcurrency', 5)
        block_keywords = actor_input.get('blockKeywords', '')
        
        # Setup proxy (Apify proxy if configured)
        proxy_config = actor_input.get('proxyConfiguration')
        proxy_url = None
        
        if proxy_config and proxy_config.get('useApifyProxy'):
            try:
                apify_proxy = await Actor.create_proxy_configuration(
                    actor_proxy_input=proxy_config
                )
                proxy_url = await apify_proxy.new_url()
                Actor.log.info(f'Using Apify proxy')
            except Exception as e:
                Actor.log.warning(f'Failed to setup Apify proxy: {e}')
        
        # Initialize extractors
        company_extractor = CompanyInfoExtractor()
        address_extractor = AddressExtractor()
        context_extractor = ContextExtractor()
        schema_extractor = SchemaExtractor()
        
        # Process URLs in batches for memory efficiency
        batch_size = max_concurrency
        total_processed = 0
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            Actor.log.info(f'Processing batch {i//batch_size + 1}: {len(batch)} URLs')
            
            # Scrape batch
            try:
                results = scrape_urls_batch_wrapper(
                    batch,
                    proxy_manager=None,  # Using Apify proxy instead
                    fast_mode=fast_mode
                )
                
                # Process and save results
                for result in results:
                    try:
                        # Extract additional info if HTML available
                        company_name = None
                        company_description = None
                        addresses = []
                        
                        if hasattr(result, 'html') and result.html:
                            try:
                                # Extract company info
                                company_name = company_extractor.extract_company_name(result.html)
                                company_description = company_extractor.extract_company_description(result.html)
                                
                                # Extract addresses using multiple methods
                                schema_data = schema_extractor.extract_all(result.html)
                                if schema_data and 'address' in schema_data:
                                    addr_data = schema_data['address']
                                    if isinstance(addr_data, dict):
                                        addr_str = f"{addr_data.get('streetAddress', '')}, {addr_data.get('addressLocality', '')}, {addr_data.get('addressRegion', '')} {addr_data.get('postalCode', '')}".strip(', ')
                                        if addr_str:
                                            addresses.append(addr_str)
                                
                                context_addresses = context_extractor.extract_addresses_with_context(result.html)
                                addresses.extend(context_addresses)
                                
                                pattern_addresses = address_extractor.extract_addresses(result.html)
                                addresses.extend([str(addr) for addr in pattern_addresses])
                                
                                # Deduplicate addresses
                                addresses = list(set(addresses))
                                
                            except Exception as e:
                                Actor.log.warning(f'Error extracting additional info for {result.url}: {e}')
                        
                        # Get emails and phones
                        emails = list(result.emails) if hasattr(result, 'emails') else []
                        phones = list(result.phones) if hasattr(result, 'phones') else []
                        
                        # Apply keyword blocking
                        if block_keywords:
                            keywords = [kw.strip().lower() for kw in block_keywords.split(',') if kw.strip()]
                            emails = [e for e in emails if not any(kw in e.lower() for kw in keywords)]
                            phones = [p for p in phones if not any(kw in p.lower() for kw in keywords)]
                        
                        # Prepare data for dataset
                        data = {
                            'url': result.url,
                            'status': result.status,
                            'emails': emails,
                            'phones': phones,
                            'company_name': company_name,
                            'company_description': company_description,
                            'addresses': addresses,
                            'social_links': result.social_links if hasattr(result, 'social_links') else {},
                            'confidence_score': round(result.confidence_score, 2) if hasattr(result, 'confidence_score') else 0,
                            'fetch_time': round(result.fetch_time, 2) if hasattr(result, 'fetch_time') else 0,
                            'pages_scanned': getattr(result, 'pages_scanned', 1),
                            'leadership_count': getattr(result, 'leadership_count', 0)
                        }
                        
                        # Push to dataset
                        await Actor.push_data(data)
                        total_processed += 1
                        
                        Actor.log.info(f'✓ Processed {result.url}: {len(emails)} emails, {len(phones)} phones')
                        
                    except Exception as e:
                        Actor.log.error(f'Error processing result for {result.url}: {e}')
                        # Push failed result
                        await Actor.push_data({
                            'url': result.url if hasattr(result, 'url') else 'unknown',
                            'status': 'failed',
                            'error': str(e),
                            'emails': [],
                            'phones': [],
                            'confidence_score': 0
                        })
                
                # Update progress
                progress = (total_processed / len(urls)) * 100
                Actor.log.info(f'Progress: {progress:.1f}% ({total_processed}/{len(urls)})')
                
                # Memory cleanup after each batch
                import gc
                gc.collect()
                
            except Exception as e:
                Actor.log.error(f'Error processing batch: {e}')
        
        Actor.log.info(f'✅ Scraping complete! Processed {total_processed}/{len(urls)} URLs')


if __name__ == '__main__':
    asyncio.run(main())
