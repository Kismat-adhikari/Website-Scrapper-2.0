# Scraper Email Validation Integration Guide

Step-by-step guide to integrate the email validator module into the existing web scraper.

## Quick Integration (5 minutes)

### Step 1: Install Dependencies

```bash
pip install dnspython
```

### Step 2: Add Import to scraper.py

At the top of `scraper.py`, add:

```python
from email_validator import (
    EmailValidator,
    EmailValidationPipeline,
    create_validator,
    EmailValidationResult
)
```

### Step 3: Initialize Validator in WebScraper Class

In the `WebScraper.__init__()` method, add:

```python
class WebScraper:
    def __init__(self, proxy_manager, timeout=10, enable_precheck=True, 
                 hard_mode_delay=0.5, max_pages_per_site=10):
        # ... existing code ...
        
        # NEW: Initialize email validator
        self.email_validator = create_validator(enable_smtp=False)
        self.validation_pipeline = EmailValidationPipeline(self.email_validator)
```

### Step 4: Validate Emails After Extraction

In the `_extract_from_html()` method, after extracting emails:

```python
def _extract_from_html(self, url: str, html: str):
    # ... existing extraction code ...
    emails, phones, leadership_count, pages_scanned, social_links = ...
    
    # NEW: Validate emails
    if emails:
        validation_result = self.validation_pipeline.process_scraper_result(
            emails=list(emails),
            website_url=url,
            scraper_confidence=0.5  # Or use actual scraper confidence
        )
        
        # Use only validated emails
        validated_emails = validation_result['validated_emails']
        emails = {e.email for e in validated_emails}
        
        # Log validation summary
        summary = validation_result['summary']
        logger.info(
            f"Email validation for {url}: "
            f"Extracted={len(list(emails))}, Valid={summary.valid_emails}, "
            f"AvgConfidence={summary.average_confidence}"
        )
    
    return emails, phones, leadership_count, pages_scanned, social_links
```

### Step 5: Export Validation Details to CSV (Optional)

In the `main()` function, after saving results:

```python
# Write results to CSV with timestamp
if results:
    # ... existing CSV write code ...
    
    # NEW: Write validation details
    validation_file = output_file.replace('.csv', '_validation.csv')
    all_validation_results = []
    
    for result in results:
        if hasattr(result, 'validation_results'):
            all_validation_results.extend(result.validation_results)
    
    if all_validation_results:
        with open(validation_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = all_validation_results[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([r.to_dict() for r in all_validation_results])
        logger.info(f"Validation details saved to {validation_file}")
```

## Full Integration Example

Here's a complete example of the modified scraper code:

```python
# At top of scraper.py
from email_validator import (
    EmailValidator,
    EmailValidationPipeline,
    create_validator
)

class WebScraper:
    def __init__(self, proxy_manager, timeout=10, enable_precheck=True, 
                 hard_mode_delay=0.5, max_pages_per_site=10):
        # ... existing initialization ...
        self.proxy_manager = proxy_manager
        self.timeout = timeout
        self.precheck = PreCheckSystem(timeout=5) if enable_precheck else None
        self.extractor = ContactExtractor()
        self.page_discovery = PageDiscovery(max_pages=max_pages_per_site)
        self.mode_selector = FetchModeSelector()
        self.retry_strategy = RetryStrategy(max_retries=5)
        self.hard_mode_delay = hard_mode_delay
        
        # NEW: Initialize email validator
        self.email_validator = create_validator(enable_smtp=False)
        self.validation_pipeline = EmailValidationPipeline(self.email_validator)
    
    def _extract_from_html(self, url: str, html: str):
        """Extract contact information from HTML"""
        emails = set()
        phones = set()
        leadership_count = 0
        pages_scanned = 1
        social_links = {}
        
        # Extract emails
        extracted_emails = self.extractor.extract_emails(html)
        
        # NEW: Validate emails
        if extracted_emails:
            validation_result = self.validation_pipeline.process_scraper_result(
                emails=list(extracted_emails),
                website_url=url,
                scraper_confidence=0.5
            )
            
            # Use validated emails
            validated_emails = validation_result['validated_emails']
            emails = {e.email for e in validated_emails}
            
            # Log summary
            summary = validation_result['summary']
            logger.debug(
                f"Email validation for {url}: "
                f"Extracted={len(extracted_emails)}, Valid={summary.valid_emails}, "
                f"AvgConfidence={summary.average_confidence}"
            )
        
        # Extract other data
        phones = self.extractor.extract_phones(html)
        leadership_count = self.extractor.extract_leadership(html)
        social_links = self.extractor.extract_social_links(html)
        
        # ... rest of extraction code ...
        
        return emails, phones, leadership_count, pages_scanned, social_links


def main():
    # ... existing code ...
    
    # Write results to CSV with timestamp
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.output == 'results.csv':
            output_file = f"results_{timestamp}.csv"
        else:
            name, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'csv')
            output_file = f"{name}_{timestamp}.{ext}"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(results[0]).keys())
            writer.writeheader()
            writer.writerows([asdict(r) for r in results])
        logger.info(f"Results saved to {output_file}")
        
        # NEW: Write validation details
        validation_file = output_file.replace('.csv', '_validation.csv')
        all_validation_results = []
        
        for result in results:
            if hasattr(result, 'validation_results'):
                all_validation_results.extend(result.validation_results)
        
        if all_validation_results:
            with open(validation_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = all_validation_results[0].to_dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([r.to_dict() for r in all_validation_results])
            logger.info(f"Validation details saved to {validation_file}")
    else:
        logger.error("No results to save")
```

