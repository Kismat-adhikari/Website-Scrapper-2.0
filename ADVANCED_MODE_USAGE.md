# Advanced Mode - Usage Guide

The advanced features are now integrated into the main scraper! You can use them directly from the command line.

## Quick Start

### Run Advanced Mode

```bash
python scraper.py --advanced
```

That's it! You'll enter interactive advanced mode where you can:
- Paste URLs one at a time
- Get detailed results with quality scoring
- Extract company info, addresses, emails, phones
- Scrape multiple pages per site
- See results in real-time

## How to Use

### 1. Start Advanced Mode

```bash
python scraper.py --advanced
```

You'll see:

```
======================================================================
    ADVANCED MODE - Multi-Page Scraping with Quality Scoring
======================================================================
Commands:
  - Paste a URL and press Enter to scrape it
  - Type 'quit' or 'exit' to stop
  - Type 'results' to view current results
  - Type 'clear' to clear results
Results will be saved to: results_advanced_20251123_234429.csv
======================================================================
```

### 2. Enter a URL

```
Enter URL (or command): https://graybox.co
```

Or just the domain (https added automatically):

```
Enter URL (or command): graybox.co
```

### 3. See Results

```
Scraping https://graybox.co with advanced features...
✓ Status: success
  Company: Graybox Inc
  Emails: 4
  Phones: 109
  Addresses: 1
  Quality Score: 0.75/1.0
  Pages Scraped: 3
```

### 4. View All Results

```
Enter URL (or command): results

Scraped 3 URLs so far:
  https://graybox.co: success (Quality: 0.75)
  https://sparkagency.com: success (Quality: 0.68)
  https://thriveagency.com: success (Quality: 0.82)
```

### 5. Clear Results

```
Enter URL (or command): clear
Results cleared
```

### 6. Exit and Save

```
Enter URL (or command): quit

✓ Results saved to results_advanced_20251123_234429.csv
✓ Total URLs scraped: 3

Summary:
  Successful: 3/3
  Total Emails: 12
  Total Phones: 287
  Average Quality: 0.75
```

## What You Get

### For Each URL:

**Status & Performance:**
- Status (success/failed)
- Company name
- Company description

**Contact Information:**
- Emails found (with count)
- Phones found (with count)
- Addresses found (with count)

**Quality Metrics:**
- Data Quality Score (0.0-1.0)
- Pages Scraped (count)
- Confidence Score

**Multi-Page Scraping:**
- Homepage ✓/✗
- Contact page ✓/✗
- About page ✓/✗
- Team page ✓/✗
- Careers page ✓/✗

### CSV Export:

All results automatically exported to timestamped CSV file with:
- URL
- Status
- Emails (semicolon-separated)
- Phones (semicolon-separated)
- Addresses (semicolon-separated)
- Company name
- Company description
- Pages scraped
- Data quality score
- Confidence score
- And more...

## Examples

### Example 1: Single URL

```bash
$ python scraper.py --advanced

Enter URL (or command): graybox.co
Scraping https://graybox.co with advanced features...
✓ Status: success
  Company: Graybox Inc
  Emails: 4
  Phones: 109
  Addresses: 1
  Quality Score: 0.75/1.0
  Pages Scraped: 3

Enter URL (or command): quit
✓ Results saved to results_advanced_20251123_234429.csv
```

### Example 2: Multiple URLs

```bash
$ python scraper.py --advanced

Enter URL (or command): sparkagency.com
✓ Status: success
  Emails: 2
  Quality Score: 0.68/1.0

Enter URL (or command): thriveagency.com
✓ Status: success
  Emails: 6
  Quality Score: 0.82/1.0

Enter URL (or command): results
Scraped 2 URLs so far:
  https://sparkagency.com: success (Quality: 0.68)
  https://thriveagency.com: success (Quality: 0.82)

Enter URL (or command): quit
✓ Results saved to results_advanced_20251123_234429.csv
Summary:
  Successful: 2/2
  Total Emails: 8
  Total Phones: 65
  Average Quality: 0.75
```

## Features

### Multi-Page Scraping
- Automatically discovers related pages
- Scrapes contact, about, team, careers pages
- Merges data from multiple pages
- Improves data completeness

### Quality Scoring
- Calculates 0.0-1.0 quality score
- Based on:
  - Emails found (0-0.25)
  - Phones found (0-0.20)
  - Addresses found (0-0.15)
  - Company info (0-0.20)
  - Pages scanned (0-0.20)

### Address Extraction
- Extracts structured addresses
- Validates US state abbreviations
- Validates postal code format
- Confidence scoring per address

### Company Information
- Extracts company name
- Extracts company description
- From meta tags, titles, descriptions

### Parallel Processing
- Up to 5 concurrent workers
- Efficient resource usage
- Progress tracking

## Timeout

- Each URL has 120-second timeout
- If scraping takes longer, it will timeout
- Try a different URL if timeout occurs

## Tips

### 1. Test Different Sites
- Marketing agencies (good for contact info)
- Tech companies (good for social links)
- Local businesses (good for addresses)
- E-commerce (good for company info)

### 2. Monitor Quality Scores
- High quality (0.8+): Excellent data
- Medium quality (0.5-0.8): Good data
- Low quality (0.0-0.5): Limited data

### 3. Check CSV Files
After testing, open the CSV file to see:
- All extracted data
- Quality scores
- Timestamps
- Fetch modes used

### 4. Batch Testing
Test multiple URLs one after another:
```
Enter URL (or command): url1.com
Enter URL (or command): url2.com
Enter URL (or command): url3.com
Enter URL (or command): results
Enter URL (or command): quit
```

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

## Command Reference

| Command | Description |
|---------|-------------|
| `https://example.com` | Scrape this URL |
| `example.com` | Scrape (https added automatically) |
| `results` | View all scraped URLs so far |
| `clear` | Clear all results |
| `quit` or `exit` | Stop and save results |

## Output Files

Each session creates a timestamped CSV file:

```
results_advanced_20251123_234429.csv
```

Contains all scraped data ready for analysis!

## Summary

Advanced mode provides:
- ✅ Multi-page scraping
- ✅ Quality scoring
- ✅ Address extraction
- ✅ Company information
- ✅ Real-time results
- ✅ Automatic CSV export
- ✅ Easy to use

Perfect for testing and validating the advanced scraper!

## Next Steps

1. Run: `python scraper.py --advanced`
2. Enter a URL
3. Review the results
4. Check the CSV file
5. Test more URLs as needed

Enjoy! 🚀
