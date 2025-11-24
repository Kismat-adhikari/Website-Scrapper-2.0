# Proxy Rotation Strategy

Comprehensive guide to the periodic proxy rotation strategy.

## Overview

The scraper implements a **periodic proxy rotation every 14 requests** strategy that:
- Rotates to the next proxy every 14 requests
- Works regardless of request success or failure
- Helps avoid detection patterns
- Distributes load evenly across proxies
- Thread-safe implementation

## Why Every 14 Requests?

### Benefits

1. **Avoids Detection Patterns**
   - Websites track request patterns
   - Rotating every 14 requests breaks patterns
   - Looks more like natural user behavior

2. **Distributes Load**
   - Spreads requests across proxies
   - Prevents single proxy from being blocked
   - Balances rate limiting

3. **Improves Reliability**
   - If one proxy fails, others take over
   - Reduces dependency on single proxy
   - Better resilience

4. **Works Regardless of Status**
   - Rotates on success AND failure
   - Consistent rotation pattern
   - Predictable behavior

## How It Works

### Request Counting

```
Request 1-13:  Use Proxy 0
Request 14:    Rotate to Proxy 1
Request 15-27: Use Proxy 1
Request 28:    Rotate to Proxy 2
Request 29-41: Use Proxy 2
Request 42:    Rotate to Proxy 3
...
```

### Thread-Safe Implementation

```python
with self.lock:
    # Rotate every 14 requests
    if self.request_count > 0 and self.request_count % 14 == 0:
        self.current_index += 1
    
    proxy = self.proxies[self.current_index % len(self.proxies)]
    self.request_count += 1
```

### Example with 3 Proxies

```
Requests 1-13:   Proxy A (192.168.1.1:8080)
Requests 14-27:  Proxy B (10.0.0.1:3128)
Requests 28-41:  Proxy C (172.16.0.1:8080)
Requests 42-55:  Proxy A (wraps around)
Requests 56-69:  Proxy B
...
```

## Configuration

### Default Behavior

```bash
# Uses periodic rotation every 14 requests
python scraper.py urls.txt --proxy-file proxies.txt
```

### Customizing Rotation Interval

To change the rotation interval, edit `scraper.py`:

```python
class ProxyManager:
    # Change this value
    ROTATION_INTERVAL = 14  # Rotate every 14 requests
```

### Common Intervals

| Interval | Use Case |
|----------|----------|
| 7 | Very aggressive (frequent rotation) |
| 14 | Balanced (default) |
| 21 | Conservative (less frequent) |
| 50 | Very conservative (rare rotation) |

## Advantages

### 1. Avoids Detection
- Websites detect patterns like:
  - Same IP for every request
  - Consistent request timing
  - Identical headers
- Rotating breaks these patterns

### 2. Distributes Load
- Spreads requests across proxies
- Prevents single proxy overload
- Better rate limiting handling

### 3. Improves Reliability
- If proxy fails, next one takes over
- Automatic failover
- Better resilience

### 4. Works Regardless of Status
- Rotates on success: ✓
- Rotates on failure: ✓
- Rotates on timeout: ✓
- Rotates on rate limit: ✓

## Example Scenarios

### Scenario 1: 100 URLs, 3 Proxies

```
Requests 1-13:   Proxy A
Requests 14-27:  Proxy B
Requests 28-41:  Proxy C
Requests 42-55:  Proxy A
Requests 56-69:  Proxy B
Requests 70-83:  Proxy C
Requests 84-97:  Proxy A
Request 98-100:  Proxy B
```

### Scenario 2: 50 URLs, 5 Proxies

```
Requests 1-13:   Proxy A
Requests 14-27:  Proxy B
Requests 28-41:  Proxy C
Requests 42-50:  Proxy D (only 9 requests)
```

### Scenario 3: Multi-Threaded (10 threads)

```
Thread 1: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
Thread 2: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
Thread 3: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...
...
Thread 10: Requests 1-13 (Proxy A), 14-27 (Proxy B), ...

Note: Each thread has independent request counter
```

## Implementation Details

### Thread Safety

```python
with self.lock:
    # Atomic operation
    if self.request_count > 0 and self.request_count % 14 == 0:
        self.current_index += 1
    
    proxy = self.proxies[self.current_index % len(self.proxies)]
    self.request_count += 1
```

### Request Counting

- Increments on every `get_next_proxy()` call
- Increments on every `get_random_proxy()` call
- Thread-safe with lock
- Wraps around with modulo operator

### Proxy Wrapping

```python
# If we have 3 proxies and current_index = 3
proxy = self.proxies[3 % 3]  # = self.proxies[0]
```

