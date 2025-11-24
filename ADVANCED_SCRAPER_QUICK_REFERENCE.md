# Advanced Scraper - Quick Reference Card

## Installation

No additional dependencies required.

## Basic Usage

```python
from advanced_scraper_features import AdvancedScraperPipeline

# Create pipeline
pipeline = AdvancedScraperPipeline(
    base_scraper=your_scraper,
    max_workers=50,
    max_pages_per_site=5
)

# Scrape single URL
result = pipeline.scrape_url_advanced('https://example.com')

# Scrape multiple URLs
results = pipeline.scrape_urls_parallel(urls)
```

## Key Features

### Multi-Page Scraping
```python
# Automatically discovers and scrapes:
# - Contact pages
# - About pages
# - Team pages
# - Careers pages
# - Service pages
# - Blog pages
```

### Address Extraction
```python
from advanced_scraper_features import AddressExtractor

extractor = AddressExtractor()
addresses = extractor.extract_addresses(html)

for addr in addresses:
    print(f"{addr.street}, {addr.city}, {addr.state} {addr.postal_code}")
```

### Company Info Extraction
```python
from advanced_scraper_features import CompanyInfoExtractor

extractor = CompanyInfoExtractor()
name = extractor.extract_company_name(html)
description = extractor.extract_company_description(html)
```

### Data Quality Scoring
```python
from advanced_scraper_features import DataQualityScorer

scorer = DataQualityScorer()
score = scorer.calculate_quality_score(
    emails=emails,
    phones=phones,
    addresses=addresses,
    company_name=name,
    company_description=desc,
    pages_scanned=pages
)
# Returns 0.0-1.0
```

### Parallel Processing
```python
# Scrape up to 150 concurrent URLs
results = pipeline.scrape_urls_parallel(
    urls=url_list,
    progress_callback=progress_func
)
```

### Advanced Retry Strategy
```python
from advanced_scraper_features import AdvancedRetryStrategy

strategy = AdvancedRetryStrategy(
    max_retries=5,
    initial_delay=1.0,
    backoff_factor=2.0
)

if strategy.should_retry(url):
    delay = strategy.get_retry_delay(url)
    time.sleep(delay)
    strategy.record_failure(url, reason)
```

## Configuration

### Pipeline
```python
AdvancedScraperPipeline(
    base_scraper,                    # Required
    max_workers=50,                  # 1-150
    max_pages_per_site=5,            # Pages per site
    enable_address_extraction=True,  # Extract addresses
    enable_company_info=True         # Extract company info
)
```

### Parallel Scraper
```python
ParallelScraper(
    max_workers=50,  # 1-150
    timeout=30       # Seconds
)
```

### Retry Strategy
```python
AdvancedRetryStrategy(
    max_retries=5,        # Max attempts
    initial_delay=1.0,    # Initial delay (s)
    max_delay=60.0,       # Max delay (s)
    backoff_factor=2.0    # Backoff multiplier
)
```

## Result Structure

```python
EnhancedScraperResult(
    url='https://example.com',
    status='success',
    emails=['contact@example.com'],
    phones=['415-123-4567'],
    addresses=[Address(...)],
    company_name='Example Corp',
    company_description='Tech company',
    pages_scraped={'homepage': True, 'contact': True},
    data_quality_score=0.88,
    confidence_score=0.85,
    pages_scanned=3,
    leadership_count=5,
    retry_count=0,
    fetch_mode='js_rendering',
    reason='Success',
    load_time=4.5
)
```

## Address Object

```python
Address(
    street='123 Main St',
    city='San Francisco',
    state='CA',
    postal_code='94105',
    country='USA',
    full_address='123 Main St, San Francisco, CA 94105',
    confidence_score=0.95
)
```

## Page Types

```python
PageType.HOMEPAGE      # /
PageType.CONTACT       # /contact, /contact-us
PageType.ABOUT         # /about, /about-us
PageType.TEAM          # /team, /our-team
PageType.CAREERS       # /careers, /jobs
PageType.SERVICES      # /services
PageType.BLOG          # /blog
```

## Performance

| Operation | Time |
|-----------|------|
| Address extraction | 1-5ms |
| Company info | 1-3ms |
| Page discovery | 5-10ms |
| Parallel overhead | Minimal |

