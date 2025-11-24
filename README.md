# Web Scraper - Contact Information Extractor

A reliability-first Python web scraper designed to extract contact information from websites with intelligent fallback mechanisms and multi-threaded execution.

## Features

- **Multi-Mode Fetch System**: Intelligent mode selection based on site characteristics
  - Fast HTML: Standard requests for accessible sites
  - JS Rendering: Playwright for JavaScript-heavy sites
  - Hard Mode: Anti-blocking techniques with rotating headers/proxies
- **Pre-Check System**: Lightweight validation before scraping
  - SSL certificate verification
  - Bot protection detection (Cloudflare, CAPTCHA, 403/429 errors)
  - Page load speed measurement
  - Intelligent scrape mode selection
- **Intelligent Page Discovery**: Automatically finds relevant pages
  - Contact pages: contact, support, help, reach, get-in-touch, hello, talk
  - Team/Leadership pages: team, about, people, leadership, executives, management, founders
  - URL deduplication and normalization
  - Configurable discovery depth to prevent excessive scraping
- **Advanced Contact Information Extraction**:
  - Emails: Filtered to exclude no-reply addresses
  - Phone numbers: Normalized with minimum 6 digits
  - Leadership titles: CEO, CTO, CMO, COO, Founder, President, VP, etc.
  - Social media links: LinkedIn, Twitter, Facebook, Instagram, GitHub, YouTube
- **Intelligent Retry & Recovery**:
  - Retry with different headers and proxies
  - Automatic fallback: HTML → JS Rendering → Hard Mode
  - Exponential backoff delays
  - Failure reason detection and logging
  - Problematic site tracking for reduced concurrency
- **Proxy Support**: Accepts proxies in `ip:port` or `ip:port:user:pass` format
  - Thread-safe proxy rotation
  - Periodic rotation every 14 requests
  - Works regardless of request success/failure
  - Helps avoid detection patterns
- **Multi-Threaded**: Parallel scraping with configurable workers
  - ThreadPoolExecutor for efficient parallelism
  - Thread-safe proxy rotation
  - Non-blocking retry logic
  - Configurable thread count (1-50+)
- **Confidence Scoring**: 0-1 score based on data quality and extraction methods
- **Comprehensive Logging**: Three detailed log files for monitoring and analysis
  - scraper.log: General execution log
  - scraper_attempts.log: Detailed attempt tracking
  - scraper_failures.log: Failed URLs with reasons
- **CSV Export**: Structured output with all extracted data

## Installation

```bash
pip install -r requirements.txt
```

You'll also need ChromeDriver for Selenium. Download from: https://chromedriver.chromium.org/

## Usage

### Basic Usage - Single URL
```bash
python scraper.py https://example.com
```

### Multiple URLs from File
```bash
python scraper.py sample_urls.txt
```

### With Proxies
```bash
python scraper.py sample_urls.txt --proxy-file proxies.txt
```

### Custom Output and Threading
```bash
python scraper.py sample_urls.txt --output results.csv --threads 10 --timeout 15
```

### Hard Mode with Custom Delay
```bash
python scraper.py sample_urls.txt --hard-mode-delay 1.5
```

### Limit Page Discovery
```bash
python scraper.py sample_urls.txt --max-pages 5
```

### Disable Pre-Check (Legacy Mode)
```bash
python scraper.py sample_urls.txt --no-precheck
```

## Proxy File Format

Create `proxies.txt` with one proxy per line:

```
192.168.1.1:8080
10.0.0.1:3128:username:password
```

## Output CSV Columns

- **url**: Target URL
- **status**: success/failed/skipped
- **emails**: List of extracted emails
- **phones**: List of extracted phone numbers
- **pages_scanned**: Number of pages scanned
- **leadership_count**: Count of leadership-related mentions
- **email_list**: Semicolon-separated email list
- **phone_list**: Semicolon-separated phone numbers
- **social_links**: JSON object with social media links (LinkedIn, Twitter, etc.)
- **confidence_score**: 0-1 confidence score
- **reason**: Failure reason or "Success"
- **load_time**: Page load time in seconds
- **ssl_valid**: SSL certificate validity (true/false)
- **bot_protection**: Detected protection type (cloudflare/captcha/403/429/None)
- **scrape_mode**: Mode used (normal/browser/slow_mode/skip)
- **fetch_mode**: Fetch method used (fast_html/js_rendering/hard_mode)
- **retry_count**: Number of retries attempted

## Confidence Score Calculation

Score is calculated 0-1 based on:
- **Email count** (0-0.25): Up to 5 emails = full score
- **Phone count** (0-0.20): Up to 3 phones = full score
- **Pages scanned** (0-0.20): Up to 5 pages = full score
- **Leadership mentions** (0-0.15): Up to 10 mentions = full score
- **Fetch method** (0-0.10): Fast HTML (0.10) > JS Rendering (0.08) > Hard Mode (0.05)
- **Retry count** (0-0.10): No retries (0.10) > 1-2 retries (0.07) > 3+ retries (0.03)

**Example Scores**:
- High quality (5 emails, 2 phones, 3 pages, 8 leadership, no retries, fast HTML): ~0.85
- Medium quality (2 emails, 1 phone, 2 pages, 3 leadership, 1 retry, JS rendering): ~0.60
- Low quality (0 emails, 0 phones, 1 page, 0 leadership, 5 retries, hard mode): ~0.15

## Logging

Logs are written to `scraper.log` and console output. Check this file for detailed failure analysis.