## Configuration Options

### Disable Email Validation

If you want to skip email validation:

```python
# In WebScraper.__init__()
self.email_validator = None
self.validation_pipeline = None

# In _extract_from_html()
if self.email_validator and extracted_emails:
    # ... validation code ...
else:
    emails = extracted_emails
```

### Enable SMTP Verification

For highest accuracy (slower):

```python
self.email_validator = create_validator(enable_smtp=True)
```

### Domain Whitelist

Only accept emails from specific domains:

```python
self.email_validator = create_validator(
    domain_whitelist=['example.com', 'company.org']
)
```

### Domain Blacklist

Never accept emails from specific domains:

```python
self.email_validator = create_validator(
    domain_blacklist=['spam.com', 'phishing.net']
)
```

## Output Files

After integration, you'll get two CSV files:

### 1. Main Results (results_TIMESTAMP.csv)

Original scraper output with validated emails:

```csv
url,status,emails,phones,pages_scanned,leadership_count,email_list,confidence_score,...
https://example.com,success,"['contact@example.com', 'sales@example.com']",[...],3,2,contact@example.com; sales@example.com,0.75,...
```

### 2. Validation Details (results_TIMESTAMP_validation.csv)

Detailed validation results for each email:

```csv
email,is_valid,confidence_score,reason,syntax_valid,mx_exists,is_disposable,smtp_verified,validation_timestamp
contact@example.com,True,0.95,valid,True,True,False,False,2025-11-23T23:30:00.123456
test@mailinator.com,False,0.4,disposable_domain,True,True,True,False,2025-11-23T23:30:01.234567
```

## Testing Integration

### Test 1: Basic Validation

```bash
python scraper.py https://example.com
```

Check logs for:
```
Email validation for https://example.com: Extracted=5, Valid=4, AvgConfidence=0.82
```

### Test 2: Batch Processing

```bash
python scraper.py sample_urls.txt
```

Check for validation CSV file:
```
results_20251123_232315_validation.csv
```

### Test 3: Run Examples

```bash
python email_validator_example.py
```

This will show all validation features in action.

## Performance Impact

- **Syntax check:** < 1ms per email
- **Disposable check:** < 1ms per email
- **MX lookup:** 50-500ms per domain (cached)
- **Total overhead:** ~100-200ms per website

For 20 websites with 5 emails each:
- Without validation: ~30 seconds
- With validation: ~35-40 seconds (minimal impact)

## Troubleshooting

### Issue: DNS Lookup Failures

**Error:** `dns.resolver.NXDOMAIN` or timeout

**Solution:** This is normal for invalid domains. The validator handles it gracefully.

### Issue: SMTP Rate Limiting

**Error:** Connection refused or timeout on SMTP check

**Solution:** Keep SMTP disabled (default). It's not necessary for most use cases.

### Issue: False Positives

**Problem:** Valid emails marked as invalid

**Solution:**
1. Check if domain has MX records: `nslookup -type=MX example.com`
2. Use domain whitelist for known domains
3. Lower confidence threshold

### Issue: Performance Degradation

**Problem:** Scraper is slower with validation

**Solution:**
1. Disable SMTP check (already default)
2. Use domain whitelist to skip validation for known domains
3. Run validation in parallel with ThreadPoolExecutor

## Monitoring

### Log Validation Metrics

Add to your monitoring:

```python
# Track validation statistics
validation_stats = {
    'total_emails': 0,
    'valid_emails': 0,
    'invalid_emails': 0,
    'avg_confidence': 0.0
}

for result in results:
    if hasattr(result, 'validation_results'):
        summary = result['summary']
        validation_stats['total_emails'] += summary.total_emails
        validation_stats['valid_emails'] += summary.valid_emails
        validation_stats['invalid_emails'] += summary.invalid_emails

print(f"Validation Rate: {validation_stats['valid_emails']}/{validation_stats['total_emails']}")
```

## Next Steps

1. ✅ Install dnspython
2. ✅ Add imports to scraper.py
3. ✅ Initialize validator in WebScraper
4. ✅ Add validation to _extract_from_html()
5. ✅ Export validation details to CSV
6. ✅ Test with sample URLs
7. ✅ Monitor logs and metrics
8. ✅ Adjust configuration as needed

## Support

For issues or questions:
1. Check EMAIL_VALIDATOR_GUIDE.md for detailed documentation
2. Run email_validator_example.py to see all features
3. Check logs for validation errors
4. Review validation CSV for detailed results

## Summary

The email validator provides:
- ✅ Multi-stage validation (syntax, MX, disposable, SMTP)
- ✅ Confidence scoring (0.0-1.0)
- ✅ Seamless scraper integration
- ✅ CSV export with details
- ✅ Thread-safe logging
- ✅ Minimal performance impact
- ✅ Easy configuration

Perfect for ensuring high-quality email data!