## Common Tasks

### Scrape Single URL
```python
result = pipeline.scrape_url_advanced(url)
```

### Scrape Multiple URLs
```python
results = pipeline.scrape_urls_parallel(urls)
```

### Get High-Quality Results
```python
high_quality = [r for r in results if r.data_quality_score >= 0.8]
```

### Export to CSV
```python
import csv

with open('results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

### Get Addresses
```python
for result in results:
    for addr in result.addresses:
        print(f"{addr.street}, {addr.city}, {addr.state}")
```

### Monitor Progress
```python
def progress(completed, total):
    print(f"Progress: {completed}/{total}")

results = pipeline.scrape_urls_parallel(urls, progress_callback=progress)
```

### Retry Failed URLs
```python
strategy = AdvancedRetryStrategy()

for url in failed_urls:
    if strategy.should_retry(url):
        delay = strategy.get_retry_delay(url)
        time.sleep(delay)
        try:
            result = scraper.scrape_url(url)
            strategy.record_success(url)
        except Exception as e:
            strategy.record_failure(url, str(e))
```

## Data Quality Score Breakdown

| Component | Weight | Max Points |
|-----------|--------|-----------|
| Emails | 0.25 | 0.25 |
| Phones | 0.20 | 0.20 |
| Addresses | 0.15 | 0.15 |
| Company Info | 0.20 | 0.20 |
| Pages Scanned | 0.20 | 0.20 |
| **Total** | **1.0** | **1.0** |

## Retry Backoff Formula

```
delay = initial_delay * (backoff_factor ^ retry_count)
delay = min(delay, max_delay)
```

Example with defaults:
- Attempt 1: 1.0s
- Attempt 2: 2.0s
- Attempt 3: 4.0s
- Attempt 4: 8.0s
- Attempt 5: 16.0s

## Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logs from 'advanced_scraper' logger
```

## Examples

### Example 1: Basic
```python
pipeline = AdvancedScraperPipeline(base_scraper)
result = pipeline.scrape_url_advanced(url)
```

### Example 2: Parallel
```python
results = pipeline.scrape_urls_parallel(urls)
```

### Example 3: Address Extraction
```python
extractor = AddressExtractor()
addresses = extractor.extract_addresses(html)
```

### Example 4: Quality Scoring
```python
scorer = DataQualityScorer()
score = scorer.calculate_quality_score(...)
```

### Example 5: Retry Strategy
```python
strategy = AdvancedRetryStrategy()
if strategy.should_retry(url):
    delay = strategy.get_retry_delay(url)
```

## Supported Address Formats

- `123 Main St, San Francisco, CA 94105`
- `456 Oak Ave, New York, NY 10001`
- `P.O. Box 789, Los Angeles, CA 90001`
- `789 Elm St, Boston, MA`

## Validation

- US state abbreviation check
- Postal code format (5 or 5+4 digits)
- Street address presence
- City/state combination

## Troubleshooting

### High Memory Usage
- Reduce `max_workers`
- Disable unused features

### Slow Performance
- Disable address/company extraction
- Reduce `max_pages_per_site`
- Increase `max_workers`

### Timeout Errors
- Increase `timeout` value
- Reduce `max_workers`
- Check network connection

## Files

| File | Purpose |
|------|---------|
| `advanced_scraper_features.py` | Main module |
| `ADVANCED_SCRAPER_GUIDE.md` | Complete documentation |
| `advanced_scraper_example.py` | 8 runnable examples |
| `ADVANCED_SCRAPER_QUICK_REFERENCE.md` | This file |

## Key Features

✅ Multi-page scraping (5+ pages per site)
✅ Parallel processing (up to 150 concurrent URLs)
✅ Address extraction (structured data)
✅ Company information extraction
✅ Data quality scoring (0.0-1.0)
✅ Advanced retry logic (exponential backoff)
✅ Enhanced result structure
✅ Thread-safe operations
✅ Comprehensive logging
✅ Easy integration

## Support

- **Documentation:** ADVANCED_SCRAPER_GUIDE.md
- **Examples:** advanced_scraper_example.py
- **Source:** advanced_scraper_features.py

---

**Quick Start:** `python advanced_scraper_example.py`
