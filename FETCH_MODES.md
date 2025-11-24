# Fetch Modes Guide

This document explains the three fetch modes and how the scraper intelligently selects between them.

## Overview

The scraper uses three fetch modes to handle different types of websites:

1. **Fast HTML** - For accessible, non-protected sites
2. **JS Rendering** - For JavaScript-heavy or lightly protected sites
3. **Hard Mode** - For heavily protected or rate-limited sites

## Fast HTML Mode

### When Used
- Initial attempt for all sites (unless pre-check detects protection)
- Fastest and most resource-efficient
- Best for static HTML sites

### How It Works
```
1. Send HEAD request to check reachability
2. If reachable, send GET request with rotating User-Agent
3. Try up to 3 different User-Agent headers
4. Return HTML if status 200
```

### Characteristics
- **Speed**: ~0.5-2 seconds per page
- **Resource Usage**: Minimal (single HTTP request)
- **Success Rate**: High for unprotected sites
- **Limitations**: Cannot handle JavaScript rendering

### Example
```bash
python scraper.py https://example.com
# Will use Fast HTML if site is accessible
```

## JS Rendering Mode

### When Used
- Fallback from Fast HTML if it fails
- Pre-check detects bot protection (Cloudflare, CAPTCHA)
- Site has slow load time (>6 seconds)

### How It Works
```
1. Launch Playwright headless browser
2. Navigate to URL with networkidle wait
3. Wait for page to fully load
4. Extract rendered HTML
5. Close browser
```

### Characteristics
- **Speed**: ~3-8 seconds per page
- **Resource Usage**: High (full browser instance)
- **Success Rate**: Very high for protected sites
- **Advantages**: Handles JavaScript, bypasses some protections

### Example
```bash
python scraper.py https://cloudflare.com
# Will use JS Rendering due to Cloudflare detection
```

## Hard Mode

### When Used
- Fallback from JS Rendering if it fails
- Explicitly requested for heavily protected sites
- Site returns 429 (rate limited) or 403 (forbidden)

### How It Works
```
1. Rotate User-Agent headers (6 different options)
2. Rotate proxies from proxy list
3. Add exponential backoff delays
4. Retry up to 5 times
5. Handle 429/403 responses gracefully
```

### Anti-Blocking Techniques
- **Header Rotation**: 6 different realistic User-Agent strings
- **Proxy Rotation**: Cycles through available proxies
- **Delay Strategy**: 
  - Attempt 1: No delay
  - Attempt 2: 0.5s + random(0-1s)
  - Attempt 3: 1.0s + random(0-1s)
  - Attempt 4: 1.5s + random(0-1s)
  - Attempt 5: 2.0s + random(0-1s)

### Characteristics
- **Speed**: ~5-30 seconds per page (with delays)
- **Resource Usage**: Moderate (HTTP requests only)
- **Success Rate**: Highest for protected sites
- **Limitations**: Slower due to delays and retries

### Example
```bash
python scraper.py https://example.com --hard-mode-delay 1.5
# Will use Hard Mode with 1.5s base delay
```

## Mode Selection Algorithm

### Initial Selection (Pre-Check)
```
if bot_protection detected:
    → Use JS Rendering
elif load_time > 6 seconds:
    → Use JS Rendering
else:
    → Use Fast HTML
```

### Fallback Strategy
```
Try Fast HTML
  ↓ (if fails)
Try JS Rendering
  ↓ (if fails)
Try Hard Mode (up to 5 retries)
  ↓ (if all fail)
Mark as failed
```

### Failure History
The scraper tracks which modes failed for each URL:
- If Fast HTML fails, it won't retry Fast HTML for that URL
- If JS Rendering fails, it won't retry JS Rendering
- Hard Mode always retries (up to 5 times)

## Configuration

### Command Line Options

