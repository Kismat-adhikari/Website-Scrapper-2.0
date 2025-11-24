# Logging and Analysis Guide

Comprehensive guide to the scraper's logging system and failure analysis.

## Overview

The scraper maintains three detailed log files for tracking, monitoring, and analysis:

1. **scraper.log** - General execution log
2. **scraper_attempts.log** - Detailed attempt tracking
3. **scraper_failures.log** - Failed URLs and reasons

## Log Files

### 1. scraper.log (General Log)

**Purpose**: General execution information and errors

**Format**: `timestamp - level - message`

**Example**:
```
2024-01-15 10:30:45,123 - INFO - Loaded 10 URLs to scrape
2024-01-15 10:30:46,234 - INFO - Starting scrape for https://example.com
2024-01-15 10:30:47,345 - DEBUG - Fast HTML attempt 1 failed for https://example.com: timeout
2024-01-15 10:30:48,456 - INFO - Fast HTML fetch succeeded for https://example.com on attempt 2
2024-01-15 10:30:49,567 - INFO - Completed: https://example.com - Status: success
```

### 2. scraper_attempts.log (Detailed Attempts)

**Purpose**: Track every scraping attempt with full details

**Format**: `timestamp - URL | Status | Mode | Retries | Pages | Emails | Phones | Confidence | LoadTime | Reason`

**Example**:
```
2024-01-15 10:30:49,567 - URL: https://example.com | Status: success | Mode: fast_html | Retries: 1 | Pages: 3 | Emails: 5 | Phones: 2 | Confidence: 0.82 | LoadTime: 1.23s | Reason: Success
2024-01-15 10:30:50,678 - URL: https://github.com | Status: success | Mode: js_rendering | Retries: 0 | Pages: 2 | Emails: 1 | Phones: 0 | Confidence: 0.65 | LoadTime: 5.45s | Reason: Success
2024-01-15 10:30:51,789 - URL: https://blocked.com | Status: failed | Mode: hard_mode | Retries: 5 | Pages: 1 | Emails: 0 | Phones: 0 | Confidence: 0.00 | LoadTime: 25.00s | Reason: All fetch modes failed: bot_detection (retries: 5)
```

### 3. scraper_failures.log (Failure Analysis)

**Purpose**: Track failed URLs for analysis and improvement

**Format**: `timestamp - URL | Reason | Mode | Retries | BotProtection | SSLValid`

**Example**:
```
2024-01-15 10:30:51,789 - URL: https://blocked.com | Reason: All fetch modes failed: bot_detection (retries: 5) | Mode: hard_mode | Retries: 5 | BotProtection: cloudflare | SSLValid: true
2024-01-15 10:30:52,890 - URL: https://timeout.com | Reason: All fetch modes failed: timeout (retries: 5) | Mode: hard_mode | Retries: 5 | BotProtection: null | SSLValid: true
2024-01-15 10:30:53,901 - URL: https://ssl-error.com | Reason: SSL certificate invalid | Mode: skip | Retries: 0 | BotProtection: null | SSLValid: false
```

## Analyzing Logs

### Count Successful Scrapes

```bash
grep "Status: success" scraper_attempts.log | wc -l
```

### Count Failed Scrapes

```bash
grep "Status: failed" scraper_attempts.log | wc -l
```

### Find Most Common Failure Reasons

```bash
grep "URL:" scraper_failures.log | cut -d'|' -f2 | sort | uniq -c | sort -rn
```

### Find Sites with Bot Protection

```bash
grep "BotProtection: cloudflare" scraper_failures.log
grep "BotProtection: captcha" scraper_failures.log
```

### Find Timeout Issues

```bash
grep "timeout" scraper_failures.log
```

### Find SSL Errors

```bash
grep "SSLValid: false" scraper_failures.log
```

## Python Analysis

### Parse Attempts Log

```python
import re
from datetime import datetime

attempts = []
with open('scraper_attempts.log') as f:
    for line in f:
        # Parse: timestamp - URL: ... | Status: ... | Mode: ... | ...
        match = re.search(r'URL: (.*?) \| Status: (.*?) \| Mode: (.*?) \| Retries: (\d+) \| Pages: (\d+) \| Emails: (\d+) \| Phones: (\d+) \| Confidence: ([\d.]+)', line)
        if match:
            attempts.append({
                'url': match.group(1),
                'status': match.group(2),
                'mode': match.group(3),
                'retries': int(match.group(4)),
                'pages': int(match.group(5)),
                'emails': int(match.group(6)),
                'phones': int(match.group(7)),
                'confidence': float(match.group(8))
            })

# Analyze
success_count = sum(1 for a in attempts if a['status'] == 'success')
failed_count = sum(1 for a in attempts if a['status'] == 'failed')
avg_confidence = sum(a['confidence'] for a in attempts) / len(attempts)

print(f"Success: {success_count}")
print(f"Failed: {failed_count}")
print(f"Average Confidence: {avg_confidence:.2f}")
```

### Parse Failures Log

```python
import re

failures = []
with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \| Reason: (.*?) \| Mode: (.*?) \| Retries: (\d+) \| BotProtection: (.*?) \| SSLValid: (.*?)$', line)
        if match:
            failures.append({
                'url': match.group(1),
                'reason': match.group(2),
                'mode': match.group(3),
                'retries': int(match.group(4)),
                'bot_protection': match.group(5),
                'ssl_valid': match.group(6) == 'true'
            })

# Group by reason
reasons = {}
for f in failures:
    reason = f['reason'].split(':')[0]  # Get first part
    reasons[reason] = reasons.get(reason, 0) + 1

for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
    print(f"{reason}: {count}")
```

