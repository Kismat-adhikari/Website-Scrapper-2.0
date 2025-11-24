"""
Quick test to verify single URL scraping works
"""

from async_scraper import scrape_url_async_wrapper
from scraper import ProxyManager
import logging

logging.basicConfig(level=logging.INFO)

# Test URL
test_url = 'https://example.com'

print(f"Testing single URL scraping: {test_url}")
print("-" * 60)

try:
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    
    # Scrape URL
    print("Scraping...")
    result = scrape_url_async_wrapper(test_url, proxy_manager=proxy_manager, fast_mode=True)
    
    # Display results
    print(f"\n✓ Scraping completed!")
    print(f"URL: {result.url}")
    print(f"Status: {result.status}")
    print(f"Emails: {len(result.emails)} found")
    print(f"Phones: {len(result.phones)} found")
    print(f"Confidence: {result.confidence_score}")
    print(f"Load time: {result.load_time:.2f}s")
    
    if result.emails:
        print(f"\nEmails found:")
        for email in result.emails:
            print(f"  - {email}")
    
    if result.phones:
        print(f"\nPhones found:")
        for phone in result.phones:
            print(f"  - {phone}")
    
    if result.status == 'failed':
        print(f"\nFailure reason: {result.reason}")
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
