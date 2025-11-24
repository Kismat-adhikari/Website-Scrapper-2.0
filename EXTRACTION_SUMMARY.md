# Extraction Summary

Quick reference for contact information extraction and confidence scoring.

## What Gets Extracted

### Emails
- Valid email addresses from text and links
- Filtered to exclude no-reply addresses
- Typical: 1-10 per site

**Excluded**:
- noreply, no-reply, do-not-reply, donotreply
- notification, notifications, automated
- mailer-daemon, postmaster

### Phone Numbers
- US format: (555) 123-4567, 555-123-4567
- International: +1-555-123-4567, +44 20 7946 0958
- Minimum 6 digits required
- Normalized to XXX-XXX-XXXX format
- Typical: 0-3 per site

### Leadership Titles
- CEO, CTO, CMO, COO, CFO, CRO
- Founder, Co-Founder
- President, Vice President, VP
- Director, Manager, Lead, Head, Chief
- Partner, Principal
- Typical: 0-20 per site

### Social Media Links
- LinkedIn (company and personal)
- Twitter
- Facebook
- Instagram
- GitHub
- YouTube
- Typical: 0-6 platforms per site

## Confidence Score Breakdown

```
Total Score = Email Score + Phone Score + Pages Score + 
              Leadership Score + Fetch Score + Retry Score
```

### Component Scores

| Component | Max | Calculation |
|-----------|-----|-------------|
| Emails | 0.25 | min(count/5, 1.0) × 0.25 |
| Phones | 0.20 | min(count/3, 1.0) × 0.20 |
| Pages | 0.20 | min(count/5, 1.0) × 0.20 |
| Leadership | 0.15 | min(count/10, 1.0) × 0.15 |
| Fetch | 0.10 | Fast HTML: 0.10, JS: 0.08, Hard: 0.05 |
| Retries | 0.10 | 0 retries: 0.10, 1-2: 0.07, 3+: 0.03 |

### Score Ranges

| Range | Level | Meaning |
|-------|-------|---------|
| 0.75-1.00 | High | Excellent data quality |
| 0.50-0.74 | Medium | Good data quality |
| 0.25-0.49 | Low | Limited data |
| 0.00-0.24 | Very Low | Minimal/no data |

## Quick Examples

### High Confidence (0.82)
```
5 emails × 0.25 = 0.25
2 phones × 0.20 = 0.13
3 pages × 0.20 = 0.12
8 leadership × 0.15 = 0.12
Fast HTML = 0.10
0 retries = 0.10
Total = 0.82
```

### Medium Confidence (0.58)
```
2 emails × 0.25 = 0.10
1 phone × 0.20 = 0.07
2 pages × 0.20 = 0.08
3 leadership × 0.15 = 0.05
JS Rendering = 0.08
1 retry = 0.07
Total = 0.45
```

### Low Confidence (0.12)
```
0 emails × 0.25 = 0.00
0 phones × 0.20 = 0.00
1 page × 0.20 = 0.04
0 leadership × 0.15 = 0.00
Hard Mode = 0.05
5 retries = 0.03
Total = 0.12
```

## Output CSV Columns

| Column | Example | Notes |
|--------|---------|-------|
| url | https://example.com | Target URL |
| status | success | success/failed/skipped |
| emails | ['contact@example.com'] | List format |
| phones | ['555-123-4567'] | List format |
| pages_scanned | 3 | Number of pages |
| leadership_count | 5 | Total mentions |
| email_list | contact@example.com | Semicolon-separated |
| phone_list | 555-123-4567 | Semicolon-separated |
| social_links | {"linkedin": [...]} | JSON format |
| confidence_score | 0.82 | 0-1 range |
| reason | Success | Status message |
| load_time | 1.23 | Seconds |
| ssl_valid | true | Boolean |
| bot_protection | null | Protection type |
| scrape_mode | normal | Scrape mode |
| fetch_mode | fast_html | Fetch method |
| retry_count | 0 | Number of retries |

## Filtering Rules

### Email Filtering
```
✓ contact@example.com
✓ sales@example.com
✓ john.doe@example.com
✗ noreply@example.com (no-reply)
✗ notifications@example.com (notification)
✗ automated@example.com (automated)
```

### Phone Filtering
```
✓ 555-123-4567 (10 digits)
✓ +1-555-123-4567 (international)
✓ +44 20 7946 0958 (international)
✗ 123-45 (less than 6 digits)
✗ abc-def-ghij (not numeric)
```

### Leadership Filtering
```
✓ "John Smith, CEO" (title)
✓ "VP of Sales" (title)
✓ "Founder and President" (titles)
✗ "ceo-level thinking" (not a title)
✗ "leadership qualities" (not a title)
```

## Performance Metrics

### Extraction Speed
- Email extraction: ~10-50ms per page
- Phone extraction: ~10-50ms per page
- Leadership extraction: ~20-100ms per page
- Social link extraction: ~20-100ms per page

### Typical Results
- Emails: 1-10 per site
- Phones: 0-3 per site
- Leadership: 0-20 per site
- Social links: 0-6 platforms

### Confidence Distribution
- High (0.75+): 30-40% of sites
- Medium (0.50-0.74): 40-50% of sites
- Low (0.25-0.49): 10-20% of sites
- Very Low (<0.25): 5-10% of sites

## Common Patterns

### High Confidence Sites
- Have dedicated contact page
- Have team/leadership page
- Multiple emails listed
- Phone number provided
- Social media links in footer
- Leadership titles mentioned

### Medium Confidence Sites
- Have contact page
- Some emails found
- Limited phone numbers
- Some social links
- Few leadership mentions

### Low Confidence Sites
- No dedicated contact page
- Few emails found
- No phone numbers
- No social links
- No leadership mentions

## Troubleshooting

### No Emails Found
→ Check contact page discovery
→ Try JS Rendering mode
→ Verify emails aren't in images

### No Phones Found
→ Check if site has phone numbers
→ Verify format (US vs international)
→ Try different pages

### Low Leadership Count
→ Check team/leadership pages
→ Verify title spelling
→ Look for variations (VP vs Vice President)

### No Social Links Found
→ Check footer for social icons
→ Check about/team pages
→ Verify links are in HTML

## Tips for Better Results

1. **Use page discovery**: Automatically finds contact/team pages
2. **Check confidence scores**: Higher = better quality
3. **Review logs**: Check `scraper.log` for details
4. **Validate manually**: Verify extracted data
5. **Adjust settings**: Customize for your use case

## Related Files

- [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md) - Detailed extraction guide
- [README.md](README.md) - Feature overview
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

## Quick Reference

### Email Keywords to Exclude
```
noreply, no-reply, do-not-reply, donotreply, no_reply,
notification, notifications, automated, auto-reply, autoreply,
mailer-daemon, postmaster
```

### Leadership Keywords to Include
```
ceo, cto, cmo, coo, cfo, cro,
founder, co-founder, cofounder,
president, vice president, vp,
director, executive director,
manager, general manager,
lead, head, chief,
partner, principal
```

### Social Platforms Detected
```
linkedin, twitter, facebook, instagram, github, youtube
```

### Confidence Score Formula
```
Score = (emails/5 × 0.25) + (phones/3 × 0.20) + (pages/5 × 0.20) +
        (leadership/10 × 0.15) + fetch_bonus + retry_bonus
```

---

For detailed information, see [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md)
