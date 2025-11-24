# Interactive Advanced Scraper Test Guide

## Quick Start

Run the interactive test script:

```bash
python interactive_advanced_test.py
```

## Features

### 1. Single URL Testing
Test any URL with the advanced scraper:

```
> https://example.com
```

Or just the domain (https will be added automatically):

```
> example.com
```

### 2. Sample URLs
Test pre-configured sample URLs by number:

```
> 1    # Tests https://graybox.co
> 2    # Tests https://sparkagency.com
> 3    # Tests https://thriveagency.com
> 4    # Tests https://websolutionagency.co
> 5    # Tests https://digitalmarketinggroup.com
```

### 3. Batch Testing
Test multiple URLs at once:

```
> batch
Enter URLs (one per line, empty line to finish):
> https://example1.com
> https://example2.com
> https://example3.com
> 
```

### 4. Exit
Stop the program:

```
> quit
```

## What You'll See

### Test Output

For each URL tested, you'll see:

**Basic Information:**
- Status (success/failed)
- Load time
- Fetch mode (fast_html, js_rendering, hard_mode)
- Reason for result

**Company Information:**
- Company name (if found)
- Company description (if found)

**Contact Data:**
- Number of emails found
- List of emails (up to 5 shown)
- Number of phones found
- List of phones (up to 5 shown)
- Number of addresses found
- List of addresses (up to 3 shown)

**Pages Scraped:**
- Homepage ✓/✗
- Contact page ✓/✗
- About page ✓/✗
- Team page ✓/✗
- Careers page ✓/✗
- Services page ✓/✗
- Blog page ✓/✗

**Quality Metrics:**
- Data Quality Score (0.0-1.0)
- Confidence Score (0.0-1.0)
- Pages Scanned
- Leadership Mentions
- Retry Count

**Quality Rating:**
- Excellent ⭐⭐⭐⭐⭐ (0.8-1.0)
- Good ⭐⭐⭐⭐ (0.6-0.8)
- Fair ⭐⭐⭐ (0.4-0.6)
- Poor ⭐⭐ (0.2-0.4)
- Very Poor ⭐ (0.0-0.2)

**Social Links:**
- LinkedIn, Instagram, GitHub, etc.

### CSV Export

Each test automatically exports results to a CSV file:

```
test_result_20251123_234429.csv
```

For batch tests:

```
batch_results_20251123_234429.csv
```

## Example Session

```
================================================================================
                    ADVANCED SCRAPER - INTERACTIVE TEST
================================================================================

Welcome to the Advanced Scraper Interactive Test!
Test the scraper with any URL you want.

Available sample URLs:
  1. https://graybox.co
  2. https://sparkagency.com
  3. https://thriveagency.com
  4. https://websolutionagency.co
  5. https://digitalmarketinggroup.com

Options:
  - Enter a URL to test
  - Enter a number (1-5) to test a sample URL
  - Type 'quit' to exit
  - Type 'batch' to test multiple URLs

> 1

================================================================================
                        TESTING: https://graybox.co
================================================================================
Started at: 2025-11-23 23:44:13

[1/4] Initializing scraper...
✓ Scraper initialized
[2/4] Scraping website...
✓ Scraping completed in 16.45s

RESULTS
-------

Basic Info:
  Status: success
  Load Time: 16.45s
  Fetch Mode: js_rendering
  Reason: Success

Company Info:
  Name: Not found
  Description: Not found

Contact Data:
  Emails: 4
    1. SalesRoundRobin@graybox.co
    2. paul@graybox.co
    3. info@graybox.co
    4. jobs@graybox.co
  Phones: 109
    1. 176-389-9640
    2. 158-572-7444
    3. 5567238593141
    4. 63947594
    5. 6641494
    ... and 104 more
  Addresses: 0

Pages Scraped:
  0/7 pages
    ✗ homepage
    ✗ contact
    ✗ about
    ✗ team
    ✗ careers
    ✗ services
    ✗ blog

Quality Metrics:
  Data Quality Score: 0.53/1.0
  Confidence Score: 0.70/1.0
  Pages Scanned: 2
  Leadership Mentions: 3
  Retry Count: 0
  Quality Rating: Fair ⭐⭐⭐

Social Links:
  None found

EXPORT
------

✓ Results exported to: test_result_20251123_234429.csv

SUMMARY
-------

✓ URL: https://graybox.co
✓ Status: success
✓ Emails: 4
✓ Phones: 109
✓ Addresses: 0
✓ Quality: 0.53
✓ CSV: test_result_20251123_234429.csv

================================================================================
                        TEST COMPLETED SUCCESSFULLY!
================================================================================

> quit

Goodbye!
```

