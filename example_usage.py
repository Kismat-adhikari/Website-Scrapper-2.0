#!/usr/bin/env python3
"""
Example usage of the web scraper with multiple fetch modes
"""

from scraper import WebScraper, ProxyManager, PreCheckSystem, ScrapeMode, FetchMode, FetchModeSelector, PageDiscovery

# Example 1: Basic usage with pre-check
def example_basic():
    print("=== Example 1: Basic Scraping with Pre-Check ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True)
    
    urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com"
    ]
    
    for url in urls:
        result = scraper.scrape_url(url)
        print(f"URL: {result.url}")
        print(f"Status: {result.status}")
        print(f"Scrape Mode: {result.scrape_mode}")
        print(f"Load Time: {result.load_time:.2f}s")
        print(f"SSL Valid: {result.ssl_valid}")
        print(f"Bot Protection: {result.bot_protection}")
        print(f"Emails Found: {len(result.emails)}")
        print(f"Confidence Score: {result.confidence_score:.2f}")
        print(f"Reason: {result.reason}\n")


# Example 2: Pre-check only (no scraping)
def example_precheck_only():
    print("=== Example 2: Pre-Check Only ===\n")
    
    precheck = PreCheckSystem(timeout=5)
    urls = [
        "https://example.com",
        "https://cloudflare.com",
        "https://httpstat.us/429",  # Rate limited
    ]
    
    for url in urls:
        result = precheck.check_url(url)
        print(f"URL: {result.url}")
        print(f"Reachable: {result.is_reachable}")
        print(f"SSL Valid: {result.ssl_valid}")
        print(f"Bot Protection: {result.bot_protection}")
        print(f"Load Time: {result.load_time:.2f}s")
        print(f"Is Slow: {result.is_slow}")
        print(f"Scrape Mode: {result.scrape_mode.value}")
        print(f"Reason: {result.check_reason}\n")


# Example 3: Using proxies with pre-check
def example_with_proxies():
    print("=== Example 3: With Proxies ===\n")
    
    # Load proxies from file
    proxy_manager = ProxyManager("proxies.txt")
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True)
    
    url = "https://example.com"
    result = scraper.scrape_url(url)
    
    print(f"URL: {result.url}")
    print(f"Status: {result.status}")
    print(f"Scrape Mode: {result.scrape_mode}")
    print(f"Emails: {result.email_list}")
    print(f"Confidence: {result.confidence_score:.2f}\n")


# Example 4: Analyzing pre-check results
def example_analyze_precheck():
    print("=== Example 4: Analyzing Pre-Check Results ===\n")
    
    precheck = PreCheckSystem(timeout=5)
    urls = [
        "https://example.com",
        "https://github.com",
        "https://httpstat.us/403",
    ]
    
    results = []
    for url in urls:
        result = precheck.check_url(url)
        results.append(result)
    
    # Analyze results
    normal_count = sum(1 for r in results if r.scrape_mode == ScrapeMode.NORMAL)
    browser_count = sum(1 for r in results if r.scrape_mode == ScrapeMode.BROWSER)
    slow_count = sum(1 for r in results if r.scrape_mode == ScrapeMode.SLOW_MODE)
    skip_count = sum(1 for r in results if r.scrape_mode == ScrapeMode.SKIP)
    
    print(f"Total URLs: {len(results)}")
    print(f"Normal Mode: {normal_count}")
    print(f"Browser Mode: {browser_count}")
    print(f"Slow Mode: {slow_count}")
    print(f"Skip: {skip_count}")
    print(f"Average Load Time: {sum(r.load_time for r in results) / len(results):.2f}s\n")
    
    # Show protection detected
    protected = [r for r in results if r.bot_protection]
    if protected:
        print("Protected Sites:")
        for r in protected:
            print(f"  - {r.url}: {r.bot_protection}")


