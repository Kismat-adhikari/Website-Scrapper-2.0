# CSV Output Guide

Complete guide to the CSV output format and columns.

## Overview

The scraper saves all results to a CSV file with UTF-8 encoding. The default output file is `results.csv`.

## CSV Columns

### Core Information
- **url**: Target URL (string)
- **status**: Scraping status (success/failed/skipped)

### Contact Information
- **emails**: List of extracted emails (Python list format)
- **phones**: List of extracted phone numbers (Python list format)
- **email_list**: Semicolon-separated email addresses (string)
- **phone_list**: Semicolon-separated phone numbers (string)

### Extraction Results
- **pages_scanned**: Number of pages scanned (integer)
- **leadership_count**: Count of leadership title mentions (integer)
- **social_links**: JSON object with social media links (JSON string)

### Quality Metrics
- **confidence_score**: Confidence score 0.0-1.0 (float)
- **reason**: Success message or failure reason (string)

### Technical Details
- **load_time**: Page load time in seconds (float)
- **ssl_valid**: SSL certificate validity (boolean)
- **bot_protection**: Detected bot protection type (string or null)
- **scrape_mode**: Scrape mode used (normal/browser/slow_mode/skip)
- **fetch_mode**: Fetch method used (fast_html/js_rendering/hard_mode)
- **retry_count**: Number of retries attempted (integer)

## Column Details

### Status Values
- `success`: Successfully scraped and extracted data
- `failed`: Failed after all retry attempts
- `skipped`: Skipped due to pre-check failure

### Scrape Mode Values
- `normal`: Standard HTML fetch
- `browser`: Headless browser mode
- `slow_mode`: Extended timeout browser mode
- `skip`: Skipped

### Fetch Mode Values
- `fast_html`: Standard requests.get
- `js_rendering`: Playwright headless browser
- `hard_mode`: Anti-blocking techniques

### Bot Protection Values
- `cloudflare`: Cloudflare detected
- `captcha`: CAPTCHA detected
- `403`: HTTP 403 Forbidden
- `429`: HTTP 429 Rate Limited
- `protection`: Generic bot protection
- `null`: No protection detected

## Example CSV Output

### Header Row
```
url,status,emails,phones,pages_scanned,leadership_count,email_list,confidence_score,reason,load_time,ssl_valid,bot_protection,scrape_mode,fetch_mode,retry_count,social_links,phone_list
```

### Data Rows

**Successful Scrape**:
```
https://example.com,success,"['contact@example.com', 'sales@example.com']","['555-123-4567', '555-987-6543']",3,5,contact@example.com; sales@example.com,0.82,Success,1.23,true,,normal,fast_html,0,"{""linkedin"": [""https://linkedin.com/company/example""], ""twitter"": [""https://twitter.com/example""]}",555-123-4567; 555-987-6543
```

**Failed Scrape**:
```
https://blocked.com,failed,[],[],1,0,,0.0,All fetch modes failed: bot_detection (retries: 5),5.0,true,cloudflare,browser,hard_mode,5,"{}",
```

**Skipped Scrape**:
```
https://invalid.com,skipped,[],[],0,0,,0.0,SSL certificate invalid,0.0,false,,skip,fast_html,0,"{}",
```

## Data Format Details

### Email List Format
- Python list format in CSV: `['email1@example.com', 'email2@example.com']`
- Semicolon-separated in `email_list`: `email1@example.com; email2@example.com`

### Phone List Format
- Python list format in CSV: `['555-123-4567', '555-987-6543']`
- Semicolon-separated in `phone_list`: `555-123-4567; 555-987-6543`

### Social Links Format
- JSON object: `{"linkedin": ["url1", "url2"], "twitter": ["url3"]}`
- Empty object if none found: `{}`

### Confidence Score Format
- Float between 0.0 and 1.0
- Examples: 0.0, 0.25, 0.50, 0.75, 1.0

## UTF-8 Encoding

