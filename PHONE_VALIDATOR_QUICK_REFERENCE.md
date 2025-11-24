# Phone Validator - Quick Reference Card

## Installation

```bash
# No external dependencies required for basic validation
# Optional: for enhanced validation
pip install phonenumbers
```

## Basic Usage

```python
from phone_validator import create_validator

# Create validator
validator = create_validator()

# Validate phones
results, summary = validator.validate_phones(
    phones=['415-123-4567', '123', 'invalid'],
    website_url='https://example.com'
)

# Check results
for result in results:
    print(f"{result.phone}: {result.confidence_score:.2f}")
```

## Scraper Integration

```python
# In scraper.py
from phone_validator import create_validator, PhoneValidationPipeline

class WebScraper:
    def __init__(self, ...):
        self.validator = create_validator()
        self.pipeline = PhoneValidationPipeline(self.validator)
    
    def _extract_from_html(self, url, html):
        phones = self.extractor.extract_phones(html)
        
        # Validate
        result = self.pipeline.process_scraper_result(
            phones=list(phones),
            website_url=url,
            country_hint='US'
        )
        
        # Use validated phones
        validated = result['validated_phones']
        return {p.normalized_phone for p in validated}
```

## Configuration

### Default (Recommended)
```python
validator = create_validator()
```

### US Only
```python
validator = create_validator(
    default_country='US',
    country_whitelist=['US', 'CA']
)
```

### Reject VoIP
```python
validator = create_validator(reject_voip=True)
```

### Multiple Countries
```python
validator = create_validator(
    country_whitelist=['US', 'UK', 'AU', 'DE']
)
```

### Strict Length
```python
validator = create_validator(
    min_length=10,
    max_length=11
)
```

### Disable Library (Faster)
```python
validator = create_validator(enable_library_check=False)
```

## Validation Stages

| Stage | Points | Check |
|-------|--------|-------|
| Syntax | 0.4 | Valid format, normalization |
| Length | 0.3 | 6-15 digits (configurable) |
| Country | 0.3 | Country-specific rules |
| VoIP | - | Detect toll-free/VoIP |
| Library | 0.3 | Optional phonenumbers check |

## Confidence Thresholds

- **Valid:** >= 0.6
- **High Confidence:** >= 0.8 (safe for outreach)
- **Medium Confidence:** 0.5-0.8 (verify before use)
- **Low Confidence:** < 0.5 (likely invalid)

## Output

### Per Phone
```python
PhoneValidationResult(
    phone='415-123-4567',
    normalized_phone='4151234567',
    is_valid=True,
    confidence_score=0.95,
    reason=ValidationReason.VALID,
    phone_type=PhoneType.MOBILE,
    country_code='US',
    is_voip=False
)
```

### Per Batch
```python
ValidationSummary(
    total_phones=10,
    valid_phones=8,
    invalid_phones=2,
    average_confidence=0.82,
    high_confidence_phones=['4151234567', ...],
    mobile_count=6,
    fixed_line_count=2,
    voip_count=0
)
```

## CSV Export

```python
import csv

results, summary = validator.validate_phones(phones, url)

with open('validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Pipeline Usage

```python
from phone_validator import PhoneValidationPipeline

pipeline = PhoneValidationPipeline(validator)

# Process scraper results
result = pipeline.process_scraper_result(
    phones=['415-123-4567', '123'],
    website_url='https://example.com',
    country_hint='US'
)

# Get validated phones
validated = result['validated_phones']

# Get rejected phones
rejected = result['rejected_phones']

# Get summary
summary = result['summary']

# Get best phones for outreach
best = pipeline.get_best_phones(
    result['validation_results'],
    min_confidence=0.8
)

# Get mobile phones
mobile = pipeline.get_mobile_phones(
    result['validation_results'],
    min_confidence=0.8
)
```

## Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logs will show:
# INFO - Valid phone: 4151234567 (confidence: 0.95, type: mobile) from https://example.com
# DEBUG - Invalid length: 123 (normalized: 123) from https://example.com
# INFO - Validation Summary for https://example.com: Total=10, Valid=8, Invalid=2, AvgConfidence=0.82, Mobile=6, FixedLine=2, VoIP=0
```

## Validation Reasons

| Reason | Meaning |
|--------|---------|
| `valid` | Phone passed all checks |
| `invalid_syntax` | Phone format is invalid |
| `invalid_length` | Phone has invalid length |
| `invalid_country` | Country not in whitelist |
| `disposable_voip` | VoIP number (rejected) |
| `unverified` | Library verification failed |
| `blacklisted` | Country is blacklisted |
| `unknown_error` | Other error |

