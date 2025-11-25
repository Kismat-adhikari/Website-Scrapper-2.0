#!/usr/bin/env python3
"""
Fast Scraper - Terminal version using async scraper
Speed: 1-2 seconds per URL (same as web interface)

Usage:
    python fast_scrape.py https://example.com
    python fast_scrape.py urls.txt
    python fast_scrape.py url1 url2 url3
"""

import sys
import csv
from datetime import datetime
from async_scraper import scrape_url_async_wrapper, scrape_urls_batch_wrapper
from scraper import ProxyManager

def scrape_single(url, proxy_manager):
    """Scrape a single URL"""
    print(f"🔍 Scraping {url}...")
    result = scrape_url_async_wrapper(url, proxy_manager, fast_mode=True)
    
    print(f"  Status: {result.status}")
    print(f"  📧 Emails: {len(result.emails)}")
    print(f"  📞 Phones: {len(result.phones)}")
    if result.emails:
        print(f"     {', '.join(result.emails)}")
    if result.phones:
        print(f"     {', '.join(result.phones)}")
    print()
    
    return result

def scrape_batch(urls, proxy_manager):
    """Scrape multiple URLs in parallel"""
    print(f"🚀 Scraping {len(urls)} URLs in parallel...")
    results = scrape_urls_batch_wrapper(urls, proxy_manager, fast_mode=True)
    
    # Print summary
    success_count = sum(1 for r in results if r.status == 'success')
    total_emails = sum(len(r.emails) for r in results)
    total_phones = sum(len(r.phones) for r in results)
    
    print(f"\n✅ Complete!")
    print(f"  Success: {success_count}/{len(urls)}")
    print(f"  Total emails: {total_emails}")
    print(f"  Total phones: {total_phones}")
    
    return results

def save_results(results, output_file=None):
    """Save results to CSV"""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', 'Status', 'Emails', 'Phones', 'Company', 'Confidence'])
        
        for r in results:
            writer.writerow([
                r.url,
                r.status,
                '; '.join(r.emails),
                '; '.join(r.phones),
                getattr(r, 'company_name', ''),
                f"{r.confidence_score:.2f}"
            ])
    
    print(f"\n💾 Saved to: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fast_scrape.py https://example.com")
        print("  python fast_scrape.py urls.txt")
        print("  python fast_scrape.py url1 url2 url3")
        sys.exit(1)
    
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    
    # Parse input
    urls = []
    for arg in sys.argv[1:]:
        if arg.startswith('http://') or arg.startswith('https://'):
            urls.append(arg)
        else:
            # Try to read as file
            try:
                with open(arg, 'r') as f:
                    file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    urls.extend(file_urls)
            except FileNotFoundError:
                print(f"❌ File not found: {arg}")
                sys.exit(1)
    
    if not urls:
        print("❌ No URLs provided")
        sys.exit(1)
    
    # Scrape
    if len(urls) == 1:
        # Single URL - show detailed output
        result = scrape_single(urls[0], proxy_manager)
        results = [result]
    else:
        # Multiple URLs - use batch mode
        results = scrape_batch(urls, proxy_manager)
    
    # Save results
    save_results(results)

if __name__ == '__main__':
    main()
