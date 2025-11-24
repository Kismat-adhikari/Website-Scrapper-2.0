# Social Links Extraction Guide

Complete guide to extracting company contact details, social links, and addresses from websites.

## Overview

The scraper extracts:
- ✅ Company name
- ✅ Physical address
- ✅ Phone numbers (validated)
- ✅ Social media links
- ✅ Email addresses

## What Gets Extracted

### Company Name

**Where to look:**
- `<footer>` sections
- `<header>` sections
- `<h1>` tags near top of page
- Meta tags (`og:site_name`, `og:title`)

**Selection criteria:**
- Largest/boldest text near footer or top
- Text in `<strong>`, `<b>`, or large font sizes
- Company branding areas

**Examples:**
```html
<!-- Footer company name -->
<footer>
  <h2>Little Collins NYC</h2>  ← Extract this
  <p>© 2024 All rights reserved</p>
</footer>

<!-- Header company name -->
<header>
  <h1>Example Inc.</h1>  ← Extract this
</header>
```

### Address & Phone

**Where to look:**
- `<footer>` sections
- Contact pages
- "About Us" pages
- Structured data (schema.org)

**Format patterns:**
```
Street, City, State ZIP
Street, City, State ZIP (Phone)
Street
City, State ZIP
Phone: XXX-XXX-XXXX
```

**Examples:**
```html
<!-- Typical footer address -->
<footer>
  <p>708 3rd Ave, New York, NY 10017</p>
  <p>Phone: (212) 308-1969</p>
</footer>

<!-- Contact page -->
<div class="contact-info">
  <p>123 Main St, San Francisco, CA 94105</p>
  <p>+1-415-123-4567</p>
</div>
```

**Extraction rules:**
- Extract full address (street, city, state, zip)
- Normalize phone numbers (strip punctuation, keep country code)
- Ignore numbers NOT near address keywords
- Validate phone format (10-15 digits)

### Social Links

**Where to look:**
- `<footer>` sections
- Social media icon sections
- `<a>` tags with social platform names
- Links with social media icons

**Valid social platforms:**
- Facebook
- Twitter / X
- LinkedIn
- Instagram
- YouTube
- TikTok
- GitHub
- Pinterest
- Snapchat
- WhatsApp
- Telegram

**Examples:**
```html
<!-- Social links in footer -->
<footer>
  <div class="social-links">
    <a href="https://www.facebook.com/example">
      <img src="facebook-icon.png" alt="Facebook">
    </a>
    <a href="https://twitter.com/example">
      <img src="twitter-icon.png" alt="Twitter">
    </a>
    <a href="https://www.linkedin.com/company/example">
      <img src="linkedin-icon.png" alt="LinkedIn">
    </a>
  </div>
</footer>

<!-- Social links with text -->
<div class="social">
  <a href="https://instagram.com/example">Follow us on Instagram</a>
  <a href="https://youtube.com/@example">Subscribe on YouTube</a>
</div>
```

**Extraction rules:**
- Extract `href` URL from `<a>` tags
- Match against social platform domains
- Ignore placeholder links (`#`, `javascript:void(0)`)
- Ignore empty or invalid URLs
- Normalize URLs (remove tracking params if needed)

## Output Format

### JSON Format

```json
{
  "company_name": "Little Collins NYC",
  "address": "708 3rd Ave, New York, NY 10017",
  "phone": "+12123081969",
  "emails": [
    "contact@littlecollinsnyc.com",
    "info@littlecollinsnyc.com"
  ],
  "social_links": {
    "facebook": "https://www.facebook.com/littlecollinscafe",
    "instagram": "https://www.instagram.com/littlecollinscafe",
    "twitter": "https://twitter.com/littlecollinscafe"
  }
}
```

### CSV Format

```csv
url,company_name,address,phone,emails,social_links,confidence_score
https://example.com,Example Inc.,708 3rd Ave NYC NY 10017,+12123081969,contact@example.com; info@example.com,facebook: https://facebook.com/example; twitter: https://twitter.com/example,0.85
```

### Table Format

| Field | Value |
|-------|-------|
| Company Name | Little Collins NYC |
| Address | 708 3rd Ave, New York, NY 10017 |
| Phone | +1-212-308-1969 |
| Emails | contact@littlecollinscafe.com |
| Facebook | https://www.facebook.com/littlecollinscafe |
| Instagram | https://www.instagram.com/littlecollinscafe |
| Twitter | https://twitter.com/littlecollinscafe |

## Extraction Process

### Step 1: Clean HTML

```python
# Remove script and style tags
soup = BeautifulSoup(html, 'html.parser')
for script in soup(['script', 'style']):
    script.decompose()
```

### Step 2: Extract Company Name

```python
# Look in footer first
footer = soup.find('footer')
if footer:
    h1 = footer.find('h1') or footer.find('h2')
    if h1:
        company_name = h1.get_text().strip()

# Fallback to header
if not company_name:
    header = soup.find('header')
    if header:
        h1 = header.find('h1')
        if h1:
            company_name = h1.get_text().strip()
```