The CSV file is saved with UTF-8 encoding to ensure:
- Compatibility with all systems
- Support for international characters
- Proper handling of special characters
- No encoding errors

### Encoding Verification

To verify UTF-8 encoding:
```bash
# Linux/Mac
file results.csv
# Output: results.csv: UTF-8 Unicode text

# Python
import csv
with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)
```

## Reading CSV Files

### Python
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"URL: {row['url']}")
        print(f"Status: {row['status']}")
        print(f"Emails: {row['email_list']}")
        print(f"Confidence: {row['confidence_score']}")
```

### Pandas
```python
import pandas as pd

df = pd.read_csv('results.csv', encoding='utf-8')
print(df.head())
print(df.describe())
```

### Excel
1. Open Excel
2. File → Open
3. Select `results.csv`
4. Choose UTF-8 encoding
5. Click OK

### Google Sheets
1. Create new spreadsheet
2. File → Import → Upload
3. Select `results.csv`
4. Choose "Replace spreadsheet"
5. Click Import

## Analyzing Results

### Count Successful Scrapes
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    success_count = sum(1 for row in reader if row['status'] == 'success')
    print(f"Successful: {success_count}")
```

### Find High Confidence Results
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    high_confidence = [row for row in reader if float(row['confidence_score']) >= 0.75]
    print(f"High confidence: {len(high_confidence)}")
```

### Extract All Emails
```python
import csv
import ast

emails = set()
with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email_list = ast.literal_eval(row['emails'])
        emails.update(email_list)

print(f"Total unique emails: {len(emails)}")
for email in sorted(emails):
    print(email)
```

### Find Failed Sites
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    failed = [row for row in reader if row['status'] == 'failed']
    
    # Group by reason
    reasons = {}
    for row in failed:
        reason = row['reason']
        reasons[reason] = reasons.get(reason, 0) + 1
    
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"{reason}: {count}")
```

## CSV Customization

### Custom Output File
```bash
python scraper.py urls.txt --output my_results.csv
```

### Batch Processing
```bash
# Process multiple URL files
for file in urls_*.txt; do
    python scraper.py $file --output results_$file.csv
done

# Combine results
cat results_*.csv > combined_results.csv
```

### Filtering Results
```python
import csv

# Read original
with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Filter successful with high confidence
filtered = [r for r in rows if r['status'] == 'success' and float(r['confidence_score']) >= 0.75]

# Write filtered
with open('filtered_results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(filtered)
```

## Troubleshooting

### CSV Not Created
- Check if scraper ran successfully
- Verify output file path is writable
- Check logs for errors

### Encoding Issues
- Ensure file is opened with UTF-8 encoding
- Use `encoding='utf-8'` in Python
- In Excel, select UTF-8 during import

### Special Characters
- UTF-8 handles all special characters
- No need for escaping
- Works with international characters

### Large Files
- CSV can handle large datasets
- Use pandas for better performance with large files
- Consider splitting into multiple files

## Performance

### File Size
- Typical: 1-10 MB for 1000-10000 URLs
- Depends on data extracted
- Compression: ~20-30% with gzip

### Writing Speed
- ~100-1000 rows per second
- Depends on system performance
- Minimal impact on scraping

## Best Practices

1. **Always use UTF-8**: Ensures compatibility
2. **Backup results**: Keep copies of CSV files
3. **Validate data**: Check for anomalies
4. **Archive results**: Store historical data
5. **Document runs**: Note date, parameters, results

## Related Documentation

- See [README.md](README.md) for feature overview
- See [QUICK_START.md](QUICK_START.md) for usage examples
- See [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md) for data details
- Check `scraper.log` for detailed logs

## Summary

The CSV output provides:
- Complete scraping results
- UTF-8 encoding for compatibility
- All required columns
- Easy analysis and filtering
- Integration with Excel, Sheets, Pandas
- Production-ready format

Use the CSV for reporting, analysis, and further processing.