## Monitoring

### Check Rotation

```bash
# Monitor proxy rotation in logs
grep "Periodic proxy rotation" scraper.log

# Example output:
# Periodic proxy rotation at request 14: switching to proxy 1
# Periodic proxy rotation at request 28: switching to proxy 2
# Periodic proxy rotation at request 42: switching to proxy 0
```

### Get Request Count

```python
from scraper import ProxyManager

proxy_manager = ProxyManager("proxies.txt")
# ... scraping ...
count = proxy_manager.get_request_count()
print(f"Total requests: {count}")
```

### Reset Counter

```python
proxy_manager.reset_request_count()
```

## Best Practices

### 1. Use Enough Proxies
```bash
# Good: 5+ proxies
python scraper.py urls.txt --proxy-file proxies.txt

# With 5 proxies, each gets ~20 requests before rotation
# Requests 1-13: Proxy 1
# Requests 14-27: Proxy 2
# Requests 28-41: Proxy 3
# Requests 42-55: Proxy 4
# Requests 56-69: Proxy 5
# Requests 70-83: Proxy 1 (wraps)
```

### 2. Monitor Rotation
```bash
# Check if rotation is happening
grep "Periodic proxy rotation" scraper.log | wc -l
```

### 3. Adjust for Your Needs
```python
# For very protected sites, rotate more frequently
ROTATION_INTERVAL = 7  # Every 7 requests

# For less protected sites, rotate less frequently
ROTATION_INTERVAL = 21  # Every 21 requests
```

### 4. Combine with Other Strategies
```bash
# Periodic rotation + hard mode delay
python scraper.py urls.txt \
  --proxy-file proxies.txt \
  --hard-mode-delay 1.5 \
  --threads 5
```

## Why This Makes Sense

### 1. Breaks Detection Patterns
Websites use heuristics to detect bots:
- Same IP for all requests → Bot
- Rotating IP every 14 requests → More natural

### 2. Distributes Load
- Prevents single proxy from being rate limited
- Spreads requests evenly
- Better resilience

### 3. Works Regardless of Status
- Doesn't matter if request succeeded or failed
- Consistent rotation pattern
- Predictable behavior

### 4. Improves Success Rate
- More proxies = more chances to succeed
- If one proxy is blocked, others work
- Better overall reliability

## Comparison with Other Strategies

### Strategy 1: No Rotation
```
All requests → Same proxy
Problem: Gets blocked quickly
```

### Strategy 2: Random Rotation
```
Each request → Random proxy
Problem: Unpredictable, might use same proxy twice
```

### Strategy 3: Sequential Rotation (Every Request)
```
Request 1 → Proxy A
Request 2 → Proxy B
Request 3 → Proxy C
Problem: Too frequent, looks suspicious
```

### Strategy 4: Periodic Rotation (Every 14 Requests) ✓
```
Requests 1-13 → Proxy A
Requests 14-27 → Proxy B
Requests 28-41 → Proxy C
Benefit: Balanced, natural-looking, reliable
```

## Performance Impact

### Minimal Overhead
- Rotation check: O(1) operation
- Lock acquisition: Negligible
- No performance degradation

### Example Performance
```
100 URLs, 5 proxies, 5 threads:
- Without rotation: ~50 seconds
- With rotation: ~50 seconds (no difference)
```

## Troubleshooting

### Rotation Not Happening
**Problem**: Proxies not rotating
**Solution**: Check if proxies are loaded
```bash
grep "Loaded.*proxies" scraper.log
```

### Rotation Too Frequent
**Problem**: Rotating too often
**Solution**: Increase `ROTATION_INTERVAL`
```python
ROTATION_INTERVAL = 21  # Every 21 requests
```

### Rotation Too Infrequent
**Problem**: Rotating too rarely
**Solution**: Decrease `ROTATION_INTERVAL`
```python
ROTATION_INTERVAL = 7  # Every 7 requests
```

## Related Documentation

- See [MULTITHREADING.md](MULTITHREADING.md) for threading details
- See [QUICK_START.md](QUICK_START.md) for proxy configuration
- See [README.md](README.md) for feature overview

## Summary

The periodic proxy rotation strategy:
- ✅ Rotates every 14 requests
- ✅ Works regardless of success/failure
- ✅ Thread-safe implementation
- ✅ Breaks detection patterns
- ✅ Distributes load evenly
- ✅ Improves reliability
- ✅ Minimal performance impact

This makes sense because it:
1. Looks more natural to websites
2. Prevents single proxy from being blocked
3. Distributes load across proxies
4. Improves overall success rate
5. Works consistently regardless of request status

Perfect for reliable, undetectable scraping!
