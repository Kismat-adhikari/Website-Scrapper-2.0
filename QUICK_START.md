# Quick Start Guide

Get up and running with the web scraper in minutes.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For Playwright support (optional but recommended)
playwright install chromium
```

## Basic Usage

### Scrape a Single URL
```bash
python scraper.py https://example.com
```

### Scrape Multiple URLs from File
```bash
python scraper.py urls.txt
```

### View Results
```bash
# Results are saved to results.csv
cat results.csv
```

## Common Use Cases

### Case 1: Quick Scrape (Speed-Focused)
```bash
python scraper.py urls.txt --threads 10 --max-pages 3
```
- Fast HTML mode preferred
- Minimal page discovery
- Good for large URL lists

### Case 2: Thorough Scrape (Quality-Focused)
```bash
python scraper.py urls.txt --threads 3 --max-pages 10 --timeout 20
```
- Discovers more pages
- Longer timeout for slow sites
- Better data quality

### Case 3: Protected Sites (Reliability-Focused)
```bash
python scraper.py urls.txt --proxy-file proxies.txt --hard-mode-delay 1.5
```
- Uses proxies
- Hard mode for protection
- Slower but more reliable

### Case 4: Large Scale (Production)
```bash
python scraper.py urls.txt --threads 20 --max-pages 5 --proxy-file proxies.txt
```
- High parallelism
- Balanced discovery
- Proxy rotation

## Output

The scraper generates `results.csv` with these columns:

```
url                    - Target URL
status                 - success/failed/skipped
emails                 - List of emails found
phones                 - List of phone numbers
pages_scanned          - Number of pages scanned
leadership_count       - Leadership mentions
email_list             - Semicolon-separated emails
confidence_score       - 0-1 confidence score
reason                 - Success or failure reason
load_time              - Page load time
ssl_valid              - SSL certificate valid
bot_protection         - Protection type detected
scrape_mode            - Scrape mode used
fetch_mode             - Fetch method used
retry_count            - Number of retries
```

## Configuration

### Command Line Options

```bash
# URLs to scrape
python scraper.py <url_or_file>

# Output file (default: results.csv)
--output results.csv

# Number of threads (default: 5)
--threads 10

# Request timeout in seconds (default: 10)
--timeout 20

# Proxy file (optional)
--proxy-file proxies.txt

# Max pages to discover per site (default: 10)
--max-pages 5

# Hard mode delay in seconds (default: 0.5)
--hard-mode-delay 1.5

# Disable pre-check system
--no-precheck
```

## Proxy Configuration

Create `proxies.txt` with one proxy per line:

```
# Basic proxy
192.168.1.1:8080

# Authenticated proxy
10.0.0.1:3128:username:password

# Comments start with #
```

## Logging

Logs are written to `scraper.log`:

```bash
# View logs in real-time
tail -f scraper.log

# View last 50 lines
tail -50 scraper.log

# Search for errors
grep ERROR scraper.log
```

## Examples

### Example 1: Single URL
```bash
python scraper.py https://example.com
```

### Example 2: File with URLs
```bash
# Create urls.txt
echo "https://example.com" > urls.txt
echo "https://github.com" >> urls.txt
echo "https://stackoverflow.com" >> urls.txt

# Scrape all URLs
python scraper.py urls.txt
```

### Example 3: With Proxies
```bash
# Create proxies.txt
echo "192.168.1.1:8080" > proxies.txt
echo "10.0.0.1:3128:user:pass" >> proxies.txt

# Scrape with proxies
python scraper.py urls.txt --proxy-file proxies.txt
```

### Example 4: Custom Configuration
```bash
python scraper.py urls.txt \
  --output my_results.csv \
  --threads 15 \
  --timeout 15 \
  --max-pages 8 \
  --hard-mode-delay 1.0
```

## Troubleshooting

### No Results
- Check if URLs are valid
- Check `scraper.log` for errors
- Try with `--no-precheck` to skip validation

### Slow Scraping
- Reduce `--threads` to avoid rate limiting
- Use `--max-pages 3` to limit discovery
- Check network connectivity

### High Failure Rate
- Use `--proxy-file proxies.txt` for proxies
- Increase `--timeout` for slow sites
- Increase `--hard-mode-delay` for protected sites

### Memory Issues
- Reduce `--threads` to use less memory
- Process URLs in smaller batches

## Performance Benchmarks

### Typical Performance
- **Fast HTML**: 0.5-2 seconds per page
- **JS Rendering**: 3-8 seconds per page
- **Hard Mode**: 5-30 seconds per page (with retries)

### Typical Results
- **Emails per site**: 1-10
- **Phone numbers per site**: 0-3
- **Leadership mentions**: 0-20

## Next Steps

1. **Read the full documentation**:
   - [README.md](README.md) - Full feature overview
   - [FETCH_MODES.md](FETCH_MODES.md) - Fetch mode details
   - [PAGE_DISCOVERY.md](PAGE_DISCOVERY.md) - Page discovery details

2. **Explore examples**:
   - Run `python example_usage.py` to see available examples
   - Uncomment examples in `example_usage.py` to run them

3. **Optimize for your use case**:
   - Adjust threads, timeout, and delays
   - Use proxies for protected sites
   - Configure page discovery limits

## Support

For issues or questions:
1. Check `scraper.log` for error messages
2. Review the documentation files
3. Check the examples in `example_usage.py`
4. Verify proxy configuration if using proxies

## Tips & Tricks

### Tip 1: Test First
Always test on a small URL set before running large scrapes:
```bash
echo "https://example.com" > test.txt
python scraper.py test.txt
```

### Tip 2: Monitor Progress
Watch the logs while scraping:
```bash
tail -f scraper.log
```

### Tip 3: Adjust for Site Type
- **Static sites**: Use `--threads 20 --max-pages 3`
- **Dynamic sites**: Use `--threads 5 --max-pages 10`
- **Protected sites**: Use `--proxy-file proxies.txt --hard-mode-delay 1.5`

### Tip 4: Batch Processing
Process large URL lists in batches:
```bash
# Split urls.txt into batches
split -l 100 urls.txt batch_

# Process each batch
for file in batch_*; do
  python scraper.py $file --output results_$file.csv
done
```

### Tip 5: Analyze Results
```bash
# Count successful scrapes
grep "success" results.csv | wc -l

# Find sites with emails
grep -v "^$" results.csv | grep -v "emails" | wc -l

# Export just URLs and emails
cut -d',' -f1,7 results.csv > urls_and_emails.csv
```
