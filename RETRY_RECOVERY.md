# Retry and Recovery Guide

Comprehensive guide to the scraper's retry and recovery mechanisms.

## Overview

The scraper implements intelligent retry and recovery strategies to maximize success rates:
- Automatic retries with different headers and proxies
- Mode escalation (HTML → JS Rendering → Hard Mode)
- Failure reason detection and logging
- Problematic site tracking
- Exponential backoff delays

## Failure Reasons

The scraper detects and logs specific failure reasons:

### Timeout
- Request exceeded timeout threshold
- Typical: Slow sites, network issues
- Recovery: Retry with longer timeout or browser mode

### Blocked
- HTTP 403 (Forbidden) or 429 (Rate Limited)
- Typical: Access denied, rate limiting
- Recovery: Use proxies, reduce concurrency, hard mode

### SSL Error
- SSL certificate validation failed
- Typical: Self-signed certificates, expired certs
- Recovery: Skip or use browser mode (ignores SSL)

### Bot Detection
- Cloudflare, CAPTCHA, or bot protection detected
- Typical: Protected sites
- Recovery: Use browser mode or hard mode

### Network Error
- Connection refused, network unreachable
- Typical: Network issues, firewall blocks
- Recovery: Retry with different proxy

### Invalid URL
- Malformed URL or invalid format
- Typical: Bad URL input
- Recovery: Skip or validate URL

### No Contact
- Page loaded but no contact info found
- Typical: Sites without contact info
- Recovery: Check different pages

### Unknown
- Unclassified error
- Typical: Unexpected exceptions
- Recovery: Log and retry

## Retry Strategy

### Retry Attempts by Mode

**Fast HTML Mode**
- Maximum attempts: 3
- Retry on: Timeout, connection error, 429/403
- Delay: 0.5s between attempts
- Headers: Rotated on each attempt
- Proxies: Rotated on each attempt

**JS Rendering Mode**
- Maximum attempts: 2
- Retry on: Timeout, connection error
- Delay: Exponential backoff (1s, 2s)
- Browser: Fresh instance per attempt

**Hard Mode**
- Maximum attempts: 1 (built-in retries)
- Retry on: 429/403 (internal)
- Delay: Exponential backoff (0.5s-2s)
- Headers: Rotated on each attempt
- Proxies: Rotated on each attempt

### Exponential Backoff

Delay calculation:
```
delay = min(backoff_factor ^ attempt, 30.0)
```

Default backoff factor: 1.5

Examples:
- Attempt 1: 1.5^0 = 1.0s
- Attempt 2: 1.5^1 = 1.5s
- Attempt 3: 1.5^2 = 2.25s
- Attempt 4: 1.5^3 = 3.375s
- Attempt 5: 1.5^4 = 5.06s

Maximum delay: 30 seconds

## Mode Escalation

The scraper automatically escalates through fetch modes:

```
Fast HTML (3 attempts)
    ↓ (if all fail)
JS Rendering (2 attempts)
    ↓ (if all fail)
Hard Mode (1 attempt with internal retries)
    ↓ (if all fail)
Mark as failed
```

### When to Escalate

**Fast HTML → JS Rendering**
- Timeout errors
- Connection errors
- Bot protection detected
- 429/403 responses

**JS Rendering → Hard Mode**
- Timeout errors
- Connection errors
- Bot protection detected
- 429/403 responses

## Failure Logging

### Log Format

```
timestamp - level - message
```

### Example Logs

```
2024-01-15 10:30:45,123 - INFO - Starting scrape for https://example.com
2024-01-15 10:30:46,234 - DEBUG - Fast HTML attempt 1 failed for https://example.com: timeout
2024-01-15 10:30:47,345 - DEBUG - Retrying https://example.com in 1.0s (attempt 2/3)
2024-01-15 10:30:48,456 - DEBUG - Fast HTML attempt 2 failed for https://example.com: 429
2024-01-15 10:30:49,567 - DEBUG - Retrying https://example.com in 1.5s (attempt 3/3)
2024-01-15 10:30:51,678 - INFO - Fast HTML failed for https://example.com, trying JS rendering
2024-01-15 10:30:52,789 - INFO - JS rendering succeeded for https://example.com
2024-01-15 10:30:53,890 - INFO - Completed: https://example.com - Status: success
```

### Log Levels

- **INFO**: Major operations (start, mode changes, completion)
- **DEBUG**: Detailed operations (attempts, retries, delays)
- **WARNING**: Issues (marked problematic, SSL invalid)
- **ERROR**: Failures (exceptions, critical errors)

## Problematic Site Tracking

### What Gets Marked as Problematic

Sites with 2+ failures across different modes:
- Multiple timeout errors
- Multiple connection errors
- Multiple bot detection
- Mixed failure types

### How It's Used

Problematic sites:
- Logged with warning level
- Tracked for future reference
- Can trigger reduced concurrency
- Helps identify patterns

### Example

```
2024-01-15 10:30:45,123 - WARNING - Marked https://example.com as problematic (failures: 2)
```

## Retry Configuration

### Command Line Options

```bash
# Default retry behavior
python scraper.py urls.txt

# Increase timeout for slow sites
python scraper.py urls.txt --timeout 20

# Use proxies for blocked sites
python scraper.py urls.txt --proxy-file proxies.txt

# Reduce concurrency for problematic sites
python scraper.py urls.txt --threads 3
```

### Python API

