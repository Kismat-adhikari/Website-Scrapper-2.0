"""
Advanced Scraper Features - Integration Examples
Demonstrates multi-page scraping, parallel processing, and enhanced validation
"""

import logging
from advanced_scraper_features import (
    AdvancedScraperPipeline,
    EnhancedScraperResult,
    Address,
    PageType,
    MultiPageScraper,
    AddressExtractor,
    DataQualityScorer,
    ParallelScraper,
    AdvancedRetryStrategy,
    CompanyInfoExtractor
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# Example 1: Address Extraction
# ============================================================================

def example_address_extraction():
    """Extract addresses from HTML"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Address Extraction")
    print("="*70)
    
    extractor = AddressExtractor()
    
    # Sample HTML with addresses
    html = """
    <html>
        <body>
            <p>Our office is located at 123 Main St, San Francisco, CA 94105</p>
            <p>Contact us at 456 Oak Ave, New York, NY 10001</p>
            <p>P.O. Box 789, Los Angeles, CA 90001</p>
        </body>
    </html>
    """
    
    addresses = extractor.extract_addresses(html)
    
    print(f"\nExtracted {len(addresses)} addresses:")
    for i, addr in enumerate(addresses, 1):
        print(f"\n  Address {i}:")
        print(f"    Street: {addr.street}")
        print(f"    City: {addr.city}")
        print(f"    State: {addr.state}")
        print(f"    Postal Code: {addr.postal_code}")
        print(f"    Full: {addr.full_address}")
        print(f"    Confidence: {addr.confidence_score:.2f}")


# ============================================================================
# Example 2: Multi-Page Discovery
# ============================================================================

def example_multi_page_discovery():
    """Discover related pages on website"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-Page Discovery")
    print("="*70)
    
    scraper = MultiPageScraper()
    
    # Sample HTML with links
    html = """
    <html>
        <body>
            <a href="/contact">Contact Us</a>
            <a href="/about-us">About Us</a>
            <a href="/team">Our Team</a>
            <a href="/careers">Careers</a>
            <a href="/blog">Blog</a>
        </body>
    </html>
    """
    
    base_url = "https://example.com"
    discovered = scraper.discover_pages(base_url, html)
    
    print(f"\nDiscovered {len(discovered)} pages:")
    for page_type, url in discovered.items():
        print(f"  {page_type.value}: {url}")


# ============================================================================
# Example 3: Data Quality Scoring
# ============================================================================

def example_data_quality_scoring():
    """Calculate data quality score"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Data Quality Scoring")
    print("="*70)
    
    scorer = DataQualityScorer()
    
    # Test cases with different data completeness
    test_cases = [
        {
            'name': 'Complete Data',
            'emails': ['contact@example.com', 'sales@example.com'],
            'phones': ['415-123-4567', '415-987-6543'],
            'addresses': [Address(street='123 Main St', city='SF', state='CA', postal_code='94105')],
            'company_name': 'Example Corp',
            'company_description': 'A great company',
            'pages_scanned': 5
        },
        {
            'name': 'Minimal Data',
            'emails': ['contact@example.com'],
            'phones': [],
            'addresses': [],
            'company_name': None,
            'company_description': None,
            'pages_scanned': 1
        },
        {
            'name': 'No Data',
            'emails': [],
            'phones': [],
            'addresses': [],
            'company_name': None,
            'company_description': None,
            'pages_scanned': 0
        }
    ]
    
    print("\nData Quality Scores:")
    for test in test_cases:
        score = scorer.calculate_quality_score(
            emails=test['emails'],
            phones=test['phones'],
            addresses=test['addresses'],
            company_name=test['company_name'],
            company_description=test['company_description'],
            pages_scanned=test['pages_scanned']
        )
        print(f"  {test['name']}: {score:.2f}")


# ============================================================================
# Example 4: Advanced Retry Strategy
# ============================================================================

def example_retry_strategy():
    """Demonstrate retry strategy with backoff"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Advanced Retry Strategy")
    print("="*70)
    
    strategy = AdvancedRetryStrategy(
        max_retries=5,
        initial_delay=1.0,
        backoff_factor=2.0
    )
    
    url = "https://example.com"
    
    print(f"\nRetry Strategy for {url}:")
    print(f"{'Attempt':<10} {'Should Retry':<15} {'Delay (s)':<12}")
    print("-" * 37)
    
    for attempt in range(1, 7):
        should_retry = strategy.should_retry(url)
        delay = strategy.get_retry_delay(url)
        
        print(f"{attempt:<10} {str(should_retry):<15} {delay:<12.2f}")
        
        if should_retry:
            strategy.record_failure(url, f"Attempt {attempt} failed")
        else:
            break


# ============================================================================
# Example 5: Company Info Extraction
# ============================================================================

