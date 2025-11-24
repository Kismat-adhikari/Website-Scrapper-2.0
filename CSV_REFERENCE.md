# CSV Output Reference

Quick reference for CSV output columns and format.

## Required Columns

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| url | string | https://example.com | Target URL |
| status | string | success | success/failed/skipped |
| emails | list | ['email@example.com'] | Python list format |
| phones | list | ['555-123-4567'] | Python list format |
| pages_scanned | int | 3 | Number of pages |
| leadership_count | int | 5 | Leadership mentions |
| email_list | string | email@example.com | Semicolon-separated |
| confidence_score | float | 0.82 | 0.0-1.0 range |
| reason | string | Success | Status message |

## Additional Columns

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| load_time | float | 1.23 | Seconds |
| ssl_valid | bool | true | Certificate valid |
| bot_protection | string | cloudflare | Protection type |
| scrape_mode | string | normal | Scrape mode |
| fetch_mode | string | fast_html | Fetch method |
| retry_count | int | 0 | Retries |
| social_links | string | {"linkedin": [...]} | JSON format |
| phone_list | string | 555-123-4567 | Semicolon-separated |

## Column Order

```
url, status, emails, phones, pages_scanned, leadership_count,
email_list, confidence_score, reason, load_time, ssl_valid,
bot_protection, scrape_mode, fetch_mode, retry_count,
social_links, phone_list
```

## Data Types

### String Columns
- url, status, reason, bot_protection, scrape_mode, fetch_mode
- email_list, phone_list, social_links

### Integer Columns
- pages_scanned, leadership_count, retry_count

### Float Columns
- confidence_score, load_time

### Boolean Columns
- ssl_valid

### List Columns (Python format)
- emails, phones

## Status Values

| Value | Meaning |
|-------|---------|
| success | Successfully scraped |
| failed | Failed after retries |
| skipped | Skipped by pre-check |

## Scrape Mode Values

| Value | Meaning |
|-------|---------|
| normal | Standard HTML fetch |
| browser | Headless browser |
| slow_mode | Extended timeout |
| skip | Skipped |

## Fetch Mode Values

| Value | Meaning |
|-------|---------|
| fast_html | Standard requests |
| js_rendering | Playwright browser |
| hard_mode | Anti-blocking |

## Bot Protection Values

| Value | Meaning |
|-------|---------|
| cloudflare | Cloudflare detected |
| captcha | CAPTCHA detected |
| 403 | HTTP 403 |
| 429 | HTTP 429 |
| protection | Generic protection |
| (empty) | No protection |

## Confidence Score Ranges

| Range | Level | Meaning |
|-------|-------|---------|
| 0.75-1.00 | High | Excellent data |
| 0.50-0.74 | Medium | Good data |
| 0.25-0.49 | Low | Limited data |
| 0.00-0.24 | Very Low | Minimal data |

## Example Rows

### Successful
```
https://example.com,success,"['contact@example.com']","['555-123-4567']",3,5,contact@example.com,0.82,Success,1.23,true,,normal,fast_html,0,"{""linkedin"": [""https://linkedin.com/company/example""]}",555-123-4567
```

### Failed
```
https://blocked.com,failed,[],[],1,0,,0.0,All fetch modes failed: bot_detection (retries: 5),5.0,true,cloudflare,browser,hard_mode,5,"{}",
```

### Skipped
```
https://invalid.com,skipped,[],[],0,0,,0.0,SSL certificate invalid,0.0,false,,skip,fast_html,0,"{}",
```

## UTF-8 Encoding

All CSV files are saved with UTF-8 encoding:
- Supports international characters
- Compatible with all systems
- No encoding errors

## Reading in Python

```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['url'], row['status'], row['confidence_score'])
```

## Reading in Pandas

```python
import pandas as pd

df = pd.read_csv('results.csv', encoding='utf-8')
print(df.head())
```

## Filtering Examples

### High Confidence
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    high = [r for r in reader if float(r['confidence_score']) >= 0.75]
```

### Successful Only
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    success = [r for r in reader if r['status'] == 'success']
```

### With Emails
```python
import csv
import ast

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    with_emails = [r for r in reader if ast.literal_eval(r['emails'])]
```

## Analysis Examples

### Count by Status
```python
import csv
from collections import Counter

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    statuses = Counter(r['status'] for r in reader)
    print(statuses)
```

### Average Confidence
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    scores = [float(r['confidence_score']) for r in reader]
    avg = sum(scores) / len(scores)
    print(f"Average: {avg:.2f}")
```

### Failure Reasons
```python
import csv
from collections import Counter

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    failed = [r for r in reader if r['status'] == 'failed']
    reasons = Counter(r['reason'] for r in failed)
    for reason, count in reasons.most_common():
        print(f"{reason}: {count}")
```

## Export Examples

### To Excel
```python
import pandas as pd

df = pd.read_csv('results.csv', encoding='utf-8')
df.to_excel('results.xlsx', index=False)
```

### To JSON
```python
import pandas as pd

df = pd.read_csv('results.csv', encoding='utf-8')
df.to_json('results.json', orient='records')
```

### Filtered CSV
```python
import csv

with open('results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r['status'] == 'success']

with open('success_only.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
```

## Troubleshooting

### Encoding Issues
- Always use `encoding='utf-8'`
- In Excel, select UTF-8 during import
- Check file properties for encoding

### List Format Issues
- Use `ast.literal_eval()` to parse lists
- Or use `json.loads()` for JSON
- Don't use `eval()` for security

### Missing Columns
- Check if scraper ran successfully
- Verify all results were saved
- Check for errors in logs

### Large Files
- Use pandas for better performance
- Consider splitting into batches
- Use compression for storage

## Best Practices

1. **Always backup**: Keep copies of results
2. **Use UTF-8**: Ensures compatibility
3. **Validate data**: Check for anomalies
4. **Document runs**: Note parameters
5. **Archive results**: Store historical data

## Related Files

- [CSV_OUTPUT.md](CSV_OUTPUT.md) - Detailed CSV guide
- [README.md](README.md) - Feature overview
- [QUICK_START.md](QUICK_START.md) - Quick start

## Summary

The CSV output includes:
- All required columns
- UTF-8 encoding
- Easy analysis
- Excel/Sheets compatible
- Production-ready format

Use for reporting, analysis, and further processing.
