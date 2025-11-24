# Page Discovery Guide

This document explains how the scraper automatically discovers and scans relevant pages on websites.

## Overview

The Page Discovery system automatically identifies contact and team pages without manual configuration. It uses intelligent keyword matching, URL normalization, and deduplication to find relevant pages while preventing excessive scraping.

## Discovery Process

### 1. Link Extraction
The scraper extracts all links from the HTML:
```
Parse HTML → Find all <a> tags → Extract href attributes
```

### 2. URL Validation
Each link is validated:
- **Format Check**: Valid URL format
- **Domain Check**: Same domain as base URL
- **Exclusion Check**: Not in exclude patterns
- **Normalization**: Remove fragments, trailing slashes

### 3. Keyword Matching
URLs are matched against keyword lists:
- **Contact Pages**: contact, support, help, reach, get-in-touch, hello, talk, inquiry, message, email-us, call-us
- **Team Pages**: team, about, people, leadership, executives, management, founders, staff, employees, company

### 4. Deduplication
Duplicate URLs are removed:
- Case-insensitive comparison
- Normalized URL comparison
- Prevents scanning same page twice

### 5. Limiting
Discovery is limited to prevent excessive scraping:
- Maximum pages per site: configurable (default: 10)
- Maximum pages to scan: 5 per site
- Depth limit: 2 levels

## Contact Page Keywords

The scraper identifies contact pages using these keywords:

```
contact, support, help, reach, get-in-touch, hello, talk,
contact-us, contact_us, contactus, getintouch,
inquiry, inquiries, message, email-us, call-us
```

### Examples
- `https://example.com/contact` ✓
- `https://example.com/support` ✓
- `https://example.com/get-in-touch` ✓
- `https://example.com/hello` ✓
- `https://example.com/contact-us` ✓

## Team/Leadership Page Keywords

The scraper identifies team pages using these keywords:

```
team, about, people, leadership, executives, management, founders,
about-us, about_us, aboutus, our-team, our_team, ourteam,
staff, employees, team-members, leadership-team, executive-team,
meet-the-team, our-people, company
```

### Examples
- `https://example.com/team` ✓
- `https://example.com/about` ✓
- `https://example.com/leadership` ✓
- `https://example.com/our-team` ✓
- `https://example.com/executives` ✓

## Exclusion Patterns

The scraper excludes URLs matching these patterns:

```
File types: .pdf, .jpg, .png, .gif, .zip
Protocols: javascript:, mailto:, tel:
Special pages: /search, /results, /404, /error
Admin pages: /admin, /login, /register, /account
Fragments: URLs with # (anchors)
```

### Examples
- `https://example.com/contact.pdf` ✗ (PDF file)
- `javascript:void(0)` ✗ (JavaScript protocol)
- `mailto:contact@example.com` ✗ (Email link)
- `https://example.com/admin` ✗ (Admin page)
- `https://example.com/contact#form` ✗ (Fragment)

## URL Normalization

URLs are normalized for consistency:

```
Before:  https://example.com/contact/?utm_source=nav
After:   https://example.com/contact

Before:  https://example.com/about#team
After:   https://example.com/about

Before:  https://example.com/team/
After:   https://example.com/team
```

## Deduplication

Duplicate URLs are detected and removed:

```
https://example.com/contact
https://example.com/Contact      → Deduplicated (case)
https://example.com/contact/     → Deduplicated (trailing slash)
https://example.com/contact?     → Deduplicated (empty query)
```

## Configuration

### Command Line Options

```bash
# Default: discover up to 10 pages per site
python scraper.py urls.txt

# Limit discovery to 5 pages per site
python scraper.py urls.txt --max-pages 5

# Limit discovery to 3 pages per site (minimal)
python scraper.py urls.txt --max-pages 3

# Unlimited discovery (not recommended)
python scraper.py urls.txt --max-pages 1000
```

### Python API

```python
from scraper import PageDiscovery

# Create discovery system
discovery = PageDiscovery(max_pages=10)

# Discover all pages
contact_urls, team_urls = discovery.discover_all_pages(base_url, html)

# Discover specific type
contact_only = discovery.discover_pages(base_url, html, 'contact')
team_only = discovery.discover_pages(base_url, html, 'team')
```