def example_company_info_extraction():
    """Extract company information"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Company Info Extraction")
    print("="*70)
    
    extractor = CompanyInfoExtractor()
    
    # Sample HTML
    html = """
    <html>
        <head>
            <title>Example Corporation - Leading Tech Solutions</title>
            <meta name="description" content="We provide innovative technology solutions for businesses worldwide.">
        </head>
        <body>
            <h1>Welcome to Example Corp</h1>
            <p>We are a leading provider of enterprise software solutions.</p>
        </body>
    </html>
    """
    
    company_name = extractor.extract_company_name(html)
    company_description = extractor.extract_company_description(html)
    
    print(f"\nExtracted Company Info:")
    print(f"  Name: {company_name}")
    print(f"  Description: {company_description}")


# ============================================================================
# Example 6: Parallel Scraping Simulation
# ============================================================================

def example_parallel_scraping():
    """Simulate parallel scraping"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Parallel Scraping Simulation")
    print("="*70)
    
    # Mock scraper function
    def mock_scraper(url):
        import time
        time.sleep(0.1)  # Simulate scraping
        return EnhancedScraperResult(
            url=url,
            status="success",
            emails=['contact@example.com'],
            phones=['415-123-4567'],
            confidence_score=0.85
        )
    
    # Create mock base scraper
    class MockScraper:
        def scrape_url(self, url):
            return mock_scraper(url)
    
    # Create pipeline
    pipeline = AdvancedScraperPipeline(
        base_scraper=MockScraper(),
        max_workers=5
    )
    
    # URLs to scrape
    urls = [
        'https://example1.com',
        'https://example2.com',
        'https://example3.com',
        'https://example4.com',
        'https://example5.com'
    ]
    
    # Progress callback
    def progress(completed, total):
        print(f"  Progress: {completed}/{total} URLs completed")
    
    print(f"\nScraping {len(urls)} URLs in parallel...")
    results = pipeline.parallel_scraper.scrape_urls_parallel(
        urls,
        mock_scraper,
        progress_callback=progress
    )
    
    print(f"\nResults:")
    for result in results:
        print(f"  {result.url}: {result.status} "
              f"(Emails: {len(result.emails)}, Phones: {len(result.phones)})")


# ============================================================================
# Example 7: Enhanced Result Structure
# ============================================================================

def example_enhanced_result():
    """Demonstrate enhanced result structure"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Enhanced Result Structure")
    print("="*70)
    
    # Create enhanced result
    result = EnhancedScraperResult(
        url='https://example.com',
        status='success',
        emails=['contact@example.com', 'sales@example.com'],
        phones=['415-123-4567'],
        addresses=[
            Address(
                street='123 Main St',
                city='San Francisco',
                state='CA',
                postal_code='94105',
                confidence_score=0.95
            )
        ],
        company_name='Example Corporation',
        company_description='Leading tech solutions provider',
        pages_scraped={
            'homepage': True,
            'contact': True,
            'about': True,
            'team': False,
            'careers': False,
            'services': False,
            'blog': False
        },
        data_quality_score=0.88,
        confidence_score=0.85,
        pages_scanned=3,
        leadership_count=5,
        retry_count=0,
        fetch_mode='js_rendering',
        reason='Success',
        load_time=4.5
    )
    
    print(f"\nEnhanced Result:")
    print(f"  URL: {result.url}")
    print(f"  Status: {result.status}")
    print(f"  Company: {result.company_name}")
    print(f"  Description: {result.company_description}")
    print(f"  Emails: {len(result.emails)}")
    print(f"  Phones: {len(result.phones)}")
    print(f"  Addresses: {len(result.addresses)}")
    print(f"  Pages Scraped: {sum(1 for v in result.pages_scraped.values() if v)}")
    print(f"  Data Quality: {result.data_quality_score:.2f}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Load Time: {result.load_time:.2f}s")
    
    # Show CSV format
    print(f"\nCSV Format:")
    csv_dict = result.to_dict()
    for key, value in csv_dict.items():
        print(f"  {key}: {value}")


# ============================================================================
# Example 8: Complete Advanced Pipeline
# ============================================================================

def example_complete_pipeline():
    """Demonstrate complete advanced pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Complete Advanced Pipeline")
    print("="*70)
    
    # Mock base scraper
    class MockBaseScraper:
        def scrape_url(self, url):
            result = EnhancedScraperResult(
                url=url,
                status='success',
                emails=['contact@example.com'],
                phones=['415-123-4567'],
                confidence_score=0.85
            )
            result.html = """
            <html>
                <head>
                    <title>Example Corp - Tech Solutions</title>
                    <meta name="description" content="Leading technology provider">
                </head>
                <body>
                    <p>Our office: 123 Main St, San Francisco, CA 94105</p>
                    <a href="/contact">Contact</a>
                    <a href="/about">About</a>
                </body>
            </html>
            """
            return result
    
    # Create pipeline
    pipeline = AdvancedScraperPipeline(
        base_scraper=MockBaseScraper(),
        max_workers=5,
        max_pages_per_site=5,
        enable_address_extraction=True,
        enable_company_info=True
    )
    
    # Scrape URL
    url = 'https://example.com'
    print(f"\nScraping {url} with advanced features...")
    
    result = pipeline.scrape_url_advanced(url)
    
    print(f"\nAdvanced Scrape Results:")
    print(f"  URL: {result.url}")
    print(f"  Status: {result.status}")
    print(f"  Company: {result.company_name}")
    print(f"  Emails: {len(result.emails)}")
    print(f"  Phones: {len(result.phones)}")
    print(f"  Addresses: {len(result.addresses)}")
    print(f"  Data Quality: {result.data_quality_score:.2f}")
    print(f"  Load Time: {result.load_time:.2f}s")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("ADVANCED SCRAPER FEATURES - EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_address_extraction()
    example_multi_page_discovery()
    example_data_quality_scoring()
    example_retry_strategy()
    example_company_info_extraction()
    example_parallel_scraping()
    example_enhanced_result()
    example_complete_pipeline()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
