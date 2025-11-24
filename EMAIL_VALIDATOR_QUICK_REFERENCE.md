# Email Validator - Quick Reference Card

## Installation

```bash
pip install dnspython
```

## Basic Usage

```python
from email_validator import create_validator

# Create validator
validator = create_validator()

# Validate emails
results, summary = validator.validate_emails(
    emails=['contact@example.com', 'test@mailinator.com'],
    website_url='https://example.com'
)

# Check results
for result in results:
    print(f"{result.email}: {result.confidence_score:.2f}")
```

## Scraper Integration

```python
# In scraper.py
from email_validator import create_validator, EmailValidationPipeline

class WebScraper:
    def __init__(self, ...):
        self.validator = create_validator()
        self.pipeline = EmailValidationPipeline(self.validator)
    
    def _extract_from_html(self, url, html):
        emails = self.extractor.extract_emails(html)
        
        # Validate
        result = self.pipeline.process_scraper_result(
            emails=list(emails),
            website_url=url
        )
        
        # Use validated emails
        validated = result['validated_emails']
        return {e.email for e in validated}
```

## Configuration

### Default (Recommended)
```python
validator = create_validator()
```

### With SMTP (Slower, More Accurate)
```python
validator = create_validator(enable_smtp=True)
```

### Domain Whitelist (Strict)
```python
validator = create_validator(
    domain_whitelist=['example.com', 'company.org']
)
```

### Domain Blacklist
```python
validator = create_validator(
    domain_blacklist=['spam.com', 'phishing.net']
)
```

### Custom Disposable Domains
```python
validator = create_validator(
    custom_disposable=['temp-company.com']
)
```

## Validation Stages

| Stage | Points | Check |
|-------|--------|-------|
| Syntax | 0.4 | Valid email format |
| Disposable | 0.2 | Not temporary email |
| MX Record | 0.4 | Domain has MX records |
| SMTP | 0.2 | Optional, disabled by default |

## Confidence Thresholds

- **Valid:** >= 0.6
- **High Confidence:** >= 0.8 (safe for outreach)
- **Medium Confidence:** 0.5-0.8 (verify before use)
- **Low Confidence:** < 0.5 (likely invalid)

## Output

### Per Email
```python
EmailValidationResult(
    email='contact@example.com',
    is_valid=True,
    confidence_score=0.95,
    reason=ValidationReason.VALID,
    syntax_valid=True,
    mx_exists=True,
    is_disposable=False,
    smtp_verified=False
)
```

### Per Batch
```python
ValidationSummary(
    total_emails=10,
    valid_emails=8,
    invalid_emails=2,
    average_confidence=0.82,
    high_confidence_emails=['contact@example.com', ...],
    medium_confidence_emails=['info@example.org'],
    low_confidence_emails=['test@temp.com']
)
```

## CSV Export

```python
import csv

results, summary = validator.validate_emails(emails, url)

with open('validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Pipeline Usage

```python
from email_validator import EmailValidationPipeline

pipeline = EmailValidationPipeline(validator)

# Process scraper results
result = pipeline.process_scraper_result(
    emails=['contact@example.com', 'test@mailinator.com'],
    website_url='https://example.com',
    scraper_confidence=0.75
)

# Get validated emails
validated = result['validated_emails']

# Get rejected emails
rejected = result['rejected_emails']

# Get summary
summary = result['summary']

# Get best emails for outreach
best = pipeline.get_best_emails(
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
# INFO - Valid email: contact@example.com (confidence: 0.95) from https://example.com
# DEBUG - Disposable domain: test@mailinator.com from https://example.com
# INFO - Validation Summary for https://example.com: Total=10, Valid=7, Invalid=3, AvgConfidence=0.72
```

## Validation Reasons

| Reason | Meaning |
|--------|---------|
| `valid` | Email passed all checks |
| `invalid_syntax` | Email format is invalid |
| `no_mx_record` | Domain has no MX records |
| `disposable_domain` | Known temporary email |
| `smtp_failed` | SMTP verification failed |
| `blacklisted` | Domain is blacklisted |
| `unknown_error` | Other error |

## Performance

| Operation | Time |
|-----------|------|
| Syntax check | < 1ms |
| Disposable check | < 1ms |
| MX lookup | 50-500ms (cached) |
| SMTP check | 1-5s (disabled by default) |

## Common Tasks

### Get High-Confidence Emails
```python
high_conf = [r for r in results if r.confidence_score >= 0.8]
```

### Get Valid Emails Only
```python
valid = [r.email for r in results if r.is_valid]
```

### Get Rejection Reasons
```python
for result in results:
    if not result.is_valid:
        print(f"{result.email}: {result.reason.value}")
```

### Get Summary Statistics
```python
print(f"Valid: {summary.valid_emails}/{summary.total_emails}")
print(f"Average confidence: {summary.average_confidence:.2f}")
print(f"High confidence: {len(summary.high_confidence_emails)}")
```

### Batch Process Multiple Websites
```python
for website_url, emails in websites.items():
    result = pipeline.process_scraper_result(
        emails=emails,
        website_url=website_url
    )
    print(f"{website_url}: {result['summary'].valid_emails} valid")
```

## Integration Steps

1. **Install:** `pip install dnspython`
2. **Import:** `from email_validator import create_validator`
3. **Initialize:** `self.validator = create_validator()`
4. **Validate:** `results, summary = validator.validate_emails(emails, url)`
5. **Use:** `validated = [r for r in results if r.is_valid]`
6. **Export:** Save results to CSV

## Troubleshooting

### DNS Lookup Failures
- Normal for invalid domains
- Validator handles gracefully
- Check domain with: `nslookup -type=MX example.com`

### SMTP Rate Limiting
- Keep SMTP disabled (default)
- Not necessary for most use cases
- Use domain whitelist instead

### False Positives
- Use domain whitelist for known domains
- Lower confidence threshold
- Check MX records manually

### Performance Issues
- Disable SMTP (already default)
- Use domain whitelist
- Run in parallel with ThreadPoolExecutor

## Files

| File | Purpose |
|------|---------|
| `email_validator.py` | Main module |
| `EMAIL_VALIDATOR_GUIDE.md` | Complete documentation |
| `email_validator_example.py` | 7 runnable examples |
| `SCRAPER_EMAIL_VALIDATION_INTEGRATION.md` | Integration guide |
| `EMAIL_VALIDATOR_SUMMARY.md` | Feature summary |
| `EMAIL_VALIDATOR_QUICK_REFERENCE.md` | This file |

## Examples

### Example 1: Basic
```python
validator = create_validator()
results, summary = validator.validate_emails(emails, url)
```

### Example 2: With Whitelist
```python
validator = create_validator(domain_whitelist=['example.com'])
results, summary = validator.validate_emails(emails, url)
```

### Example 3: Pipeline
```python
pipeline = EmailValidationPipeline(validator)
result = pipeline.process_scraper_result(emails, url)
```

### Example 4: Export
```python
with open('validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Key Features

✅ Multi-stage validation (syntax, MX, disposable, SMTP)
✅ Confidence scoring (0.0-1.0)
✅ Thread-safe logging
✅ CSV export
✅ Domain whitelist/blacklist
✅ Custom disposable domains
✅ Batch processing
✅ Pipeline integration
✅ Minimal performance impact
✅ Comprehensive documentation

## Support

- **Documentation:** EMAIL_VALIDATOR_GUIDE.md
- **Examples:** email_validator_example.py
- **Integration:** SCRAPER_EMAIL_VALIDATION_INTEGRATION.md
- **Source:** email_validator.py

---

**Quick Start:** `pip install dnspython && python email_validator_example.py`