### Step 3: Extract Address

```python
# Look for address patterns
address_pattern = r'\d+\s+[\w\s]+(?:St|Ave|Blvd|Rd|Dr|Ln|Court|Place|Way|Parkway)'
addresses = re.findall(address_pattern, text)

# Validate and normalize
for addr in addresses:
    if validate_address(addr):
        extracted_address = addr
```

### Step 4: Extract Phone

```python
# Look for phone near address
phone_pattern = r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
phones = re.findall(phone_pattern, text)

# Validate
for phone in phones:
    if validate_phone(phone):
        extracted_phone = phone
```

### Step 5: Extract Social Links

```python
# Find all links
links = soup.find_all('a', href=True)

social_links = {}
for link in links:
    href = link['href']
    
    # Skip invalid links
    if href in ['#', 'javascript:void(0)'] or not href:
        continue
    
    # Check against social platforms
    if 'facebook.com' in href:
        social_links['facebook'] = href
    elif 'twitter.com' in href or 'x.com' in href:
        social_links['twitter'] = href
    elif 'linkedin.com' in href:
        social_links['linkedin'] = href
    elif 'instagram.com' in href:
        social_links['instagram'] = href
    elif 'youtube.com' in href:
        social_links['youtube'] = href
    # ... etc for other platforms
```

## Validation Rules

### Address Validation

✅ **Valid:**
- `708 3rd Ave, New York, NY 10017`
- `123 Main Street, San Francisco, CA 94105`
- `456 Oak Boulevard, Boston, MA 02101`

❌ **Invalid:**
- `123` (no street name)
- `Street` (no number)
- `Random text` (not an address)

### Phone Validation

✅ **Valid:**
- `(212) 308-1969`
- `212-308-1969`
- `2123081969`
- `+1-212-308-1969`

❌ **Invalid:**
- `555-1234` (too short)
- `000-000-0000` (all zeros)
- `111-111-1111` (repeating)
- `123456789012345` (too long)

### Social Link Validation

✅ **Valid:**
- `https://www.facebook.com/example`
- `https://twitter.com/example`
- `https://www.linkedin.com/company/example`
- `https://instagram.com/example`

❌ **Invalid:**
- `#` (placeholder)
- `javascript:void(0)` (placeholder)
- `` (empty)
- `https://example.com` (not social)

## Cleanup Rules

### Remove Junk Numbers

Only keep numbers that:
- Have proper formatting (dashes, parentheses, spaces)
- Are 10-15 digits long
- Don't have repeating patterns
- Are near address keywords

### Remove Invalid Social Links

Skip links that:
- Are placeholders (`#`, `javascript:void(0)`)
- Are empty or null
- Don't match social platform domains
- Are tracking/redirect URLs

### Remove Script/Style Content

```python
# Remove before extraction
for tag in soup(['script', 'style']):
    tag.decompose()
```

## Current Implementation

The scraper already extracts:

### Company Name
- From meta tags
- From page title
- From header/footer

### Address
- From footer sections
- From contact pages
- Validated format

### Phone Numbers
- Strict format validation
- No junk numbers
- Normalized format

### Social Links
- From footer
- From contact sections
- Validated URLs

### Emails
- From contact pages
- Validated format
- No fake emails

## Example Output

### Little Collins NYC

```json
{
  "url": "https://www.littlecollinsnyc.com/",
  "company_name": "Little Collins NYC",
  "address": "708 3rd Ave, New York, NY 10017",
  "phone": "+1-212-308-1969",
  "emails": ["contact@littlecollinscafe.com"],
  "social_links": {
    "facebook": "https://www.facebook.com/littlecollinscafe",
    "instagram": "https://www.instagram.com/littlecollinscafe",
    "twitter": "https://twitter.com/littlecollinscafe"
  },
  "confidence_score": 0.85
}
```

## Best Practices

1. **Always validate** before including data
2. **Normalize formats** (phone, address, URLs)
3. **Remove duplicates** (same URL in different formats)
4. **Skip placeholders** (empty links, javascript:void(0))
5. **Prioritize footer** (most reliable location)
6. **Use context** (look for keywords like "contact", "follow", "address")
7. **Handle edge cases** (international formats, special characters)

## Troubleshooting

### No Company Name Found
- Check if site uses different structure
- Look in meta tags
- Check page title

### No Address Found
- Site might not have physical address
- Check contact page
- Look for structured data

### No Social Links Found
- Site might not have social presence
- Check footer carefully
- Look for icon-based links

### Invalid Phone Numbers
- Validate format before including
- Check for repeating patterns
- Ensure proper length (10-15 digits)

## Summary

The extraction system:
- ✅ Finds company names in headers/footers
- ✅ Extracts addresses with validation
- ✅ Gets phone numbers (no junk)
- ✅ Collects social media links
- ✅ Validates all data
- ✅ Outputs clean, structured results

Perfect for getting complete company contact information!