## Tips

### 1. Test Different Types of Sites
- Marketing agencies (good for contact info)
- Tech companies (good for social links)
- Local businesses (good for addresses)
- E-commerce (good for company info)

### 2. Monitor Quality Scores
- High quality (0.8+): Excellent data
- Medium quality (0.5-0.8): Good data with some gaps
- Low quality (0.0-0.5): Limited data found

### 3. Check CSV Files
After testing, open the CSV files to see:
- All extracted data
- Quality scores
- Timestamps
- Fetch modes used

### 4. Batch Testing
Use batch mode to:
- Test multiple URLs at once
- Compare quality across sites
- Generate comprehensive reports
- Export all results to one file

## Troubleshooting

### Issue: Timeout Error
**Problem:** URL takes too long to load

**Solution:**
- Try a different URL
- Check your internet connection
- Some sites may have rate limiting

### Issue: No Data Found
**Problem:** Scraper returns empty results

**Solution:**
- Site may have strong protection
- Try a different URL
- Check if site is accessible in browser

### Issue: Low Quality Score
**Problem:** Quality score is very low

**Solution:**
- Site may not have contact info
- Try a business/company site
- Check if addresses are in different format

## CSV Output Format

Each CSV file contains:

```
url,status,emails,phones,addresses,company_name,company_description,
pages_scraped,data_quality_score,confidence_score,pages_scanned,
leadership_count,retry_count,fetch_mode,reason,load_time,validation_timestamp
```

Example row:

```
https://graybox.co,success,SalesRoundRobin@graybox.co; paul@graybox.co,
176-389-9640; 158-572-7444,123 Main St; San Francisco; CA; 94105,
Graybox Inc,Leading tech solutions,
{'homepage': True; 'contact': True},0.53,0.70,2,3,0,
js_rendering,Success,16.45,2025-11-23T23:44:29.517283
```

## Advanced Options

### Custom Timeout
Edit the script to change timeout:

```python
base_scraper = WebScraper(
    proxy_manager=proxy_manager,
    timeout=30,  # Change this value
    enable_precheck=True
)
```

### More Pages Per Site
Edit the script to scrape more pages:

```python
pipeline = AdvancedScraperPipeline(
    base_scraper=base_scraper,
    max_pages_per_site=10,  # Change this value
)
```

### Disable Features
Edit the script to disable features:

```python
pipeline = AdvancedScraperPipeline(
    base_scraper=base_scraper,
    enable_address_extraction=False,  # Disable address extraction
    enable_company_info=False         # Disable company info
)
```

## Summary

The interactive test script allows you to:
- ✅ Test any URL with advanced scraper
- ✅ See detailed results immediately
- ✅ Export results to CSV
- ✅ Test multiple URLs in batch
- ✅ Compare quality across sites
- ✅ Monitor scraper performance

Perfect for testing and validating the advanced scraper!

## Next Steps

1. Run: `python interactive_advanced_test.py`
2. Test a sample URL (enter 1-5)
3. Review the results
4. Check the CSV file
5. Test more URLs as needed
6. Export and analyze results

Enjoy testing! 🚀