### Find Most Problematic Sites

```python
import re
from collections import Counter

failures = []
with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \|', line)
        if match:
            failures.append(match.group(1))

# Count failures per domain
domains = Counter(failures)
for domain, count in domains.most_common(10):
    print(f"{domain}: {count} failures")
```

## Monitoring

### Real-Time Monitoring

```bash
# Watch attempts as they happen
tail -f scraper_attempts.log

# Watch failures as they happen
tail -f scraper_failures.log

# Watch general log
tail -f scraper.log
```

### Generate Report

```bash
#!/bin/bash

echo "=== Scraping Report ==="
echo ""
echo "Total Attempts:"
wc -l scraper_attempts.log

echo ""
echo "Success Rate:"
success=$(grep "Status: success" scraper_attempts.log | wc -l)
total=$(wc -l < scraper_attempts.log)
echo "Success: $success / $total ($(( success * 100 / total ))%)"

echo ""
echo "Top Failure Reasons:"
grep "URL:" scraper_failures.log | cut -d'|' -f2 | sort | uniq -c | sort -rn | head -5

echo ""
echo "Bot Protection Detected:"
grep "BotProtection:" scraper_failures.log | grep -v "null" | wc -l

echo ""
echo "SSL Errors:"
grep "SSLValid: false" scraper_failures.log | wc -l
```

## Learning from Failures

### Identify Patterns

```python
import re
from collections import Counter

# Read failures
failures = []
with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'Reason: (.*?) \|', line)
        if match:
            reason = match.group(1)
            # Extract main reason
            main_reason = reason.split(':')[0]
            failures.append(main_reason)

# Find patterns
reasons = Counter(failures)
print("Failure Patterns:")
for reason, count in reasons.most_common():
    print(f"  {reason}: {count} ({count*100//len(failures)}%)")
```

### Identify Problematic Sites

```python
import re

# Read failures
failures = {}
with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \| Reason: (.*?) \|', line)
        if match:
            url = match.group(1)
            reason = match.group(2)
            if url not in failures:
                failures[url] = []
            failures[url].append(reason)

# Find sites that fail consistently
print("Consistently Failing Sites:")
for url, reasons in failures.items():
    if len(reasons) > 1:  # Failed multiple times
        print(f"  {url}: {len(reasons)} failures")
        print(f"    Reasons: {reasons[0]}")
```

## Improvement Strategies

### Based on Failure Analysis

1. **High Bot Protection Rate**
   - Use more proxies
   - Increase hard mode delay
   - Reduce thread count

2. **High Timeout Rate**
   - Increase timeout value
   - Use browser mode
   - Check network connectivity

3. **High SSL Error Rate**
   - These sites can't be scraped (skip them)
   - Or use browser mode (ignores SSL)

4. **High Rate Limiting (429)**
   - Use proxies
   - Reduce thread count
   - Increase delays

## Reporting

### Generate CSV Report

```python
import csv
import re

# Parse attempts
attempts = []
with open('scraper_attempts.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \| Status: (.*?) \| Mode: (.*?) \| Retries: (\d+) \| Pages: (\d+) \| Emails: (\d+) \| Phones: (\d+) \| Confidence: ([\d.]+)', line)
        if match:
            attempts.append({
                'url': match.group(1),
                'status': match.group(2),
                'mode': match.group(3),
                'retries': int(match.group(4)),
                'pages': int(match.group(5)),
                'emails': int(match.group(6)),
                'phones': int(match.group(7)),
                'confidence': float(match.group(8))
            })

# Write report
with open('scraping_report.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=attempts[0].keys())
    writer.writeheader()
    writer.writerows(attempts)
```

### Generate Summary Report

```python
import re
from datetime import datetime

# Parse logs
attempts = []
failures = []

with open('scraper_attempts.log') as f:
    for line in f:
        match = re.search(r'Status: (.*?) \|', line)
        if match:
            attempts.append(match.group(1))

with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'Reason: (.*?) \|', line)
        if match:
            failures.append(match.group(1))

# Generate report
print("=== Scraping Summary Report ===")
print(f"Generated: {datetime.now()}")
print(f"Total Attempts: {len(attempts)}")
print(f"Successful: {attempts.count('success')}")
print(f"Failed: {attempts.count('failed')}")
print(f"Success Rate: {attempts.count('success')*100//len(attempts)}%")
print(f"\nTop Failure Reasons:")
from collections import Counter
for reason, count in Counter(failures).most_common(5):
    print(f"  {reason}: {count}")
```

## Best Practices

1. **Monitor Regularly**: Check logs daily
2. **Analyze Patterns**: Look for recurring issues
3. **Adjust Settings**: Based on failure analysis
4. **Archive Logs**: Keep historical data
5. **Generate Reports**: Track improvements over time

## Related Documentation

- See [RETRY_RECOVERY.md](RETRY_RECOVERY.md) for failure reasons
- See [QUICK_START.md](QUICK_START.md) for basic usage
- See [README.md](README.md) for feature overview

## Summary

The logging system provides:
- ✅ Detailed attempt tracking
- ✅ Failure analysis
- ✅ Pattern identification
- ✅ Performance monitoring
- ✅ Learning opportunities
- ✅ Historical data

Perfect for understanding what works, what doesn't, and how to improve!
