# Web Contact Scraper - Apify Actor

Fast, intelligent web scraper for extracting contact information from websites.

## Features

✅ **Email Extraction** - Finds and validates email addresses
✅ **Phone Extraction** - Extracts and validates phone numbers
✅ **Company Info** - Extracts company name and description
✅ **Address Extraction** - Finds physical addresses using multiple methods
✅ **Social Links** - Extracts LinkedIn, Twitter, Facebook, Instagram, etc.
✅ **Multi-Page Discovery** - Automatically finds contact, about, and team pages
✅ **Smart Validation** - Filters out junk emails and fake phone numbers
✅ **Fast Performance** - 1-2 seconds per URL using async HTTP

## Input

### Start URLs (Recommended)
```json
{
  "startUrls": [
    { "url": "https://example.com" },
    { "url": "https://company.com" }
  ],
  "fastMode": true,
  "maxPages": 3,
  "maxConcurrency": 5
}
```

### Simple URLs
```json
{
  "urls": [
    "https://example.com",
    "https://company.com"
  ]
}
```

### Options

- **fastMode** (boolean, default: true) - Use fast HTML scraping. Disable for JavaScript-heavy sites.
- **maxPages** (integer, default: 1) - Maximum pages to scrape per website (1-10)
- **enableValidation** (boolean, default: false) - Enable SMTP email validation (slower)
- **maxConcurrency** (integer, default: 5) - Number of URLs to scrape concurrently (1-20)
- **blockKeywords** (string) - Comma-separated keywords to filter from results (e.g., "noreply,spam")
- **proxyConfiguration** (object) - Proxy settings (Apify proxy recommended)

## Output

Results are saved to the dataset with the following fields:

```json
{
  "url": "https://example.com",
  "status": "success",
  "emails": ["contact@example.com", "info@example.com"],
  "phones": ["+1-555-0100", "+1-555-0200"],
  "company_name": "Example Corp",
  "company_description": "Leading provider of...",
  "addresses": ["123 Main St, New York, NY 10001"],
  "social_links": {
    "linkedin": ["https://linkedin.com/company/example"],
    "twitter": ["https://twitter.com/example"]
  },
  "confidence_score": 0.85,
  "fetch_time": 1.23,
  "pages_scanned": 3,
  "leadership_count": 5
}
```

## Performance

- **Speed**: 1-2 seconds per URL
- **Memory**: ~500MB for 100 URLs
- **Concurrency**: 5-10 URLs in parallel
- **Success Rate**: 95%+ for accessible sites

## Use Cases

- **Lead Generation** - Extract contact info from company websites
- **Market Research** - Gather company information at scale
- **Data Enrichment** - Add contact details to existing databases
- **Competitor Analysis** - Collect competitor contact information
- **Sales Prospecting** - Build targeted contact lists

## Tips for Best Results

1. **Use Apify Proxy** - Improves success rate and avoids blocking
2. **Start with Fast Mode** - Faster and works for 80% of sites
3. **Increase maxPages** - Scrape contact/about pages for more data
4. **Enable Validation** - For higher quality emails (slower)
5. **Use Block Keywords** - Filter out unwanted emails (noreply, spam)

## Limitations

- JavaScript-heavy sites may need `fastMode: false`
- Some sites use CAPTCHA or bot protection
- Addresses may not be found if embedded in images/maps
- SMTP validation adds 3-5 seconds per URL

## Local Testing

```bash
# Install Apify CLI
npm install -g apify-cli

# Test locally
apify run

# Push to Apify
apify push
```

## Support

For issues or questions, check the documentation or contact support.

## Version

1.0.0 - Initial release