```python
from scraper import WebScraper, ProxyManager, RetryStrategy

# Create scraper with custom retry settings
proxy_manager = ProxyManager("proxies.txt")
scraper = WebScraper(
    proxy_manager=proxy_manager,
    timeout=15,
    hard_mode_delay=1.5
)

# Access retry strategy
retry_strategy = scraper.retry_strategy
print(f"Failures for URL: {retry_strategy.get_failure_count(url)}")
print(f"Reasons: {retry_strategy.get_failure_reasons(url)}")
print(f"Is problematic: {retry_strategy.is_problematic(url)}")
```

## Failure Analysis

### Analyzing Failures

```python
import csv

with open('results.csv') as f:
    reader = csv.DictReader(f)
    
    failures = [r for r in reader if r['status'] == 'failed']
    
    # Group by reason
    reasons = {}
    for failure in failures:
        reason = failure['reason']
        reasons[reason] = reasons.get(reason, 0) + 1
    
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"{reason}: {count}")
```

### Common Failure Patterns

**Timeout Issues**
- Slow sites (>6 seconds)
- Solution: Increase timeout, use browser mode

**Rate Limiting (429)**
- Too many requests
- Solution: Use proxies, reduce threads, increase delay

**Access Denied (403)**
- Blocked by firewall or WAF
- Solution: Use proxies, hard mode, different headers

**Bot Detection**
- Cloudflare, CAPTCHA, etc.
- Solution: Use browser mode, hard mode

**Network Errors**
- Connection refused, unreachable
- Solution: Check network, use proxies, retry

## Best Practices

### For Reliable Scraping

1. **Use proxies**: Essential for protected sites
   ```bash
   python scraper.py urls.txt --proxy-file proxies.txt
   ```

2. **Adjust timeout**: Increase for slow sites
   ```bash
   python scraper.py urls.txt --timeout 20
   ```

3. **Reduce concurrency**: For problematic sites
   ```bash
   python scraper.py urls.txt --threads 3
   ```

4. **Monitor logs**: Check for patterns
   ```bash
   tail -f scraper.log
   ```

5. **Analyze failures**: Understand what's failing
   ```bash
   grep "failed" scraper.log | head -20
   ```

### For Problematic Sites

1. **Identify problematic sites**
   ```bash
   grep "problematic" scraper.log
   ```

2. **Retry with different settings**
   ```bash
   python scraper.py problematic_urls.txt --proxy-file proxies.txt --threads 1
   ```

3. **Use hard mode**
   ```bash
   python scraper.py problematic_urls.txt --hard-mode-delay 2.0
   ```

4. **Increase timeout**
   ```bash
   python scraper.py problematic_urls.txt --timeout 30
   ```

## Performance Impact

### Retry Overhead

- **Fast HTML**: ~1-2 seconds per retry
- **JS Rendering**: ~3-8 seconds per retry
- **Hard Mode**: ~5-30 seconds per retry

### Typical Retry Rates

- **Successful on first attempt**: 70-80%
- **Successful on second attempt**: 10-15%
- **Successful on third attempt**: 5-10%
- **Failed after all attempts**: 5-10%

### Optimization

To minimize retry overhead:
1. Use appropriate timeout
2. Use proxies for protected sites
3. Reduce threads for problematic sites
4. Monitor and adjust settings

## Troubleshooting

### High Timeout Rate

**Symptoms**: Many "timeout" failures

**Solutions**:
- Increase `--timeout` to 20-30 seconds
- Use `--threads 3` to reduce load
- Check network connectivity

### High Rate Limiting (429)

**Symptoms**: Many "429" failures

**Solutions**:
- Use `--proxy-file proxies.txt`
- Reduce `--threads` to 3-5
- Increase `--hard-mode-delay` to 2.0+

### High Bot Detection

**Symptoms**: Many "bot_detection" failures

**Solutions**:
- Use `--proxy-file proxies.txt`
- Use `--hard-mode-delay 1.5+`
- Reduce `--threads` to 1-3

### High SSL Errors

**Symptoms**: Many "ssl_error" failures

**Solutions**:
- These are typically skipped (can't bypass SSL)
- Check if sites have valid certificates
- Consider using browser mode

### High Network Errors

**Symptoms**: Many "network_error" failures

**Solutions**:
- Check network connectivity
- Use `--proxy-file proxies.txt`
- Retry with different proxies

## Advanced Usage

### Custom Retry Strategy

To implement custom retry logic:

```python
from scraper import RetryStrategy, FailureReason

# Create custom retry strategy
retry_strategy = RetryStrategy(max_retries=10, backoff_factor=2.0)

# Record failures
retry_strategy.record_failure(url, "fast_html", FailureReason.TIMEOUT)

# Check status
if retry_strategy.should_retry(url):
    delay = retry_strategy.get_retry_delay(attempt)
    # Retry with delay
```

### Failure Reason Detection

To detect failure reasons:

```python
from scraper import WebScraper

scraper = WebScraper(proxy_manager)

# Detect reason from exception
reason = scraper._detect_failure_reason(exception, response_code)
print(f"Failure reason: {reason.value}")
```

## Related Documentation

- See [README.md](README.md) for feature overview
- See [FETCH_MODES.md](FETCH_MODES.md) for fetch mode details
- See [QUICK_START.md](QUICK_START.md) for usage examples
- Check `scraper.log` for detailed logs

## Summary

The retry and recovery system ensures:
- Maximum success rate through intelligent retries
- Specific failure reason detection
- Automatic mode escalation
- Exponential backoff to avoid overwhelming servers
- Problematic site tracking for optimization
- Comprehensive logging for analysis

This makes the scraper robust and reliable for production use.
