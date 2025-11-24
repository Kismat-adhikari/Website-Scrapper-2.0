# Retry and Recovery Summary

Quick reference for retry and recovery mechanisms.

## Failure Reasons

| Reason | Cause | Recovery |
|--------|-------|----------|
| timeout | Request exceeded timeout | Increase timeout, use browser |
| blocked | HTTP 403/429 | Use proxies, reduce threads |
| ssl_error | SSL certificate error | Skip or use browser mode |
| bot_detection | Cloudflare/CAPTCHA/bot protection | Use browser or hard mode |
| network_error | Connection refused/unreachable | Retry with proxy |
| invalid_url | Malformed URL | Skip or validate |
| no_contact | No contact info found | Check different pages |
| unknown | Unclassified error | Log and retry |

## Retry Attempts

### Fast HTML Mode
- Max attempts: 3
- Retry on: Timeout, connection error, 429/403
- Delay: 0.5s between attempts
- Headers: Rotated
- Proxies: Rotated

### JS Rendering Mode
- Max attempts: 2
- Retry on: Timeout, connection error
- Delay: Exponential backoff
- Browser: Fresh instance

### Hard Mode
- Max attempts: 1 (with internal retries)
- Retry on: 429/403 (internal)
- Delay: Exponential backoff
- Headers: Rotated
- Proxies: Rotated

## Mode Escalation

```
Fast HTML (3 attempts)
    ↓ (if all fail)
JS Rendering (2 attempts)
    ↓ (if all fail)
Hard Mode (1 attempt)
    ↓ (if all fail)
Failed
```

## Exponential Backoff

```
delay = min(1.5 ^ attempt, 30.0)
```

Examples:
- Attempt 1: 1.0s
- Attempt 2: 1.5s
- Attempt 3: 2.25s
- Attempt 4: 3.375s
- Attempt 5: 5.06s

## Problematic Site Tracking

Sites marked as problematic after 2+ failures:
- Logged with warning level
- Tracked for future reference
- Can trigger reduced concurrency

## Log Examples

### Successful Retry
```
DEBUG - Fast HTML attempt 1 failed for https://example.com: timeout
DEBUG - Retrying https://example.com in 1.0s (attempt 2/3)
INFO - Fast HTML fetch succeeded for https://example.com on attempt 2
```

### Mode Escalation
```
DEBUG - Fast HTML attempt 1 failed: timeout
DEBUG - Fast HTML attempt 2 failed: 429
DEBUG - Fast HTML attempt 3 failed: timeout
INFO - Fast HTML failed for https://example.com, trying JS rendering
INFO - JS rendering succeeded for https://example.com
```

### Problematic Site
```
WARNING - Marked https://example.com as problematic (failures: 2)
```

## Configuration

### Command Line

```bash
# Increase timeout for slow sites
python scraper.py urls.txt --timeout 20

# Use proxies for blocked sites
python scraper.py urls.txt --proxy-file proxies.txt

# Reduce concurrency for problematic sites
python scraper.py urls.txt --threads 3

# Increase hard mode delay
python scraper.py urls.txt --hard-mode-delay 2.0
```

### Python API

```python
from scraper import WebScraper, RetryStrategy

scraper = WebScraper(proxy_manager)

# Access retry strategy
retry_strategy = scraper.retry_strategy

# Check failures
failures = retry_strategy.get_failure_count(url)
reasons = retry_strategy.get_failure_reasons(url)
is_problematic = retry_strategy.is_problematic(url)
```

## Typical Retry Rates

- Successful on first attempt: 70-80%
- Successful on second attempt: 10-15%
- Successful on third attempt: 5-10%
- Failed after all attempts: 5-10%

## Best Practices

1. **Use proxies**: Essential for protected sites
2. **Adjust timeout**: Increase for slow sites
3. **Reduce concurrency**: For problematic sites
4. **Monitor logs**: Check for patterns
5. **Analyze failures**: Understand what's failing

## Troubleshooting

### High Timeout Rate
- Increase `--timeout` to 20-30
- Use `--threads 3`
- Check network

### High Rate Limiting (429)
- Use `--proxy-file proxies.txt`
- Reduce `--threads` to 3-5
- Increase `--hard-mode-delay` to 2.0+

### High Bot Detection
- Use `--proxy-file proxies.txt`
- Use `--hard-mode-delay 1.5+`
- Reduce `--threads` to 1-3

### High Network Errors
- Check network connectivity
- Use `--proxy-file proxies.txt`
- Retry with different proxies

## Performance Impact

### Retry Overhead
- Fast HTML retry: ~1-2 seconds
- JS Rendering retry: ~3-8 seconds
- Hard Mode retry: ~5-30 seconds

### Optimization
- Use appropriate timeout
- Use proxies for protected sites
- Reduce threads for problematic sites
- Monitor and adjust settings

## Related Files

- [RETRY_RECOVERY.md](RETRY_RECOVERY.md) - Detailed retry guide
- [README.md](README.md) - Feature overview
- [QUICK_START.md](QUICK_START.md) - Quick start
- [FETCH_MODES.md](FETCH_MODES.md) - Fetch mode details

## Key Takeaways

1. **Automatic retries**: Different headers, proxies, modes
2. **Failure detection**: Specific reasons logged
3. **Mode escalation**: HTML → JS → Hard Mode
4. **Exponential backoff**: Avoid overwhelming servers
5. **Problematic tracking**: Identify difficult sites
6. **Comprehensive logging**: Detailed failure analysis

The retry and recovery system ensures maximum success rate and reliability.
