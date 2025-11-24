"""
Test Advanced Scraper Features with Real URL
Tests the advanced scraper with a real website from sample_urls.txt
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the existing scraper
try:
    from scraper import WebScraper, ProxyManager
    from advanced_scraper_features import (
        AdvancedScraperPipeline,
        AddressExtractor,
        CompanyInfoExtractor,
        DataQualityScorer
    )
    logger.info("Successfully imported scraper modules")
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)


def test_advanced_scraper_real_url():
    """Test advanced scraper with real URL"""
    
    print("\n" + "="*80)
    print("ADVANCED SCRAPER - REAL URL TEST")
    print("="*80)
    
    # URL to test
    test_url = "https://graybox.co"
    
    print(f"\nTesting URL: {test_url}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize base scraper
        print("\n[1/5] Initializing base scraper...")
        proxy_manager = ProxyManager()
        base_scraper = WebScraper(
            proxy_manager=proxy_manager,
            timeout=15,
            enable_precheck=True
        )
        logger.info("Base scraper initialized")
        
        # Initialize advanced pipeline
        print("[2/5] Initializing advanced pipeline...")
        pipeline = AdvancedScraperPipeline(
            base_scraper=base_scraper,
            max_workers=5,
            max_pages_per_site=3,
            enable_address_extraction=True,
            enable_company_info=True
        )
        logger.info("Advanced pipeline initialized")
        
        # Scrape with advanced features
        print(f"[3/5] Scraping {test_url} with advanced features...")
        result = pipeline.scrape_url_advanced(test_url)
        logger.info(f"Scraping completed for {test_url}")
        
        # Display results
        print("\n" + "="*80)
        print("SCRAPING RESULTS")
        print("="*80)
        
        print(f"\nBasic Information:")
        print(f"  URL: {result.url}")
        print(f"  Status: {result.status}")
        print(f"  Load Time: {result.load_time:.2f}s")
        print(f"  Fetch Mode: {result.fetch_mode}")
        print(f"  Reason: {result.reason}")
        
        print(f"\nCompany Information:")
        print(f"  Company Name: {result.company_name or 'Not found'}")
        print(f"  Description: {result.company_description[:100] + '...' if result.company_description else 'Not found'}")
        
        print(f"\nContact Information:")
        print(f"  Emails Found: {len(result.emails)}")
        if result.emails:
            for i, email in enumerate(result.emails[:5], 1):
                print(f"    {i}. {email}")
            if len(result.emails) > 5:
                print(f"    ... and {len(result.emails) - 5} more")
        
        print(f"  Phones Found: {len(result.phones)}")
        if result.phones:
            for i, phone in enumerate(result.phones[:5], 1):
                print(f"    {i}. {phone}")
            if len(result.phones) > 5:
                print(f"    ... and {len(result.phones) - 5} more")
        
        print(f"  Addresses Found: {len(result.addresses)}")
        if result.addresses:
            for i, addr in enumerate(result.addresses[:3], 1):
                print(f"    {i}. {addr.full_address}")
                print(f"       Confidence: {addr.confidence_score:.2f}")
        
        print(f"\nPages Scraped:")
        for page_type, scraped in result.pages_scraped.items():
            status = "✓" if scraped else "✗"
            print(f"  {status} {page_type}")
        
        print(f"\nData Quality:")
        print(f"  Quality Score: {result.data_quality_score:.2f}/1.0")
        print(f"  Confidence Score: {result.confidence_score:.2f}/1.0")
        print(f"  Pages Scanned: {result.pages_scanned}")
        print(f"  Leadership Mentions: {result.leadership_count}")
        print(f"  Retry Count: {result.retry_count}")
        
        print(f"\nSocial Links:")
        if result.social_links:
            for platform, links in result.social_links.items():
                print(f"  {platform}: {len(links)} link(s)")
                for link in links[:2]:
                    print(f"    - {link}")
                if len(links) > 2:
                    print(f"    ... and {len(links) - 2} more")
        else:
            print("  No social links found")
        
        # Quality analysis
        print("\n" + "="*80)
        print("DATA QUALITY ANALYSIS")
        print("="*80)
        
        scorer = DataQualityScorer()
        quality = scorer.calculate_quality_score(
            emails=result.emails,
            phones=result.phones,
            addresses=result.addresses,
            company_name=result.company_name,
            company_description=result.company_description,
            pages_scanned=result.pages_scanned
        )
        
        print(f"\nQuality Score Breakdown:")
        print(f"  Emails: {len(result.emails)} found (max 0.25 points)")
        print(f"  Phones: {len(result.phones)} found (max 0.20 points)")
        print(f"  Addresses: {len(result.addresses)} found (max 0.15 points)")
        print(f"  Company Info: {'Yes' if result.company_name else 'No'} (max 0.20 points)")
        print(f"  Pages Scanned: {result.pages_scanned} pages (max 0.20 points)")
        print(f"  Overall Quality: {quality:.2f}/1.0")
        
        # Quality rating
        if quality >= 0.8:
            rating = "Excellent"
        elif quality >= 0.6:
            rating = "Good"
        elif quality >= 0.4:
            rating = "Fair"
        else:
            rating = "Poor"
        
        print(f"  Rating: {rating}")
        
        # Export to CSV
        print("\n" + "="*80)
        print("EXPORTING RESULTS")
        print("="*80)
        
        import csv
        csv_file = f"advanced_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=result.to_dict().keys())
            writer.writeheader()
            writer.writerow(result.to_dict())
        
        print(f"\n✓ Results exported to: {csv_file}")
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        print(f"\n✓ Successfully scraped: {test_url}")
        print(f"✓ Company: {result.company_name or 'Not found'}")
        print(f"✓ Emails: {len(result.emails)}")
        print(f"✓ Phones: {len(result.phones)}")
        print(f"✓ Addresses: {len(result.addresses)}")
        print(f"✓ Quality Score: {result.data_quality_score:.2f}")
        print(f"✓ Pages Scraped: {sum(1 for v in result.pages_scraped.values() if v)}/{len(result.pages_scraped)}")
        print(f"✓ Load Time: {result.load_time:.2f}s")
        print(f"✓ CSV Export: {csv_file}")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False


if __name__ == '__main__':
    success = test_advanced_scraper_real_url()
    sys.exit(0 if success else 1)
