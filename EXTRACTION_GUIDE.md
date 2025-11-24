# Extraction Guide

Comprehensive guide to contact information extraction and confidence scoring.

## Overview

The scraper extracts multiple types of contact information from websites:
- Emails (filtered)
- Phone numbers (normalized)
- Leadership titles
- Social media links
- Confidence scores

## Email Extraction

### What Gets Extracted
- Valid email addresses in standard format
- Emails from links, text, and HTML attributes
- Multiple emails per page

### What Gets Filtered Out
- No-reply addresses: noreply, no-reply, do-not-reply, donotreply, no_reply
- Notification addresses: notification, notifications, automated, auto-reply, autoreply
- System addresses: mailer-daemon, postmaster
- File extensions: .png, .jpg, .gif, .pdf

### Examples

**Extracted**:
- contact@example.com ✓
- sales@example.com ✓
- john.doe@example.com ✓
- support+help@example.com ✓

**Filtered**:
- noreply@example.com ✗ (no-reply)
- notifications@example.com ✗ (notification)
- automated@example.com ✗ (automated)
- contact.png ✗ (file extension)

### Email Patterns
```regex
\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b
```

## Phone Number Extraction

### What Gets Extracted
- US format: (555) 123-4567, 555-123-4567, 555.123.4567
- International format: +1-555-123-4567, +44 20 7946 0958
- Minimum 6 digits required

### Normalization
- US format (10 digits): Normalized to XXX-XXX-XXXX
- International format: Kept as-is with country code
- Duplicates removed

### Examples

**Extracted**:
- 555-123-4567 ✓
- (555) 123-4567 ✓
- +1-555-123-4567 ✓
- +44 20 7946 0958 ✓

**Filtered**:
- 123-45 ✗ (less than 6 digits)
- 555 ✗ (too short)
- abc-def-ghij ✗ (not numeric)

### Phone Patterns
```regex
# US Format
\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b

# International Format
\+?[1-9]\d{1,14}
```

## Leadership Detection

### Titles Detected
- **C-Level**: CEO, CTO, CMO, COO, CFO, CRO
- **Founders**: Founder, Co-Founder, Cofounder
- **Executive**: President, Vice President, VP
- **Management**: Director, Executive Director, Manager, General Manager
- **Other**: Lead, Head, Chief, Partner, Principal

### How It Works
- Searches for exact word matches (case-insensitive)
- Uses word boundaries to avoid partial matches
- Counts total occurrences across all pages
- Normalized to 0-50 range

### Examples

**Detected**:
- "John Smith, CEO" → 1 mention
- "Jane Doe, VP of Sales" → 1 mention
- "CEO and Founder" → 2 mentions
- "Leadership Team: CEO, CTO, CFO" → 3 mentions

**Not Detected**:
- "ceo-level thinking" ✗ (not a title)
- "The chief reason" ✗ (not a title)
- "leadership qualities" ✗ (not a title)

### Leadership Keywords
```
ceo, cto, cmo, coo, cfo, cro,
founder, co-founder, cofounder,
president, vice president, vp,
director, executive director,
manager, general manager,
lead, head, chief,
partner, principal
```

## Social Media Link Extraction

### Platforms Detected
- **LinkedIn**: Company and personal profiles
- **Twitter**: User accounts
- **Facebook**: Pages and profiles
- **Instagram**: User accounts
- **GitHub**: User and organization profiles
- **YouTube**: Channels and users

### How It Works
- Extracts from href attributes in links
- Extracts from text content
- Deduplicates URLs
- Returns as JSON object

### Examples

**Extracted**:
```json
{
  "linkedin": ["https://linkedin.com/company/example"],
  "twitter": ["https://twitter.com/example"],
  "github": ["https://github.com/example"]
}
```

### Social Media Patterns
```regex
linkedin: (?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/[\w-]+
twitter: (?:https?://)?(?:www\.)?twitter\.com/[\w]+
facebook: (?:https?://)?(?:www\.)?facebook\.com/[\w.-]+
instagram: (?:https?://)?(?:www\.)?instagram\.com/[\w.]+
github: (?:https?://)?(?:www\.)?github\.com/[\w-]+
youtube: (?:https?://)?(?:www\.)?youtube\.com/(?:c|channel|user)/[\w-]+
```

## Confidence Score Calculation

### Score Components

**1. Email Count (0-0.25)**
- 0 emails: 0.00
- 1-2 emails: 0.05-0.10
- 3-5 emails: 0.15-0.25
- 5+ emails: 0.25 (max)

**2. Phone Count (0-0.20)**
- 0 phones: 0.00
- 1 phone: 0.07
- 2-3 phones: 0.14-0.20
- 3+ phones: 0.20 (max)

**3. Pages Scanned (0-0.20)**
- 1 page: 0.04
- 2-3 pages: 0.08-0.12
- 4-5 pages: 0.16-0.20
- 5+ pages: 0.20 (max)

**4. Leadership Mentions (0-0.15)**
- 0 mentions: 0.00
- 1-5 mentions: 0.02-0.08
- 6-10 mentions: 0.09-0.15
- 10+ mentions: 0.15 (max)

**5. Fetch Method (0-0.10)**
- Fast HTML: 0.10 (best)
- JS Rendering: 0.08
- Hard Mode: 0.05 (worst)

**6. Retry Count (0-0.10)**
- 0 retries: 0.10 (best)
- 1-2 retries: 0.07
- 3+ retries: 0.03 (worst)

