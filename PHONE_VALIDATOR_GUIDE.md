# Phone Validator Module Guide

Comprehensive phone number validation module for the web scraper with multi-stage validation and confidence scoring.

## Overview

The phone validator provides:
- **Multi-stage validation** (syntax, length, country rules, VoIP check, library verification)
- **Confidence scoring** (0.0-1.0 per phone)
- **Country-specific rules** (US, UK, AU, DE, FR, JP, IN)
- **Phone type detection** (mobile, fixed line, VoIP)
- **Thread-safe logging** for parallel scraping
- **Seamless CSV integration** with existing scraper
- **Extensible design** for custom checks

## Installation

### Dependencies

```bash
# Required
# (no external dependencies required for basic validation)

# Optional (for enhanced validation)
pip install phonenumbers
```

The module uses:
- `phonenumbers` - Phone number validation and type detection (optional)
- `re` - Regular expressions (built-in)
- `threading` - Thread-safe logging (built-in)
- `logging` - Logging framework (built-in)
- `dataclasses` - Data structures (built-in)
- `enum` - Enumerations (built-in)

## Quick Start

### Basic Usage

```python
from phone_validator import create_validator

# Create validator with defaults
validator = create_validator()

# Validate phones from a website
phones = ['415-123-4567', '123', 'invalid', '+1-415-987-6543']
results, summary = validator.validate_phones(phones, 'https://example.com')

# Check results
for result in results:
    print(f"{result.phone}: {result.confidence_score:.2f} - {result.reason.value}")

# Get summary
print(f"Valid: {summary.valid_phones}/{summary.total_phones}")
print(f"Average confidence: {summary.average_confidence}")
```

### With Configuration

```python
# Create validator with custom settings
validator = create_validator(
    default_country='US',
    country_whitelist=['US', 'CA'],
    min_length=10,
    max_length=11,
    enable_voip_check=True,
    reject_voip=False
)

# Validate
results, summary = validator.validate_phones(phones, 'https://example.com')
```

## Integration with Scraper

### Step 1: Import in scraper.py

```python
from phone_validator import PhoneValidator, PhoneValidationPipeline, create_validator
```

### Step 2: Initialize in WebScraper class

```python
class WebScraper:
    def __init__(self, ...):
        # ... existing code ...
        self.phone_validator = create_validator(default_country='US')
        self.phone_pipeline = PhoneValidationPipeline(self.phone_validator)
```

### Step 3: Validate phones after extraction

```python
def _extract_from_html(self, url: str, html: str):
    # ... existing extraction code ...
    phones = self.extractor.extract_phones(html)
    
    # NEW: Validate phones
    validation_result = self.phone_pipeline.process_scraper_result(
        phones=list(phones),
        website_url=url,
        country_hint='US',  # Optional
        scraper_confidence=self.current_confidence
    )
    
    # Use validated phones
    validated_phones = validation_result['validated_phones']
    phones = {p.normalized_phone for p in validated_phones}
    
    return emails, phones, leadership_count, pages_scanned, social_links
```

### Step 4: Export validation details to CSV

```python
# In main() function, after scraping
if results:
    # Existing CSV write
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=asdict(results[0]).keys())
        writer.writeheader()
        writer.writerows([asdict(r) for r in results])
    
    # NEW: Write validation details
    validation_file = output_file.replace('.csv', '_phone_validation.csv')
    all_validation_results = []
    for result in results:
        all_validation_results.extend(result.phone_validation_results)
    
    if all_validation_results:
        with open(validation_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_validation_results[0].to_dict().keys())
            writer.writeheader()
            writer.writerows([r.to_dict() for r in all_validation_results])
```

## Validation Stages

### Stage 1: Syntax & Normalization (0.4 points)

Normalizes and validates phone format:
- Removes spaces, hyphens, parentheses, dots
- Accepts optional '+' prefix
- Checks for only digits (and optional +)
- Validates minimum length

**Rejects:**
- `invalid-phone` (non-numeric)
- `123` (too short)
- Empty strings

**Accepts:**
- `415-123-4567` → `4151234567`
- `(415) 123-4567` → `4151234567`
- `+1 415 123 4567` → `+14151234567`

### Stage 2: Length Check (0.3 points)

Validates phone number length:
- Default: 6-15 digits
- Configurable per validator
- Checks after normalization

**Rejects:**
- Numbers < 6 digits
- Numbers > 15 digits

### Stage 3: Country/Region Check (0.3 points)

Validates against country-specific rules:
- Supports 8 countries (US, UK, CA, AU, DE, FR, JP, IN)
- Checks area codes and prefixes
- Validates patterns

**Supported Countries:**
- **US:** +1, 10 digits, area code validation
- **UK:** +44, 10-13 digits, London/regional codes
- **CA:** +1, 10 digits (same as US)
- **AU:** +61, 9-12 digits, area codes
- **DE:** +49, 10-13 digits
- **FR:** +33, 9-12 digits
- **JP:** +81, 10-12 digits
- **IN:** +91, 10-12 digits