## Discovery Limits

### Per-Site Limits
- **Max pages to discover**: 10 (configurable)
- **Max pages to scan**: 5 (hardcoded)
- **Discovery depth**: 2 levels (hardcoded)

### Why These Limits?
- Prevents crawling entire website
- Reduces bandwidth usage
- Speeds up scraping
- Focuses on most relevant pages

### Adjusting Limits

```bash
# Conservative: scan fewer pages
python scraper.py urls.txt --max-pages 3

# Aggressive: scan more pages
python scraper.py urls.txt --max-pages 20

# Balanced (default)
python scraper.py urls.txt --max-pages 10
```

## Output Analysis

### Pages Scanned Column
The CSV output includes `pages_scanned` which shows:
- 1: Only main page scanned
- 2-6: Main page + discovered pages scanned

### Example Output
```csv
url,pages_scanned,emails,phones,leadership_count
https://example.com,3,5,2,3
https://github.com,2,1,0,2
https://stackoverflow.com,1,0,0,0
```

## Performance Impact

### Discovery Time
- Minimal: ~0.1-0.5 seconds per page
- Includes: HTML parsing, URL extraction, keyword matching

### Bandwidth Impact
- Main page: ~100-500 KB
- Per discovered page: ~50-300 KB
- Total per site: ~500 KB - 2 MB (with 5 pages scanned)

### Optimization Tips
- Use `--max-pages 3` for speed
- Use `--max-pages 10` for balance
- Use `--max-pages 20` for thoroughness

## Examples

### Example 1: Basic Discovery
```bash
python scraper.py https://example.com
# Discovers and scans up to 5 contact/team pages
```

### Example 2: Conservative Discovery
```bash
python scraper.py urls.txt --max-pages 3
# Discovers up to 3 pages per site
# Scans up to 3 pages per site
```

### Example 3: Aggressive Discovery
```bash
python scraper.py urls.txt --max-pages 20
# Discovers up to 20 pages per site
# Scans up to 5 pages per site (hardcoded limit)
```

## Troubleshooting

### Not Finding Contact Pages
- Check if site uses different keywords
- Verify links are in HTML (not JavaScript-generated)
- Check if pages are excluded by patterns

### Finding Too Many Pages
- Use `--max-pages 3` to limit discovery
- Check if keywords are too broad
- Verify exclusion patterns

### Slow Discovery
- Reduce `--max-pages` to scan fewer pages
- Use `--threads 3` to reduce concurrent requests
- Check network connectivity

## Best Practices

1. **Start with defaults**: `--max-pages 10` is balanced
2. **Monitor logs**: Check `scraper.log` for discovery details
3. **Test first**: Run on small URL set before full scrape
4. **Adjust as needed**: Increase for thorough scraping, decrease for speed
5. **Use keywords**: Verify keywords match your target sites

## Advanced Usage

### Custom Keyword Matching
To add custom keywords, modify the PageDiscovery class:

```python
class PageDiscovery:
    CONTACT_KEYWORDS = [
        'contact', 'support', 'help',
        'custom-keyword'  # Add here
    ]
    
    TEAM_KEYWORDS = [
        'team', 'about', 'people',
        'custom-team-keyword'  # Add here
    ]
```

### Custom Exclusion Patterns
To add custom exclusion patterns:

```python
class PageDiscovery:
    EXCLUDE_PATTERNS = [
        r'\.pdf$', r'\.jpg$',
        r'/custom-exclude'  # Add here
    ]
```

## Statistics

### Typical Discovery Results
- **Small sites** (< 50 pages): 2-5 contact/team pages found
- **Medium sites** (50-500 pages): 5-10 contact/team pages found
- **Large sites** (> 500 pages): 10+ contact/team pages found

### Typical Scan Results
- **Contact pages**: 2-5 emails, 0-2 phone numbers
- **Team pages**: 5-20 emails, 0-5 phone numbers
- **Leadership pages**: 3-10 leadership mentions

## Related Documentation

- See [FETCH_MODES.md](FETCH_MODES.md) for fetch mode details
- See [README.md](README.md) for general usage
- Check `scraper.log` for detailed discovery logs
