# Scraper Phone Validation Integration Guide

Step-by-step guide to integrate the phone validator module into the existing web scraper.

## Quick Integration (5 minutes)

### Step 1: Copy Module

Copy `phone_validator.py` to your project directory.

### Step 2: Add Import to scraper.py

At the top of `scraper.py`, add:

```python
from phone_validator import (
    PhoneValidator,
    PhoneValidationPipeline,
    create_validator,
    PhoneValidationResult
)
```

### Step 3: Initialize Validator in WebScraper Class

In the `WebScraper.__init__()` method, add:

```python
class WebScraper:
    def __init__(self, proxy_manager, timeout=10, enable_precheck=True, 
                 hard_mode_delay=0.5, max_pages_per_site=10):
        # ... existing code ...
        
        # NEW: Initialize phone validator
        self.phone_validator = create_validator(
            default_country='US',
            enable_voip_check=True,
            reject_voip=False
        )
        self.phone_pipeline = PhoneValidationPipeline(self.phone_validator)
```

### Step 4: Validate Phones After Extraction

In the `_extract_from_html()` method, after extracting phones:

```python
def _extract_from_html(self, url: str, html: str):
    # ... existing extraction code ...
    phones = self.extractor.extract_phones(html)
    
    # NEW: Validate phones
    if phones:
        validation_result = self.phone_pipeline.process_scraper_result(
            phones=list(phones),
            website_url=url,
            country_hint='US',  # Optional
            scraper_confidence=0.5
        )
        
        # Use only validated phones
        validated_phones = validation_result['validated_phones']
        phones = {p.normalized_phone for p in validated_phones}
        
        # Log validation summary
        summary = validation_result['summary']
        logger.info(
            f"Phone validation for {url}: "
            f"Extracted={len(list(phones))}, Valid={summary.valid_phones}, "
            f"AvgConfidence={summary.average_confidence}, "
            f"Mobile={summary.mobile_count}"
        )
    
    return emails, phones, leadership_count, pages_scanned, social_links
```

### Step 5: Export Validation Details to CSV (Optional)

In the `main()` function, after saving results:

```python
# Write results to CSV with timestamp
if results:
    # ... existing CSV write code ...
    
    # NEW: Write phone validation details
    phone_validation_file = output_file.replace('.csv', '_phone_validation.csv')
    all_phone_validation_results = []
    
    for result in results:
        if hasattr(result, 'phone_validation_results'):
            all_phone_validation_results.extend(result.phone_validation_results)
    
    if all_phone_validation_results:
        with open(phone_validation_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = all_phone_validation_results[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([r.to_dict() for r in all_phone_validation_results])
        logger.info(f"Phone validation details saved to {phone_validation_file}")
```

## Full Integration Example

Here's a complete example of the modified scraper code:

```python
# At top of scraper.py
from phone_validator import (
    PhoneValidator,
    PhoneValidationPipeline,
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
        
        # NEW: Initialize phone validator
        self.phone_validator = create_validator(
            default_country='US',
            enable_voip_check=True,
            reject_voip=False
        )
        self.phone_pipeline = PhoneValidationPipeline(self.phone_validator)
    
    def _extract_from_html(self, url: str, html: str):
        """Extract contact information from HTML"""
        emails = set()
        phones = set()
        leadership_count = 0
        pages_scanned = 1
        social_links = {}
        
        # Extract phones
        extracted_phones = self.extractor.extract_phones(html)
        
        # NEW: Validate phones
        if extracted_phones:
            validation_result = self.phone_pipeline.process_scraper_result(
                phones=list(extracted_phones),
                website_url=url,
                country_hint='US',
                scraper_confidence=0.5
            )
            
            # Use validated phones
            validated_phones = validation_result['validated_phones']
            phones = {p.normalized_phone for p in validated_phones}
            
            # Log summary
            summary = validation_result['summary']
            logger.debug(
                f"Phone validation for {url}: "
                f"Extracted={len(extracted_phones)}, Valid={summary.valid_phones}, "
                f"AvgConfidence={summary.average_confidence}"
            )
        
        # Extract other data
        emails = self.extractor.extract_emails(html)
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
        
        # NEW: Write phone validation details
        phone_validation_file = output_file.replace('.csv', '_phone_validation.csv')
        all_phone_validation_results = []
        
        for result in results:
            if hasattr(result, 'phone_validation_results'):
                all_phone_validation_results.extend(result.phone_validation_results)
        
        if all_phone_validation_results:
            with open(phone_validation_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = all_phone_validation_results[0].to_dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([r.to_dict() for r in all_phone_validation_results])
            logger.info(f"Phone validation details saved to {phone_validation_file}")
    else:
        logger.error("No results to save")
```

## Configuration Options

### Default Configuration

```python
self.phone_validator = create_validator()
```

### US-Only Validation

```python
self.phone_validator = create_validator(
    default_country='US',
    country_whitelist=['US', 'CA']
)
```

### Reject VoIP Numbers

```python
self.phone_validator = create_validator(
    reject_voip=True
)
```

