# Interactive Mode Fix - Timeout & Precheck Disabled

## Problem

When running interactive mode and pasting a URL, the scraper would say "Scraping..." and then hang indefinitely without returning results.

## Root Cause

The precheck system was detecting bot protection (Cloudflare, CAPTCHA, etc.) and trying to use browser rendering (Playwright), which could hang if:
- The browser process wasn't responding
- The page was taking too long to load
- Playwright wasn't properly initialized

## Solution

Two fixes were implemented:

### 1. Disabled Precheck for Interactive Mode

The precheck system is now **disabled by default** in interactive mode to prevent hangs:

```python
# Disable precheck for interactive mode to avoid hangs
is_interactive = args.interactive or not args.urls
enable_precheck = not args.no_precheck and not is_interactive
```

This means:
- ✅ Interactive mode: Fast HTML fetch only (no precheck)
- ✅ Batch mode: Precheck enabled (can use browser rendering if needed)

### 2. Added Timeout Wrapper

Interactive mode now has a **60-second timeout** per URL:

```python
scrape_thread = threading.Thread(target=scrape_with_timeout, daemon=True)
scrape_thread.start()
scrape_thread.join(timeout=60)  # 60 second timeout

if scrape_thread.is_alive():
    print(f"✗ Timeout: Scraping took too long (>60s)")
```

If a URL takes longer than 60 seconds, it will timeout and let you try another URL.

## How to Use

### Interactive Mode (Default)

```bash
python scraper.py
```

Then paste URLs:
```
Enter URL (or command): https://example.com
Scraping https://example.com...
✓ Status: success
  Emails: 2
  Phones: 1
  Confidence: 0.75
```

### With Precheck Enabled (Optional)

If you want precheck in interactive mode:

```bash
python scraper.py --interactive
```

Then use `--no-precheck` flag to disable it:

```bash
python scraper.py --no-precheck
```

### Batch Mode (Precheck Enabled)

```bash
python scraper.py urls.txt
```

Batch mode still uses precheck for better accuracy.

## What Changed

| Feature | Before | After |
|---------|--------|-------|
| Interactive Mode | Hangs on bot protection | Fast, 60s timeout |
| Precheck | Always enabled | Disabled in interactive mode |
| Browser Rendering | Could hang indefinitely | Timeout after 60s |
| User Experience | Frustrating hangs | Responsive feedback |

## Examples

### Fast URL (Returns Immediately)

```bash
Enter URL (or command): https://github.com
Scraping https://github.com...
✓ Status: success
  Emails: 1
  Phones: 0
  Confidence: 0.65
```

### Slow URL (Times Out After 60s)

```bash
Enter URL (or command): https://slow-site.com
Scraping https://slow-site.com...
✗ Timeout: Scraping took too long (>60s)
  Try a different URL or check your connection
```

### Invalid URL (Returns Error)

```bash
Enter URL (or command): https://invalid-domain-12345.com
Scraping https://invalid-domain-12345.com...
✓ Status: failed
  Emails: 0
  Phones: 0
  Confidence: 0.0
```

## Benefits

1. **No More Hangs**: 60-second timeout prevents indefinite waiting
2. **Faster Results**: No precheck overhead in interactive mode
3. **Better UX**: Immediate feedback on success/failure
4. **Batch Mode Unchanged**: Batch mode still uses precheck for accuracy
5. **Responsive**: Can try multiple URLs quickly

## Troubleshooting

### Still Hanging?

If it's still hanging, try:

1. **Check your internet connection**
   ```bash
   ping example.com
   ```

2. **Try a different URL**
   ```bash
   Enter URL (or command): https://github.com
   ```

3. **Use batch mode instead**
   ```bash
   python scraper.py urls.txt
   ```

### Want Precheck in Interactive Mode?

If you need precheck (for bot protection detection), use batch mode:

```bash
# Create a file with one URL
echo "https://example.com" > single_url.txt

# Run batch mode (precheck enabled)
python scraper.py single_url.txt
```

### Timeout Too Short?

The 60-second timeout is reasonable for most sites. If you need longer:

1. Use batch mode (no timeout)
2. Or modify the timeout in `interactive_mode()` function

## Summary

✅ Interactive mode now works without hanging
✅ 60-second timeout prevents indefinite waits
✅ Precheck disabled for interactive mode (faster)
✅ Batch mode still uses precheck (more accurate)
✅ Better user experience overall

Try it now!