# Example 5: Fetch mode selection
def example_fetch_modes():
    print("=== Example 5: Fetch Mode Selection ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True, hard_mode_delay=0.5)
    
    urls = [
        "https://example.com",
        "https://github.com",
        "https://cloudflare.com",
    ]
    
    for url in urls:
        result = scraper.scrape_url(url)
        print(f"URL: {result.url}")
        print(f"Fetch Mode: {result.fetch_mode}")
        print(f"Retries: {result.retry_count}")
        print(f"Status: {result.status}")
        print(f"Emails: {len(result.emails)}")
        print(f"Confidence: {result.confidence_score:.2f}\n")


# Example 6: Hard mode with custom delay
def example_hard_mode():
    print("=== Example 6: Hard Mode with Custom Delay ===\n")
    
    proxy_manager = ProxyManager("proxies.txt")
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True, hard_mode_delay=1.5)
    
    # This URL will use hard mode if it has bot protection
    url = "https://example.com"
    result = scraper.scrape_url(url)
    
    print(f"URL: {result.url}")
    print(f"Fetch Mode: {result.fetch_mode}")
    print(f"Retries: {result.retry_count}")
    print(f"Bot Protection: {result.bot_protection}")
    print(f"Status: {result.status}\n")


# Example 7: Analyzing fetch mode distribution
def example_fetch_mode_analysis():
    print("=== Example 7: Fetch Mode Distribution ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True)
    
    urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com",
    ]
    
    results = []
    for url in urls:
        result = scraper.scrape_url(url)
        results.append(result)
    
    # Analyze fetch modes
    fast_html_count = sum(1 for r in results if r.fetch_mode == FetchMode.FAST_HTML.value)
    js_rendering_count = sum(1 for r in results if r.fetch_mode == FetchMode.JS_RENDERING.value)
    hard_mode_count = sum(1 for r in results if r.fetch_mode == FetchMode.HARD_MODE.value)
    
    print(f"Total URLs: {len(results)}")
    print(f"Fast HTML: {fast_html_count}")
    print(f"JS Rendering: {js_rendering_count}")
    print(f"Hard Mode: {hard_mode_count}")
    print(f"Total Retries: {sum(r.retry_count for r in results)}")
    print(f"Success Rate: {sum(1 for r in results if r.status == 'success') / len(results) * 100:.1f}%\n")


# Example 8: Page discovery
def example_page_discovery():
    print("=== Example 8: Page Discovery ===\n")
    
    discovery = PageDiscovery(max_pages=10)
    
    # Simulate HTML with links
    html = """
    <html>
        <body>
            <a href="/contact">Contact Us</a>
            <a href="/about">About</a>
            <a href="/team">Our Team</a>
            <a href="/support">Support</a>
            <a href="/leadership">Leadership</a>
            <a href="/blog">Blog</a>
            <a href="/admin">Admin</a>
        </body>
    </html>
    """
    
    base_url = "https://example.com"
    contact_urls, team_urls = discovery.discover_all_pages(base_url, html)
    
    print(f"Contact pages found: {len(contact_urls)}")
    for url in contact_urls:
        print(f"  - {url}")
    
    print(f"\nTeam pages found: {len(team_urls)}")
    for url in team_urls:
        print(f"  - {url}")


# Example 9: Page discovery with deduplication
def example_page_discovery_dedup():
    print("=== Example 9: Page Discovery with Deduplication ===\n")
    
    discovery = PageDiscovery(max_pages=10)
    
    # HTML with duplicate links (different cases, trailing slashes)
    html = """
    <html>
        <body>
            <a href="/contact">Contact</a>
            <a href="/Contact">Contact (uppercase)</a>
            <a href="/contact/">Contact (trailing slash)</a>
            <a href="/about">About</a>
            <a href="/About/">About (uppercase + slash)</a>
        </body>
    </html>
    """
    
    base_url = "https://example.com"
    contact_urls, team_urls = discovery.discover_all_pages(base_url, html)
    
    print(f"Contact pages (deduplicated): {len(contact_urls)}")
    for url in contact_urls:
        print(f"  - {url}")
    
    print(f"\nTeam pages (deduplicated): {len(team_urls)}")
    for url in team_urls:
        print(f"  - {url}")