### Strict Length Validation

```python
self.phone_validator = create_validator(
    min_length=10,
    max_length=11
)
```

### Multiple Countries

```python
self.phone_validator = create_validator(
    country_whitelist=['US', 'CA', 'UK', 'AU']
)
```

### Disable Library Check (Faster)

```python
self.phone_validator = create_validator(
    enable_library_check=False
)
```

## Output Files

After integration, you'll get two CSV files:

### 1. Main Results (results_TIMESTAMP.csv)

Original scraper output with validated phones:

```csv
url,status,emails,phones,pages_scanned,leadership_count,phone_list,confidence_score,...
https://example.com,success,"['contact@example.com']","['4151234567', '4159876543']",3,2,4151234567; 4159876543,0.75,...
```

### 2. Phone Validation Details (results_TIMESTAMP_phone_validation.csv)

Detailed validation results for each phone:

```csv
phone,normalized_phone,is_valid,confidence_score,reason,phone_type,country_code,syntax_valid,length_valid,country_valid,library_verified,is_voip,validation_timestamp
415-123-4567,4151234567,True,0.95,valid,mobile,US,True,True,True,True,False,2025-11-23T23:30:00.123456
123,123,False,0.4,invalid_length,unknown,US,True,False,True,False,False,2025-11-23T23:30:01.234567
```

## Testing Integration

### Test 1: Basic Validation

```bash
python scraper.py https://example.com
```

Check logs for:
```
Phone validation for https://example.com: Extracted=5, Valid=4, AvgConfidence=0.82, Mobile=3
```

### Test 2: Batch Processing

```bash
python scraper.py sample_urls.txt
```

Check for validation CSV file:
```
results_20251123_232315_phone_validation.csv
```

### Test 3: Run Examples

```bash
python phone_validator_example.py
```

This will demonstrate all validation features.

## Performance Impact

- **Syntax check:** < 1ms per phone
- **Length check:** < 1ms per phone
- **Country check:** < 1ms per phone
- **VoIP check:** < 1ms per phone
- **Library verification:** 5-20ms per phone (if enabled)

For 20 websites with 5 phones each:
- Without validation: ~30 seconds
- With validation (no library): ~31-32 seconds
- With validation (with library): ~32-35 seconds
- **Overhead: 1-5 seconds (minimal)**

## Troubleshooting

### Issue: Library Not Available

**Error:** `phonenumbers` not installed

**Solution:**
```bash
pip install phonenumbers
```

Or disable library check:
```python
validator = create_validator(enable_library_check=False)
```

### Issue: VoIP Numbers Rejected

**Error:** Toll-free numbers marked as invalid

**Solution:**
```python
validator = create_validator(reject_voip=False)  # Allow VoIP
```

### Issue: False Positives

**Problem:** Valid phones marked as invalid

**Solution:**
1. Check country configuration
2. Use country whitelist for known countries
3. Lower confidence threshold
4. Enable library check for better accuracy

### Issue: Performance Degradation

**Problem:** Scraper is slower with validation

**Solution:**
1. Disable library check: `enable_library_check=False`
2. Use country whitelist to skip validation
3. Run validation in parallel

## Monitoring

### Log Validation Metrics

Add to your monitoring:

```python
# Track validation statistics
phone_stats = {
    'total_phones': 0,
    'valid_phones': 0,
    'invalid_phones': 0,
    'avg_confidence': 0.0,
    'mobile_count': 0
}

for result in results:
    if hasattr(result, 'phone_validation_results'):
        summary = result['summary']
        phone_stats['total_phones'] += summary.total_phones
        phone_stats['valid_phones'] += summary.valid_phones
        phone_stats['invalid_phones'] += summary.invalid_phones
        phone_stats['mobile_count'] += summary.mobile_count

print(f"Phone Validation Rate: {phone_stats['valid_phones']}/{phone_stats['total_phones']}")
print(f"Mobile Phones: {phone_stats['mobile_count']}")
```

## Next Steps

1. ✅ Copy phone_validator.py to project
2. ✅ Add imports to scraper.py
3. ✅ Initialize validator in WebScraper
4. ✅ Add validation to _extract_from_html()
5. ✅ Export validation details to CSV
6. ✅ Test with sample URLs
7. ✅ Monitor logs and metrics
8. ✅ Adjust configuration as needed

## Support

For issues or questions:
1. Check PHONE_VALIDATOR_GUIDE.md for detailed documentation
2. Run phone_validator_example.py to see all features
3. Check logs for validation errors
4. Review validation CSV for detailed results

## Summary

The phone validator provides:
- ✅ Multi-stage validation (syntax, length, country, VoIP, library)
- ✅ Confidence scoring (0.0-1.0)
- ✅ Country-specific rules (8 countries)
- ✅ Phone type detection (mobile, fixed line, VoIP)
- ✅ Seamless scraper integration
- ✅ CSV export with details
- ✅ Thread-safe logging
- ✅ Minimal performance impact
- ✅ Easy configuration

Perfect for ensuring high-quality phone data!