## Phone Types

| Type | Meaning |
|------|---------|
| `mobile` | Mobile/cellular number |
| `fixed_line` | Landline number |
| `voip` | VoIP/toll-free number |
| `unknown` | Type not determined |

## Performance

| Operation | Time |
|-----------|------|
| Syntax check | < 1ms |
| Length check | < 1ms |
| Country check | < 1ms |
| VoIP check | < 1ms |
| Library check | 5-20ms |

## Common Tasks

### Get High-Confidence Phones
```python
high_conf = [r for r in results if r.confidence_score >= 0.8]
```

### Get Valid Phones Only
```python
valid = [r.normalized_phone for r in results if r.is_valid]
```

### Get Rejection Reasons
```python
for result in results:
    if not result.is_valid:
        print(f"{result.phone}: {result.reason.value}")
```

### Get Summary Statistics
```python
print(f"Valid: {summary.valid_phones}/{summary.total_phones}")
print(f"Average confidence: {summary.average_confidence:.2f}")
print(f"Mobile: {summary.mobile_count}")
```

### Batch Process Multiple Websites
```python
for website_url, phones in websites.items():
    result = pipeline.process_scraper_result(
        phones=phones,
        website_url=website_url,
        country_hint='US'
    )
    print(f"{website_url}: {result['summary'].valid_phones} valid")
```

## Supported Countries

| Code | Country | Format |
|------|---------|--------|
| US | United States | +1 (10 digits) |
| UK | United Kingdom | +44 (10-13 digits) |
| CA | Canada | +1 (10 digits) |
| AU | Australia | +61 (9-12 digits) |
| DE | Germany | +49 (10-13 digits) |
| FR | France | +33 (9-12 digits) |
| JP | Japan | +81 (10-12 digits) |
| IN | India | +91 (10-12 digits) |

## Integration Steps

1. **Copy:** phone_validator.py to project
2. **Import:** `from phone_validator import create_validator`
3. **Initialize:** `self.validator = create_validator()`
4. **Validate:** `results, summary = validator.validate_phones(phones, url)`
5. **Use:** `validated = [r for r in results if r.is_valid]`
6. **Export:** Save results to CSV

## Troubleshooting

### Library Not Available
- Install: `pip install phonenumbers`
- Or disable: `enable_library_check=False`

### VoIP Numbers Rejected
- Allow VoIP: `reject_voip=False` (default)
- Or filter: `[r for r in results if not r.is_voip]`

### False Positives
- Use country whitelist
- Lower confidence threshold
- Enable library check

### Performance Issues
- Disable library check
- Use country whitelist
- Run in parallel

## Files

| File | Purpose |
|------|---------|
| `phone_validator.py` | Main module |
| `PHONE_VALIDATOR_GUIDE.md` | Complete documentation |
| `phone_validator_example.py` | 8 runnable examples |
| `SCRAPER_PHONE_VALIDATION_INTEGRATION.md` | Integration guide |
| `PHONE_VALIDATOR_QUICK_REFERENCE.md` | This file |

## Examples

### Example 1: Basic
```python
validator = create_validator()
results, summary = validator.validate_phones(phones, url)
```

### Example 2: Country-Specific
```python
validator = create_validator(default_country='UK')
results, summary = validator.validate_phones(phones, url)
```

### Example 3: Pipeline
```python
pipeline = PhoneValidationPipeline(validator)
result = pipeline.process_scraper_result(phones, url)
```

### Example 4: Mobile Detection
```python
mobile = pipeline.get_mobile_phones(result['validation_results'])
```

### Example 5: Export
```python
with open('validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Key Features

✅ Multi-stage validation (syntax, length, country, VoIP, library)
✅ Confidence scoring (0.0-1.0)
✅ Country-specific rules (8 countries)
✅ Phone type detection (mobile, fixed line, VoIP)
✅ Thread-safe logging
✅ CSV export
✅ Domain whitelist/blacklist
✅ Batch processing
✅ Pipeline integration
✅ Minimal performance impact
✅ Comprehensive documentation

## Support

- **Documentation:** PHONE_VALIDATOR_GUIDE.md
- **Examples:** phone_validator_example.py
- **Integration:** SCRAPER_PHONE_VALIDATION_INTEGRATION.md
- **Source:** phone_validator.py

---

**Quick Start:** `python phone_validator_example.py`