### Score Ranges

**High Confidence (0.75-1.00)**
- 4+ emails
- 2+ phones
- 3+ pages scanned
- 5+ leadership mentions
- Fast HTML or JS Rendering
- 0-1 retries

**Medium Confidence (0.50-0.74)**
- 2-3 emails
- 1 phone
- 2 pages scanned
- 2-4 leadership mentions
- Any fetch method
- 1-2 retries

**Low Confidence (0.25-0.49)**
- 1 email
- 0 phones
- 1 page scanned
- 0-1 leadership mentions
- Hard Mode
- 3+ retries

**Very Low Confidence (0.00-0.24)**
- 0 emails
- 0 phones
- 1 page scanned
- 0 leadership mentions
- Hard Mode
- 5+ retries

### Example Calculations

**Example 1: High Quality**
```
Emails: 5 → 0.25
Phones: 2 → 0.13
Pages: 3 → 0.12
Leadership: 8 → 0.12
Fetch: Fast HTML → 0.10
Retries: 0 → 0.10
Total: 0.82 (High Confidence)
```

**Example 2: Medium Quality**
```
Emails: 2 → 0.10
Phones: 1 → 0.07
Pages: 2 → 0.08
Leadership: 3 → 0.05
Fetch: JS Rendering → 0.08
Retries: 1 → 0.07
Total: 0.45 (Low-Medium Confidence)
```

**Example 3: Low Quality**
```
Emails: 0 → 0.00
Phones: 0 → 0.00
Pages: 1 → 0.04
Leadership: 0 → 0.00
Fetch: Hard Mode → 0.05
Retries: 5 → 0.03
Total: 0.12 (Very Low Confidence)
```

## Output Format

### CSV Columns

```
url,status,emails,phones,pages_scanned,leadership_count,
email_list,phone_list,social_links,confidence_score,reason,
load_time,ssl_valid,bot_protection,scrape_mode,fetch_mode,retry_count
```

### Example Row

```csv
https://example.com,success,"['contact@example.com', 'sales@example.com']",
"['555-123-4567', '555-987-6543']",3,5,
contact@example.com; sales@example.com,555-123-4567; 555-987-6543,
"{""linkedin"": [""https://linkedin.com/company/example""], ""twitter"": [""https://twitter.com/example""]}",
0.82,Success,1.23,true,,normal,fast_html,0
```

### JSON Social Links Format

```json
{
  "linkedin": ["https://linkedin.com/company/example"],
  "twitter": ["https://twitter.com/example"],
  "github": ["https://github.com/example"],
  "facebook": ["https://facebook.com/example"]
}
```

## Extraction Tips

### For Better Email Results
1. Check contact pages (automatically discovered)
2. Check team/leadership pages
3. Look for email addresses in text, not just links
4. Filter out no-reply addresses

### For Better Phone Results
1. Check contact pages
2. Look for international formats
3. Normalize to consistent format
4. Verify minimum 6 digits

### For Better Leadership Results
1. Scan team/leadership pages
2. Look for title mentions
3. Count all occurrences
4. Use word boundaries

### For Better Social Links
1. Check footer links
2. Check about/team pages
3. Look for social media icons
4. Extract from text content

## Troubleshooting

### No Emails Found
- Check if site has contact page
- Verify emails aren't in JavaScript
- Check if emails are in images
- Try JS Rendering mode

### No Phones Found
- Check if site has phone numbers
- Verify format (US vs international)
- Check if phones are in images
- Try different pages

### Low Leadership Count
- Check team/leadership pages
- Verify titles are spelled correctly
- Check for variations (VP vs Vice President)
- Look for title mentions in text

### No Social Links Found
- Check footer for social icons
- Check about/team pages
- Verify links are in HTML (not images)
- Check for different URL formats

## Advanced Usage

### Custom Email Filters
To add custom no-reply patterns, edit `ContactExtractor`:

```python
NO_REPLY_PATTERNS = [
    r'noreply', r'no-reply',
    r'your-pattern'  # Add here
]
```

### Custom Leadership Keywords
To add custom titles, edit `ContactExtractor`:

```python
LEADERSHIP_KEYWORDS = [
    'ceo', 'founder',
    'your-title'  # Add here
]
```

### Custom Social Platforms
To add custom social platforms, edit `ContactExtractor`:

```python
SOCIAL_PATTERNS = {
    'linkedin': r'...',
    'your-platform': r'your-pattern'  # Add here
}
```

## Performance

### Typical Extraction Results
- **Emails per site**: 1-10
- **Phones per site**: 0-3
- **Leadership mentions**: 0-20
- **Social links**: 0-6 platforms

### Extraction Time
- Email extraction: ~10-50ms per page
- Phone extraction: ~10-50ms per page
- Leadership extraction: ~20-100ms per page
- Social link extraction: ~20-100ms per page

## Best Practices

1. **Use page discovery**: Automatically finds contact/team pages
2. **Check confidence scores**: Higher scores = better data quality
3. **Review logs**: Check `scraper.log` for extraction details
4. **Validate results**: Verify extracted data manually
5. **Adjust thresholds**: Customize for your use case

## Related Documentation

- See [README.md](README.md) for output columns
- See [QUICK_START.md](QUICK_START.md) for usage examples
- See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
- Check `scraper.log` for detailed extraction logs
