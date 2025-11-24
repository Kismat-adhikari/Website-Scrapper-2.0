# Proxy Rotation Quick Reference

Quick reference for periodic proxy rotation strategy.

## What It Does

Rotates to the next proxy **every 14 requests**, regardless of success or failure.

## Why It Makes Sense

1. **Breaks Detection Patterns**: Websites detect bots by IP patterns
2. **Distributes Load**: Spreads requests across proxies
3. **Improves Reliability**: If one proxy fails, others work
4. **Works Consistently**: Rotates regardless of request status

## How It Works

```
Requests 1-13:   Proxy A
Requests 14-27:  Proxy B
Requests 28-41:  Proxy C
Requests 42-55:  Proxy A (wraps)
```

## Example

### With 3 Proxies

```bash
python scraper.py urls.txt --proxy-file proxies.txt
```

```
Request 1:  Proxy 0 (192.168.1.1:8080)
Request 2:  Proxy 0
...
Request 13: Proxy 0
Request 14: Proxy 1 (10.0.0.1:3128) ← Rotates here
Request 15: Proxy 1
...
Request 27: Proxy 1
Request 28: Proxy 2 (172.16.0.1:8080) ← Rotates here
...
Request 42: Proxy 0 (wraps around)
```

## Thread-Safe

Each thread has independent request counter:

```
Thread 1: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
Thread 2: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
Thread 3: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
```

## Configuration

### Default (Every 14 Requests)

```bash
python scraper.py urls.txt --proxy-file proxies.txt
```

### Customize Interval

Edit `scraper.py`:

```python
class ProxyManager:
    ROTATION_INTERVAL = 14  # Change this value
```

### Common Intervals

| Interval | Use Case |
|----------|----------|
| 7 | Very aggressive |
| 14 | Balanced (default) |
| 21 | Conservative |
| 50 | Very conservative |

## Monitoring

### Check Rotation in Logs

```bash
grep "Periodic proxy rotation" scraper.log
```

### Get Request Count

```python
from scraper import ProxyManager

proxy_manager = ProxyManager("proxies.txt")
count = proxy_manager.get_request_count()
print(f"Total requests: {count}")
```

## Advantages

✅ Looks natural to websites
✅ Prevents single proxy blocking
✅ Distributes load evenly
✅ Works regardless of status
✅ Thread-safe
✅ Minimal overhead

## Comparison

| Strategy | Pattern | Detection Risk |
|----------|---------|-----------------|
| No rotation | Same IP always | Very high |
| Random | Random IP | Medium |
| Every request | IP changes every time | High (too frequent) |
| Every 14 requests | IP changes periodically | Low (natural) |

## Why Every 14?

- **Not too frequent**: Doesn't look suspicious
- **Not too rare**: Prevents blocking
- **Balanced**: Good for most sites
- **Customizable**: Can adjust if needed

## Examples

### 100 URLs, 5 Proxies

```
Requests 1-13:   Proxy 1
Requests 14-27:  Proxy 2
Requests 28-41:  Proxy 3
Requests 42-55:  Proxy 4
Requests 56-69:  Proxy 5
Requests 70-83:  Proxy 1 (wraps)
Requests 84-97:  Proxy 2
Requests 98-100: Proxy 3
```

### Multi-Threaded (10 threads)

Each thread independently rotates:

```
Thread 1: 1-13 (P1), 14-27 (P2), 28-41 (P3), ...
Thread 2: 1-13 (P1), 14-27 (P2), 28-41 (P3), ...
Thread 3: 1-13 (P1), 14-27 (P2), 28-41 (P3), ...
...
```

## Best Practices

1. **Use enough proxies**: 5+ recommended
2. **Monitor rotation**: Check logs
3. **Adjust if needed**: Change `ROTATION_INTERVAL`
4. **Combine strategies**: Use with hard mode delay

## Troubleshooting

### Rotation Not Happening
- Check if proxies loaded: `grep "Loaded.*proxies" scraper.log`
- Verify proxy file exists

### Rotating Too Frequently
- Increase `ROTATION_INTERVAL` to 21 or 50

### Rotating Too Rarely
- Decrease `ROTATION_INTERVAL` to 7

## Related Files

- [PROXY_ROTATION.md](PROXY_ROTATION.md) - Detailed guide
- [MULTITHREADING.md](MULTITHREADING.md) - Threading details
- [QUICK_START.md](QUICK_START.md) - Proxy setup

## Summary

**Periodic proxy rotation every 14 requests:**
- ✅ Breaks detection patterns
- ✅ Distributes load
- ✅ Improves reliability
- ✅ Works regardless of status
- ✅ Thread-safe
- ✅ Makes sense for undetectable scraping

Perfect for reliable, natural-looking scraping!
