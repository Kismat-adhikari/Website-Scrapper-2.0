"""
Interactive Advanced Scraper Test
Test the advanced scraper with any URL you want
"""

import sys
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import modules
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


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80)


def print_section(title):
    """Print formatted section"""
    print(f"\n{title}")
    print("-" * len(title))


def format_text(text, max_length=100):
    """Format text with max length"""
    if not text:
        return "Not found"
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def test_single_url(url):
    """Test scraper with a single URL"""
    
    print_header(f"TESTING: {url}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize
        print("\n[1/4] Initializing scraper...")
        proxy_manager = ProxyManager()
        base_scraper = WebScraper(
            proxy_manager=proxy_manager,
            timeout=15,
            enable_precheck=True
        )
        
        pipeline = AdvancedScraperPipeline(
            base_scraper=base_scraper,
            max_workers=5,
            max_pages_per_site=3,
            enable_address_extraction=True,
            enable_company_info=True
        )
        print("✓ Scraper initialized")
        
        # Scrape
        print("[2/4] Scraping website...")
        start_time = time.time()
        result = pipeline.scrape_url_advanced(url)
        elapsed = time.time() - start_time
        print(f"✓ Scraping completed in {elapsed:.2f}s")
        
        # Display results
        print_section("RESULTS")
        
        print(f"\nBasic Info:")
        print(f"  Status: {result.status}")
        print(f"  Load Time: {result.load_time:.2f}s")
        print(f"  Fetch Mode: {result.fetch_mode}")
        print(f"  Reason: {result.reason}")
        
        print(f"\nCompany Info:")
        print(f"  Name: {result.company_name or 'Not found'}")
        print(f"  Description: {format_text(result.company_description, 80)}")
        
        print(f"\nContact Data:")
        print(f"  Emails: {len(result.emails)}")
        if result.emails:
            for i, email in enumerate(result.emails[:5], 1):
                print(f"    {i}. {email}")
            if len(result.emails) > 5:
                print(f"    ... and {len(result.emails) - 5} more")
        
        print(f"  Phones: {len(result.phones)}")
        if result.phones:
            for i, phone in enumerate(result.phones[:5], 1):
                print(f"    {i}. {phone}")
            if len(result.phones) > 5:
                print(f"    ... and {len(result.phones) - 5} more")
        
        print(f"  Addresses: {len(result.addresses)}")
        if result.addresses:
            for i, addr in enumerate(result.addresses[:3], 1):
                print(f"    {i}. {addr.full_address}")
        
        print(f"\nPages Scraped:")
        scraped_count = sum(1 for v in result.pages_scraped.values() if v)
        print(f"  {scraped_count}/{len(result.pages_scraped)} pages")
        for page_type, scraped in result.pages_scraped.items():
            status = "✓" if scraped else "✗"
            print(f"    {status} {page_type}")
        
        print(f"\nQuality Metrics:")
        print(f"  Data Quality Score: {result.data_quality_score:.2f}/1.0")
        print(f"  Confidence Score: {result.confidence_score:.2f}/1.0")
        print(f"  Pages Scanned: {result.pages_scanned}")
        print(f"  Leadership Mentions: {result.leadership_count}")
        print(f"  Retry Count: {result.retry_count}")
        
        # Quality rating
        if result.data_quality_score >= 0.8:
            rating = "Excellent ⭐⭐⭐⭐⭐"
        elif result.data_quality_score >= 0.6:
            rating = "Good ⭐⭐⭐⭐"
        elif result.data_quality_score >= 0.4:
            rating = "Fair ⭐⭐⭐"
        elif result.data_quality_score >= 0.2:
            rating = "Poor ⭐⭐"
        else:
            rating = "Very Poor ⭐"
        
        print(f"  Quality Rating: {rating}")
        
        print(f"\nSocial Links:")
        if result.social_links:
            for platform, links in result.social_links.items():
                print(f"  {platform}: {len(links)} link(s)")
        else:
            print("  None found")
        
        # Export
        print_section("EXPORT")
        
        import csv
        csv_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=result.to_dict().keys())
            writer.writeheader()
            writer.writerow(result.to_dict())
        
        print(f"\n✓ Results exported to: {csv_file}")
        
        # Summary
        print_section("SUMMARY")
        
        print(f"\n✓ URL: {url}")
        print(f"✓ Status: {result.status}")
        print(f"✓ Emails: {len(result.emails)}")
        print(f"✓ Phones: {len(result.phones)}")
        print(f"✓ Addresses: {len(result.addresses)}")
        print(f"✓ Quality: {result.data_quality_score:.2f}")
        print(f"✓ CSV: {csv_file}")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!".center(80))
        print("="*80 + "\n")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main interactive loop"""
    
    print_header("ADVANCED SCRAPER - INTERACTIVE TEST")
    
    print("\nWelcome to the Advanced Scraper Interactive Test!")
    print("Test the scraper with any URL you want.\n")
    
    print("Available sample URLs:")
    sample_urls = [
        "https://graybox.co",
        "https://sparkagency.com",
        "https://thriveagency.com",
        "https://websolutionagency.co",
        "https://digitalmarketinggroup.com",
    ]
    
    for i, url in enumerate(sample_urls, 1):
        print(f"  {i}. {url}")
    
    print("\nOptions:")
    print("  - Enter a URL to test")
    print("  - Enter a number (1-5) to test a sample URL")
    print("  - Type 'quit' to exit")
    print("  - Type 'batch' to test multiple URLs")
    
    while True:
        try:
            user_input = input("\n> Enter URL or command: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'batch':
                test_batch()
                continue
            
            # Check if it's a number
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(sample_urls):
                    url = sample_urls[idx]
                else:
                    print("Invalid number. Please enter 1-5.")
                    continue
            else:
                url = user_input
                # Add https if not present
                if not url.startswith('http'):
                    url = 'https://' + url
            
            # Test the URL
            test_single_url(url)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


def test_batch():
    """Test multiple URLs"""
    
    print_header("BATCH TEST MODE")
    
    print("\nEnter URLs (one per line, empty line to finish):")
    urls = []
    
    while True:
        url = input("> ").strip()
        if not url:
            break
        if not url.startswith('http'):
            url = 'https://' + url
        urls.append(url)
    
    if not urls:
        print("No URLs entered.")
        return
    
    print(f"\nTesting {len(urls)} URLs...")
    
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Testing {url}...")
        try:
            proxy_manager = ProxyManager()
            base_scraper = WebScraper(
                proxy_manager=proxy_manager,
                timeout=15,
                enable_precheck=True
            )
            
            pipeline = AdvancedScraperPipeline(
                base_scraper=base_scraper,
                max_workers=5,
                max_pages_per_site=3
            )
            
            result = pipeline.scrape_url_advanced(url)
            results.append(result)
            
            print(f"  ✓ Status: {result.status}")
            print(f"  ✓ Emails: {len(result.emails)}")
            print(f"  ✓ Phones: {len(result.phones)}")
            print(f"  ✓ Quality: {result.data_quality_score:.2f}")
        
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    # Export batch results
    if results:
        import csv
        csv_file = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
            writer.writeheader()
            writer.writerows([r.to_dict() for r in results])
        
        print(f"\n✓ Batch results exported to: {csv_file}")
        
        # Summary
        print_section("BATCH SUMMARY")
        
        total = len(results)
        successful = sum(1 for r in results if r.status == 'success')
        total_emails = sum(len(r.emails) for r in results)
        total_phones = sum(len(r.phones) for r in results)
        avg_quality = sum(r.data_quality_score for r in results) / len(results) if results else 0
        
        print(f"\nTotal URLs: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Total Emails: {total_emails}")
        print(f"Total Phones: {total_phones}")
        print(f"Average Quality: {avg_quality:.2f}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
