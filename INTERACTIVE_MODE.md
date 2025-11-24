# Interactive Mode Guide

Use the scraper in interactive mode to paste URLs one at a time and see results immediately.

## How to Use

### Start Interactive Mode

```bash
# Option 1: Just run with --interactive flag
python scraper.py --interactive

# Option 2: Run with no arguments (auto-enters interactive mode)
python scraper.py
```

## Interactive Commands

Once running, you can:

### Paste a URL
```
Enter URL (or command): https://example.com
```

The scraper will:
1. Scrape the URL
2. Show quick results
3. Ask for next URL

### View Results
```
Enter URL (or command): results
```

Shows all URLs scraped so far with status and email count.

### Clear Results
```
Enter URL (or command): clear
```

Clears all results (but doesn't delete the CSV file).

### Exit
```
Enter URL (or command): quit
```

or

```
Enter URL (or command): exit
```

Saves results to CSV and exits.

## Example Session

```
============================================================
INTERACTIVE MODE - Paste URLs one at a time
============================================================
Commands:
  - Paste a URL and press Enter to scrape it
  - Type 'quit' or 'exit' to stop
  - Type 'results' to view current results
  - Type 'clear' to clear results
============================================================

Enter URL (or command): https://example.com
Scraping https://example.com...
✓ Status: success
  Emails: 5
  Phones: 2
  Confidence: 0.82

Enter URL (or command): https://github.com
Scraping https://github.com...
✓ Status: success
  Emails: 1
  Phones: 0
  Confidence: 0.65

Enter URL (or command): results
Scraped 2 URLs so far:
  https://example.com: success (5 emails)
  https://github.com: success (1 emails)

Enter URL (or command): quit

✓ Results saved to results.csv
✓ Total URLs scraped: 2
```

## Configuration

You can still use command-line options with interactive mode:

```bash
# Interactive mode with custom settings
python scraper.py --interactive --threads 10 --timeout 20

# Interactive mode with proxies
python scraper.py --interactive --proxy-file proxies.txt

# Interactive mode with custom output file
python scraper.py --interactive --output my_results.csv
```

## Output

When you exit, results are saved to:
- **results.csv** (or custom file with `--output`)
- **scraper.log** - General log
- **scraper_attempts.log** - Detailed attempts
- **scraper_failures.log** - Failed URLs

## Tips

1. **Paste multiple URLs**: Just keep pasting, one per line
2. **Check progress**: Type `results` to see what you've scraped
3. **Stop anytime**: Press Ctrl+C or type `quit`
4. **Batch mode**: If you have many URLs, use batch mode instead:
   ```bash
   python scraper.py urls.txt
   ```

## Keyboard Shortcuts

- **Ctrl+C**: Stop immediately (results still saved)
- **Enter**: Submit URL or command

## Troubleshooting

### Scraper seems stuck
- Press Ctrl+C to stop
- Check `scraper.log` for errors

### Results not saving
- Make sure you type `quit` or `exit` (not Ctrl+C)
- Check file permissions in current directory

### Want to use batch mode instead
```bash
python scraper.py urls.txt
```

## Comparison: Interactive vs Batch

### Interactive Mode
```bash
python scraper.py --interactive
# Paste URLs one at a time
# See results immediately
# Good for testing/exploring
```

### Batch Mode
```bash
python scraper.py urls.txt
# Process all URLs at once
# Multi-threaded for speed
# Good for large lists
```

## Summary

Interactive mode lets you:
- ✅ Paste URLs one at a time
- ✅ See results immediately
- ✅ Test before batch processing
- ✅ Explore specific sites
- ✅ Save results to CSV

Perfect for quick testing and exploration!
