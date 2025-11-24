# Logging Quick Reference

Quick reference for the scraper's logging system.

## Log Files

### scraper.log
General execution log with all events

```bash
tail -f scraper.log
```

### scraper_attempts.log
Detailed tracking of every scraping attempt

```bash
tail -f scraper_attempts.log
```

### scraper_failures.log
Failed URLs with reasons for analysis

```bash
tail -f scraper_failures.log
```

## Attempt Log Format

```
URL: {url} | Status: {status} | Mode: {mode} | Retries: {retries} | 
Pages: {pages} | Emails: {emails} | Phones: {phones} | 
Confidence: {score} | LoadTime: {time}s | Reason: {reason}
```

## Failure Log Format

```
URL: {url} | Reason: {reason} | Mode: {mode} | Retries: {retries} | 
BotProtection: {protection} | SSLValid: {valid}
```

## Quick Analysis

### Count Results

```bash
# Successful
grep "Status: success" scraper_attempts.log | wc -l

# Failed
grep "Status: failed" scraper_attempts.log | wc -l

# Skipped
grep "Status: skipped" scraper_attempts.log | wc -l
```

### Find Failure Reasons

```bash
# Top reasons
grep "URL:" scraper_failures.log | cut -d'|' -f2 | sort | uniq -c | sort -rn

# Bot protection
grep "BotProtection:" scraper_failures.log | grep -v "null"

# Timeouts
grep "timeout" scraper_failures.log

# SSL errors
grep "SSLValid: false" scraper_failures.log
```

### Success Rate

```bash
success=$(grep "Status: success" scraper_attempts.log | wc -l)
total=$(wc -l < scraper_attempts.log)
echo "Success Rate: $(( success * 100 / total ))%"
```

## Python Analysis

### Parse Attempts

```python
import re

attempts = []
with open('scraper_attempts.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \| Status: (.*?) \| Mode: (.*?) \| Retries: (\d+)', line)
        if match:
            attempts.append({
                'url': match.group(1),
                'status': match.group(2),
                'mode': match.group(3),
                'retries': int(match.group(4))
            })

# Analyze
success = sum(1 for a in attempts if a['status'] == 'success')
print(f"Success: {success}/{len(attempts)}")
```

### Parse Failures

```python
import re

failures = []
with open('scraper_failures.log') as f:
    for line in f:
        match = re.search(r'URL: (.*?) \| Reason: (.*?) \|', line)
        if match:
            failures.append({
                'url': match.group(1),
                'reason': match.group(2)
            })

# Group by reason
from collections import Counter
reasons = Counter(f['reason'].split(':')[0] for f in failures)
for reason, count in reasons.most_common():
    print(f"{reason}: {count}")
```

## Monitoring Commands

### Real-Time Monitoring

```bash
# Watch attempts
tail -f scraper_attempts.log

# Watch failures
tail -f scraper_failures.log

# Watch all logs
tail -f scraper.log scraper_attempts.log scraper_failures.log
```

### Generate Report

```bash
#!/bin/bash

echo "=== Scraping Report ==="
echo "Total: $(wc -l < scraper_attempts.log)"
echo "Success: $(grep "Status: success" scraper_attempts.log | wc -l)"
echo "Failed: $(grep "Status: failed" scraper_attempts.log | wc -l)"
echo ""
echo "Top Failures:"
grep "URL:" scraper_failures.log | cut -d'|' -f2 | sort | uniq -c | sort -rn | head -5
```

## What to Look For

### High Failure Rate
- Check bot protection types
- Increase proxies
- Reduce thread count

### High Timeout Rate
- Increase timeout value
- Use browser mode
- Check network

### High Bot Protection
- Use more proxies
- Increase hard mode delay
- Reduce concurrency

### Consistent Site Failures
- May need special handling
- Consider skipping
- Or use different strategy

## Log Rotation

### Archive Old Logs

```bash
# Backup current logs
cp scraper.log scraper.log.$(date +%Y%m%d)
cp scraper_attempts.log scraper_attempts.log.$(date +%Y%m%d)
cp scraper_failures.log scraper_failures.log.$(date +%Y%m%d)

# Clear for new run
> scraper.log
> scraper_attempts.log
> scraper_failures.log
```

## Analysis Examples

### Find Most Problematic Sites

```bash
grep "URL:" scraper_failures.log | cut -d'|' -f1 | sort | uniq -c | sort -rn | head -10
```

### Find Sites by Protection Type

```bash
# Cloudflare
grep "BotProtection: cloudflare" scraper_failures.log | cut -d'|' -f1

# CAPTCHA
grep "BotProtection: captcha" scraper_failures.log | cut -d'|' -f1
```

### Average Confidence Score

```bash
grep "Status: success" scraper_attempts.log | \
  grep -oP 'Confidence: \K[\d.]+' | \
  awk '{sum+=$1; count++} END {print sum/count}'
```

### Retry Statistics

```bash
grep "Retries:" scraper_attempts.log | \
  grep -oP 'Retries: \K\d+' | \
  awk '{sum+=$1; count++} END {print "Avg Retries: " sum/count}'
```

## Best Practices

1. **Monitor daily**: Check logs regularly
2. **Archive logs**: Keep historical data
3. **Analyze patterns**: Look for trends
4. **Adjust settings**: Based on analysis
5. **Generate reports**: Track improvements

## Related Files

- [LOGGING_ANALYSIS.md](LOGGING_ANALYSIS.md) - Detailed guide
- [RETRY_RECOVERY.md](RETRY_RECOVERY.md) - Failure reasons
- [QUICK_START.md](QUICK_START.md) - Basic usage

## Summary

Three log files track everything:
- **scraper.log**: General events
- **scraper_attempts.log**: Detailed attempts
- **scraper_failures.log**: Failed URLs

Perfect for monitoring, analysis, and improvement!