```bash
# Basic usage (auto-select modes)
python scraper.py urls.txt

# Disable pre-check (always start with Fast HTML)
python scraper.py urls.txt --no-precheck

# Increase hard mode delay for heavily protected sites
python scraper.py urls.txt --hard-mode-delay 2.0

# Increase timeout for slow sites
python scraper.py urls.txt --timeout 20

# Use proxies with hard mode
python scraper.py urls.txt --proxy-file proxies.txt --hard-mode-delay 1.5
```

### Python API

```python
from scraper import WebScraper, ProxyManager

# Create scraper with custom settings
proxy_manager = ProxyManager("proxies.txt")
scraper = WebScraper(
    proxy_manager=proxy_manager,
    timeout=15,
    enable_precheck=True,
    hard_mode_delay=1.0
)

# Scrape URL (mode selected automatically)
result = scraper.scrape_url("https://example.com")
print(f"Fetch mode used: {result.fetch_mode}")
print(f"Retries: {result.retry_count}")
```

## Output Analysis

### CSV Columns for Mode Analysis

- **fetch_mode**: Which mode was used (fast_html/js_rendering/hard_mode)
- **retry_count**: Number of retries attempted
- **bot_protection**: Type of protection detected
- **load_time**: Time to fetch the page
- **status**: success/failed/skipped

### Example Analysis

```python
import csv

with open('results.csv') as f:
    reader = csv.DictReader(f)
    
    fast_html = sum(1 for r in reader if r['fetch_mode'] == 'fast_html')
    js_rendering = sum(1 for r in reader if r['fetch_mode'] == 'js_rendering')
    hard_mode = sum(1 for r in reader if r['fetch_mode'] == 'hard_mode')
    
    print(f"Fast HTML: {fast_html}")
    print(f"JS Rendering: {js_rendering}")
    print(f"Hard Mode: {hard_mode}")
```

## Performance Tuning

### For Speed
```bash
# Disable pre-check, use fewer threads
python scraper.py urls.txt --no-precheck --threads 10
```

### For Reliability
```bash
# Enable pre-check, use hard mode delay
python scraper.py urls.txt --hard-mode-delay 1.5 --threads 3
```

### For Protected Sites
```bash
# Use proxies and hard mode delay
python scraper.py urls.txt --proxy-file proxies.txt --hard-mode-delay 2.0
```

## Troubleshooting

### All URLs failing with Fast HTML
- Enable pre-check: `--no-precheck` removed
- Check if sites have bot protection
- Try increasing timeout: `--timeout 20`

### JS Rendering mode too slow
- Reduce threads: `--threads 3`
- Increase timeout: `--timeout 20`
- Consider using proxies to avoid rate limiting

### Hard Mode not working
- Verify proxies are valid: `--proxy-file proxies.txt`
- Increase delay: `--hard-mode-delay 2.0`
- Check logs for specific error messages

### High retry counts
- Indicates site is heavily protected
- Consider increasing hard mode delay
- Use more proxies
- Reduce thread count to avoid rate limiting

## Best Practices

1. **Start with defaults**: Let the scraper auto-select modes
2. **Monitor logs**: Check `scraper.log` for patterns
3. **Use proxies**: Essential for hard mode effectiveness
4. **Adjust delays**: Increase for heavily protected sites
5. **Reduce threads**: Lower thread count = less rate limiting
6. **Test first**: Run on small URL set before full scrape

## Examples

### Example 1: Basic Scraping
```bash
python scraper.py urls.txt
# Uses pre-check to select modes automatically
```

### Example 2: Protected Sites
```bash
python scraper.py urls.txt --proxy-file proxies.txt --hard-mode-delay 1.5
# Uses proxies and hard mode for protection
```

### Example 3: Large Scale
```bash
python scraper.py urls.txt --threads 20 --hard-mode-delay 0.5
# Fast scraping with minimal delays
```

### Example 4: Slow Sites
```bash
python scraper.py urls.txt --timeout 30 --hard-mode-delay 2.0
# Extended timeout and delays for slow sites
```