## Architecture

### Page Discovery

**Intelligent Page Detection**
- Scans HTML for links matching contact/team keywords
- Contact keywords: contact, support, help, reach, get-in-touch, hello, talk, inquiry, message, etc.
- Team keywords: team, about, people, leadership, executives, management, founders, staff, etc.

**URL Processing**
- Normalizes URLs (removes fragments, trailing slashes)
- Deduplicates URLs with different cases/formats
- Filters out non-HTML resources (PDFs, images, etc.)
- Excludes admin/login/error pages
- Verifies same-domain links only

**Discovery Limits**
- Maximum pages per site: configurable (default: 10)
- Maximum pages to scan: 5 per site (prevents excessive scraping)
- Depth limit: 2 levels to prevent crawling entire website

### Fetch Modes

**Fast HTML** (`fast_html`)
- Standard `requests.get` with rotating User-Agent headers
- Fastest option for accessible sites
- Minimal resource usage

**JS Rendering** (`js_rendering`)
- Playwright headless browser
- Handles JavaScript-rendered content
- Detects dynamic page loads
- Fallback from Fast HTML

**Hard Mode** (`hard_mode`)
- Anti-blocking techniques:
  - Rotating User-Agent headers
  - Proxy rotation
  - Configurable delays between requests
  - Up to 5 retry attempts
- Handles rate limiting (429) and access denied (403)
- Last resort for protected sites

### FetchModeSelector
Intelligent mode selection based on:
- Pre-check results (bot protection, load time)
- Failure history (tracks failed modes per URL)
- Automatic escalation: Fast HTML → JS Rendering → Hard Mode

### PreCheckSystem
Lightweight validation before scraping:
- **SSL Verification**: Validates HTTPS certificates
- **Reachability Check**: HEAD request to verify site accessibility
- **Bot Protection Detection**: Identifies Cloudflare, CAPTCHA, 403/429 errors
- **Load Time Measurement**: Measures page response time
- **Scrape Mode Selection**: Returns optimal scraping strategy

### ProxyManager
Manages proxy rotation and parsing for both basic and authenticated proxies.

### ContactExtractor
Extracts emails, phones, leadership info using regex patterns and HTML parsing.

### WebScraper
Main scraping engine with intelligent fallback:
1. Pre-check validation (if enabled)
2. Fetch mode selection based on pre-check and history
3. Automatic escalation through fetch modes
4. Automatic contact page discovery

## Pre-Check System Details

The pre-check system runs before each scrape to optimize strategy:

1. **SSL Check**: Validates certificate chain (HTTPS only)
2. **Reachability**: Sends HEAD request with timeout
3. **Bot Protection Detection**:
   - Cloudflare: Checks headers and content for CF indicators
   - CAPTCHA: Detects recaptcha, hcaptcha, challenge pages
   - HTTP Errors: 403 (Forbidden), 429 (Rate Limited)
4. **Load Time**: Measures response time
   - Normal: < 6 seconds
   - Slow: > 6 seconds (uses extended timeout)

Results are logged and included in CSV output for analysis.

## Page Discovery Details

The scraper automatically discovers relevant pages without manual configuration:

**Contact Pages**
- Keywords: contact, support, help, reach, get-in-touch, hello, talk, inquiry, message
- Examples: /contact, /support, /get-in-touch, /contact-us

**Team/Leadership Pages**
- Keywords: team, about, people, leadership, executives, management, founders, staff
- Examples: /team, /about, /leadership, /our-team, /executives

**Smart Processing**
- URL normalization (removes fragments, trailing slashes)
- Deduplication (case-insensitive, format-insensitive)
- Exclusion of non-HTML resources (PDFs, images, etc.)
- Same-domain verification
- Configurable discovery limits

**Limits**
- Maximum pages to discover: configurable (default: 10)
- Maximum pages to scan: 5 per site
- Prevents crawling entire website

See [PAGE_DISCOVERY.md](PAGE_DISCOVERY.md) for detailed configuration.

## Performance Tips

- **Threads**: Use `--threads` to adjust parallelism (default: 5)
  - Higher threads = faster but more resource usage
  - Lower threads = slower but less blocking
- **Timeout**: Increase `--timeout` for slow sites (default: 10s)
- **Hard Mode Delay**: Use `--hard-mode-delay` to control rate limiting
  - Default: 0.5s between requests
  - Increase for heavily protected sites
- **Page Discovery**: Use `--max-pages` to control discovery depth
  - Default: 10 pages per site
  - Lower for speed, higher for thoroughness
- **Proxies**: Use proxies to avoid rate limiting and IP blocking
- **Pre-Check**: Adds ~1-2 seconds per URL but prevents wasted browser resources
- **Monitoring**: Check `scraper.log` for patterns in failures

## Fetch Mode Selection Strategy

The scraper automatically selects the best fetch mode:

1. **Pre-check determines initial mode**:
   - No protection + fast load → Fast HTML
   - Bot protection or slow → JS Rendering

2. **Failure triggers escalation**:
   - Fast HTML fails → Try JS Rendering
   - JS Rendering fails → Try Hard Mode
   - Hard Mode retries up to 5 times

3. **Hard Mode anti-blocking**:
   - Rotating headers (6 different User-Agents)
   - Proxy rotation
   - Exponential backoff delays
   - Handles 429 (rate limit) and 403 (forbidden)
#   W e b s i t e - S c r a p p e r - 2 . 0  
 