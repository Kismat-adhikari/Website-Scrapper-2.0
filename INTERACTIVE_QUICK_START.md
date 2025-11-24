# Interactive Mode - Quick Start

## The Simplest Way to Test

### Step 1: Install
```bash
pip install -r requirements.txt
```

### Step 2: Run
```bash
python scraper.py
```

### Step 3: Paste URLs
```
Enter URL (or command): https://example.com
```

Press Enter and watch it scrape!

## That's It!

The scraper will:
1. Scrape the URL
2. Show you the results
3. Ask for the next URL

## Commands While Running

```
https://example.com     ← Paste a URL
results                 ← See all results so far
clear                   ← Clear results
quit                    ← Save and exit
```

## Example

```bash
$ python scraper.py

============================================================
INTERACTIVE MODE - Paste URLs one at a time
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

Enter URL (or command): quit

✓ Results saved to results.csv
✓ Total URLs scraped: 2
```

## View Results

```bash
cat results.csv
```

## That's All!

No arguments needed. Just run `python scraper.py` and paste URLs!