# Example 10: Scraping with page discovery
def example_scraping_with_discovery():
    print("=== Example 10: Scraping with Page Discovery ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True, max_pages_per_site=5)
    
    url = "https://example.com"
    result = scraper.scrape_url(url)
    
    print(f"URL: {result.url}")
    print(f"Pages scanned: {result.pages_scanned}")
    print(f"Emails found: {len(result.emails)}")
    print(f"Phones found: {len(result.phones)}")
    print(f"Leadership mentions: {result.leadership_count}")
    print(f"Status: {result.status}\n")


# Example 11: Extraction analysis
def example_extraction_analysis():
    print("=== Example 11: Extraction Analysis ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True)
    
    urls = [
        "https://example.com",
        "https://github.com",
    ]
    
    results = []
    for url in urls:
        result = scraper.scrape_url(url)
        results.append(result)
    
    # Analyze extraction
    for result in results:
        print(f"URL: {result.url}")
        print(f"Emails: {len(result.emails)} - {result.email_list}")
        print(f"Phones: {len(result.phones)} - {result.phone_list}")
        print(f"Leadership: {result.leadership_count}")
        print(f"Social Links: {result.social_links}")
        print(f"Confidence: {result.confidence_score:.2f}\n")


# Example 12: Confidence score analysis
def example_confidence_analysis():
    print("=== Example 12: Confidence Score Analysis ===\n")
    
    proxy_manager = ProxyManager()
    scraper = WebScraper(proxy_manager, timeout=10, enable_precheck=True)
    
    urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com",
    ]
    
    results = []
    for url in urls:
        result = scraper.scrape_url(url)
        results.append(result)
    
    # Analyze confidence scores
    high_confidence = sum(1 for r in results if r.confidence_score >= 0.75)
    medium_confidence = sum(1 for r in results if 0.50 <= r.confidence_score < 0.75)
    low_confidence = sum(1 for r in results if r.confidence_score < 0.50)
    
    print(f"Total URLs: {len(results)}")
    print(f"High Confidence (0.75+): {high_confidence}")
    print(f"Medium Confidence (0.50-0.74): {medium_confidence}")
    print(f"Low Confidence (<0.50): {low_confidence}")
    print(f"Average Confidence: {sum(r.confidence_score for r in results) / len(results):.2f}\n")
    
    # Show breakdown
    for result in results:
        confidence_level = "High" if result.confidence_score >= 0.75 else ("Medium" if result.confidence_score >= 0.50 else "Low")
        print(f"{result.url}: {result.confidence_score:.2f} ({confidence_level})")


if __name__ == "__main__":
    # Uncomment to run examples
    # example_basic()
    # example_precheck_only()
    # example_with_proxies()
    # example_analyze_precheck()
    # example_fetch_modes()
    # example_hard_mode()
    # example_fetch_mode_analysis()
    # example_page_discovery()
    # example_page_discovery_dedup()
    # example_scraping_with_discovery()
    # example_extraction_analysis()
    # example_confidence_analysis()
    
    print("Examples available:")
    print("1. example_basic() - Basic scraping with pre-check")
    print("2. example_precheck_only() - Pre-check validation only")
    print("3. example_with_proxies() - Using proxies")
    print("4. example_analyze_precheck() - Analyzing pre-check results")
    print("5. example_fetch_modes() - Fetch mode selection")
    print("6. example_hard_mode() - Hard mode with custom delay")
    print("7. example_fetch_mode_analysis() - Fetch mode distribution")
    print("8. example_page_discovery() - Page discovery")
    print("9. example_page_discovery_dedup() - Page discovery with deduplication")
    print("10. example_scraping_with_discovery() - Scraping with page discovery")
    print("11. example_extraction_analysis() - Extraction analysis")
    print("12. example_confidence_analysis() - Confidence score analysis")
