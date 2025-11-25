# Terminal vs Web Speed Comparison

## Current Situation

### 🌐 Web Interface (Flask app.py)
**Speed: 1-2 seconds per URL** ⚡
- Uses `async_scraper.py` (optimized)
- Timeout: 5 seconds
- Max pages: 1 (main page only)
- No pre-check
- Smart escalation to aggressive mode

### 💻 Terminal (scraper.py)
**Speed: 5-15 seconds per URL** 🐌
- Uses old `WebScraper` class (synchronous)
- Timeout: 10 seconds (default)
- Max pages: 10 (default)
- Pre-check enabled (adds 2-5s per URL)
- More thorough but slower

---

## Why Terminal is Slower

### 1. Pre-Check System
```python
enable_precheck = True  # Default
```
- Checks SSL certificate (1-2s)
- Tests reachability (1-2s)
- Detects bot protection (1-2s)
- **Total overhead: 3-6 seconds per URL**

### 2. Higher Timeout
```python
timeout = 10  # vs 5 in async
```
- Waits longer for slow sites
- **Adds 5 seconds** when sites are slow

### 3. More Pages
```python
max_pages = 10  # vs 1 in async
```
- Scrapes contact, about, team pages
- **Adds 5-10 seconds** per URL

### 4. Synchronous Requests
- Uses `requests` library (blocking)
- No parallel page fetching
- **Slower than async by 30-50%**

---

## How to Speed Up Terminal Scraper

### Option 1: Quick Flags (Fastest)
```bash
python scraper.py urls.txt --no-precheck --timeout 5 --max-pages 1
```
**Result: 2-3 seconds per URL** ⚡

### Option 2: Use Async Wrapper
Create a new file `fast_scraper.py`:
```python
from async_scraper import scrape_url_async_wrapper
from scraper import ProxyManager

proxy_manager = ProxyManager()

urls = ['https://example.com', 'https://example2.com']

for url in urls:
    result = scrape_url_async_wrapper(url, proxy_manager, fast_mode=True)
    print(f"{url}: {len(result.emails)} emails, {len(result.phones)} phones")
```
**Result: 1-2 seconds per URL** ⚡⚡

### Option 3: Batch Mode with Async
```python
from async_scraper import scrape_urls_batch_wrapper
from scraper import ProxyManager

proxy_manager = ProxyManager()
urls = ['url1', 'url2', 'url3', ...]

results = scrape_urls_batch_wrapper(urls, proxy_manager, fast_mode=True)
# All URLs scraped in parallel!
```
**Result: 0.1-0.2 seconds per URL** ⚡⚡⚡

---

## Recommended Usage

### For Speed (1-2s per URL)
Use the **web interface** or create a simple script:
```python
# fast_scrape.py
from async_scraper import scrape_url_async_wrapper
from scraper import ProxyManager
import sys

proxy_manager = ProxyManager()
url = sys.argv[1]

result = scrape_url_async_wrapper(url, proxy_manager, fast_mode=True)
print(f"Emails: {result.emails}")
print(f"Phones: {result.phones}")
```

Run: `python fast_scrape.py https://example.com`

### For Thoroughness (5-15s per URL)
Use the **terminal scraper** with default settings:
```bash
python scraper.py urls.txt
```
- Scrapes multiple pages
- Validates everything
- More complete data

### For Batch Processing (0.1-0.2s per URL)
Use **async batch mode**:
```python
# batch_scrape.py
from async_scraper import scrape_urls_batch_wrapper
from scraper import ProxyManager

proxy_manager = ProxyManager()

# Read URLs from file
with open('urls.txt') as f:
    urls = [line.strip() for line in f if line.strip()]

# Scrape all in parallel
results = scrape_urls_batch_wrapper(urls, proxy_manager, fast_mode=True)

# Save results
import csv
with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'Emails', 'Phones', 'Status'])
    for r in results:
        writer.writerow([r.url, '; '.join(r.emails), '; '.join(r.phones), r.status])

print(f"Scraped {len(results)} URLs!")
```

---

## Speed Comparison Table

| Method | Speed per URL | Best For |
|--------|--------------|----------|
| Web Interface | 1-2s | Interactive use |
| Terminal (default) | 5-15s | Thorough scraping |
| Terminal (fast flags) | 2-3s | Quick terminal use |
| Async wrapper | 1-2s | Custom scripts |
| Async batch | 0.1-0.2s | Large batches |

---

## Bottom Line

**Yes, terminal scraper is slower** because it:
- Uses old synchronous code
- Has pre-check enabled
- Scrapes more pages
- Has longer timeouts

**To match web speed from terminal:**
```bash
python scraper.py urls.txt --no-precheck --timeout 5 --max-pages 1
```

**Or create a fast script using async_scraper.py** (recommended!)