### Stage 4: VoIP Detection (Optional)

Detects known VoIP/toll-free numbers:
- US toll-free: 1800, 1888, 1877, 1866
- UK: 0800, 0808, 0844, 0845
- AU: 1300, 1800, 1900

**Can be:**
- Detected but allowed (default)
- Detected and rejected (if `reject_voip=True`)

### Stage 5: Library Verification (0.3 points, optional)

Uses `phonenumbers` library for validation:
- Validates number format
- Detects phone type (mobile, fixed line, VoIP)
- Requires `pip install phonenumbers`

## Confidence Scoring

### Score Calculation

```
Base: 0.0

+ 0.4 if syntax valid
+ 0.3 if length valid
+ 0.3 if country rules valid
+ 0.3 if library verification succeeds (optional)

= Final score (capped at 1.0)
```

### Thresholds

- **Valid phone:** confidence >= 0.6
- **High confidence:** >= 0.8 (safe for outreach)
- **Medium confidence:** 0.5-0.8 (verify before use)
- **Low confidence:** < 0.5 (likely invalid)

### Examples

```
415-123-4567
- Syntax: ✓ (+0.4)
- Length: ✓ (+0.3)
- Country: ✓ (+0.3)
- Library: ✓ (+0.3)
= 1.0 (High confidence)

123
- Syntax: ✓ (+0.4)
- Length: ✗ (0)
= 0.4 (Low confidence, rejected)

invalid-phone
- Syntax: ✗ (0)
= 0.0 (Invalid)
```

## Output Format

### Validation Result

```python
PhoneValidationResult(
    phone='415-123-4567',
    normalized_phone='4151234567',
    is_valid=True,
    confidence_score=0.95,
    reason=ValidationReason.VALID,
    phone_type=PhoneType.MOBILE,
    country_code='US',
    syntax_valid=True,
    length_valid=True,
    country_valid=True,
    library_verified=True,
    is_voip=False,
    validation_timestamp='2025-11-23T23:30:00.123456'
)
```

### CSV Export

```csv
phone,normalized_phone,is_valid,confidence_score,reason,phone_type,country_code,syntax_valid,length_valid,country_valid,library_verified,is_voip,validation_timestamp
415-123-4567,4151234567,True,0.95,valid,mobile,US,True,True,True,True,False,2025-11-23T23:30:00.123456
123,123,False,0.4,invalid_length,unknown,US,True,False,True,False,False,2025-11-23T23:30:01.234567
invalid-phone,invalid-phone,False,0.0,invalid_syntax,unknown,US,False,False,True,False,False,2025-11-23T23:30:02.345678
```

### Summary Statistics

```python
ValidationSummary(
    total_phones=10,
    valid_phones=7,
    invalid_phones=3,
    average_confidence=0.72,
    high_confidence_phones=['4151234567', '4159876543'],
    medium_confidence_phones=['4155551234'],
    low_confidence_phones=['123'],
    mobile_count=5,
    fixed_line_count=2,
    voip_count=0
)
```

## Configuration Options

### PhoneValidator Parameters

```python
PhoneValidator(
    default_country='US',              # Default country code
    country_whitelist={'US', 'CA'},    # Only allow these countries
    country_blacklist={'XX'},          # Never allow these countries
    min_length=6,                      # Minimum phone length
    max_length=15,                     # Maximum phone length
    enable_library_check=True,         # Use phonenumbers library
    enable_voip_check=True,            # Check for VoIP numbers
    reject_voip=False,                 # Reject VoIP numbers
    scraper_confidence=0.5             # Base confidence from scraper
)
```

### Factory Function

```python
create_validator(
    default_country='US',
    country_whitelist=['US', 'CA'],
    country_blacklist=['XX'],
    min_length=6,
    max_length=15,
    enable_library_check=True,
    enable_voip_check=True,
    reject_voip=False
)
```

## Logging

### Log Levels

- **DEBUG:** Detailed validation steps, rejected phones
- **INFO:** Valid phones, summaries, configuration
- **WARNING:** Validation errors, timeouts
- **ERROR:** Critical failures

### Example Logs

```
INFO - Valid phone: 4151234567 (confidence: 0.95, type: mobile) from https://example.com
DEBUG - Syntax invalid: invalid-phone from https://example.com
DEBUG - Invalid length: 123 (normalized: 123) from https://example.com
DEBUG - VoIP number rejected: 18005551234 from https://example.com
INFO - Validation Summary for https://example.com: Total=10, Valid=7, Invalid=3, AvgConfidence=0.72, Mobile=5, FixedLine=2, VoIP=0
```

### Thread-Safe Logging

All logging is protected by locks for safe multi-threaded operation:

```python
with _log_lock:
    phone_validator_logger.log(level, message)
```

## Advanced Usage

### Country Whitelist (Strict Mode)

```python
# Only accept phones from these countries
whitelist = ['US', 'CA', 'UK']
validator = create_validator(country_whitelist=whitelist)
```

### Country Blacklist

```python
# Never accept phones from these countries
blacklist = ['XX', 'YY']
validator = create_validator(country_blacklist=blacklist)
```

### VoIP Rejection

```python
# Reject toll-free and VoIP numbers
validator = create_validator(reject_voip=True)
```

### Custom Length Validation

```python
# Strict length validation
validator = create_validator(min_length=10, max_length=11)
```

### Mobile Phone Detection

```python
from phone_validator import PhoneType

pipeline = PhoneValidationPipeline(validator)
result = pipeline.process_scraper_result(phones, url)

# Get only mobile phones
mobile_phones = pipeline.get_mobile_phones(
    result['validation_results'],
    min_confidence=0.8
)
```

## Performance Considerations

### Speed

- **Syntax check:** < 1ms per phone
- **Length check:** < 1ms per phone
- **Country check:** < 1ms per phone
- **VoIP check:** < 1ms per phone
- **Library verification:** 5-20ms per phone (if enabled)

### Optimization Tips

1. **Disable library check** for large batches (faster)
2. **Use country whitelist** to skip validation for known countries
3. **Batch similar countries** to reuse validation rules
4. **Run in parallel** with ThreadPoolExecutor

### Example: Parallel Validation

```python
from concurrent.futures import ThreadPoolExecutor

validator = create_validator()

def validate_batch(phones, url):
    results, summary = validator.validate_phones(phones, url)
    return results

# Validate multiple websites in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(validate_batch, phones, url): url
        for url, phones in website_phones.items()
    }
    
    for future in futures:
        results = future.result()
```

## Troubleshooting

### Library Not Available

**Problem:** `phonenumbers` library not installed

**Solution:**
```bash
pip install phonenumbers
```

Or disable library check:
```python
validator = create_validator(enable_library_check=False)
```

### False Positives

**Problem:** Valid phones marked as invalid

**Solution:**
```python
# Lower confidence threshold
high_conf = [r for r in results if r.confidence_score >= 0.5]

# Or use country whitelist
validator = create_validator(country_whitelist=['US'])
```

### VoIP Numbers

**Problem:** Toll-free numbers being rejected

**Solution:**
```python
# Allow VoIP (default)
validator = create_validator(reject_voip=False)

# Or filter them separately
voip_phones = [r for r in results if r.is_voip]
```

## Integration Checklist

- [ ] Import PhoneValidator in scraper.py
- [ ] Initialize validator in WebScraper.__init__()
- [ ] Call validate_phones() after extraction
- [ ] Export validation results to CSV
- [ ] Test with sample phones
- [ ] Configure country whitelist/blacklist if needed
- [ ] Monitor logs for validation issues
- [ ] Adjust confidence thresholds as needed
- [ ] (Optional) Install phonenumbers for enhanced validation

## Examples

### Example 1: Basic Validation

```python
from phone_validator import create_validator

validator = create_validator()
phones = ['415-123-4567', '123', 'invalid']
results, summary = validator.validate_phones(phones, 'https://example.com')

for result in results:
    if result.is_valid:
        print(f"✓ {result.normalized_phone} ({result.confidence_score:.2f})")
    else:
        print(f"✗ {result.phone} ({result.reason.value})")
```

### Example 2: Country-Specific

```python
# UK validation
validator = create_validator(default_country='UK')
phones = ['+44 20 7946 0958', '020 7946 0958']
results, summary = validator.validate_phones(phones, 'https://example.co.uk')
```

### Example 3: Pipeline Integration

```python
from phone_validator import create_validator, PhoneValidationPipeline

validator = create_validator()
pipeline = PhoneValidationPipeline(validator)

result = pipeline.process_scraper_result(
    phones=['415-123-4567', '123'],
    website_url='https://example.com',
    country_hint='US'
)

validated = result['validated_phones']
```

### Example 4: Mobile Detection

```python
mobile_phones = pipeline.get_mobile_phones(
    result['validation_results'],
    min_confidence=0.8
)
```

### Example 5: Export to CSV

```python
import csv

results, summary = validator.validate_phones(phones, url)

with open('phone_validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Summary

The phone validator provides:
- ✅ Multi-stage validation (syntax, length, country, VoIP, library)
- ✅ Confidence scoring (0.0-1.0)
- ✅ Country-specific rules (8 countries)
- ✅ Phone type detection (mobile, fixed line, VoIP)
- ✅ Thread-safe logging
- ✅ CSV integration
- ✅ Extensible design
- ✅ High performance
- ✅ Easy integration

Perfect for ensuring high-quality phone data from web scraping!
