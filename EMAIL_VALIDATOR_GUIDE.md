# Email Validator Module Guide

Comprehensive email validation module for the web scraper with multi-stage validation and confidence scoring.

## Overview

The email validator provides:
- **Multi-stage validation** (syntax, MX records, disposable check, optional SMTP)
- **Confidence scoring** (0.0-1.0 per email)
- **Thread-safe logging** for parallel scraping
- **Seamless CSV integration** with existing scraper
- **Extensible design** for custom checks

## Installation

### Dependencies

```bash
pip install dnspython
```

The module uses:
- `dnspython` - MX record lookups
- `smtplib` - SMTP verification (built-in)
- `socket` - Network operations (built-in)
- `threading` - Thread-safe logging (built-in)

## Quick Start

### Basic Usage

```python
from email_validator import EmailValidator, create_validator

# Create validator with defaults
validator = create_validator()

# Validate emails from a website
emails = ['contact@example.com', 'test@mailinator.com', 'invalid@']
results, summary = validator.validate_emails(emails, 'https://example.com')

# Check results
for result in results:
    print(f"{result.email}: {result.confidence_score:.2f} - {result.reason.value}")

# Get summary
print(f"Valid: {summary.valid_emails}/{summary.total_emails}")
print(f"Average confidence: {summary.average_confidence}")
```

### With Configuration

```python
# Create validator with custom settings
validator = create_validator(
    enable_smtp=False,  # Disable SMTP (slower, rate-limited)
    domain_whitelist=['example.com', 'company.com'],  # Only these domains
    domain_blacklist=['spam.com'],  # Never these domains
    custom_disposable=['custom-temp.com']  # Additional temp domains
)

# Validate
results, summary = validator.validate_emails(emails, 'https://example.com')
```

## Integration with Scraper

### Step 1: Import in scraper.py

```python
from email_validator import EmailValidator, EmailValidationPipeline, create_validator
```

### Step 2: Initialize in WebScraper class

```python
class WebScraper:
    def __init__(self, ...):
        # ... existing code ...
        self.email_validator = create_validator(enable_smtp=False)
        self.validation_pipeline = EmailValidationPipeline(self.email_validator)
```

### Step 3: Validate emails after extraction

```python
def _extract_from_html(self, url: str, html: str):
    # ... existing extraction code ...
    emails, phones, leadership_count, pages_scanned, social_links = ...
    
    # NEW: Validate emails
    validation_result = self.validation_pipeline.process_scraper_result(
        emails=list(emails),
        website_url=url,
        scraper_confidence=self.current_confidence  # From scraper
    )
    
    # Use validated emails
    validated_emails = validation_result['validated_emails']
    emails = {e.email for e in validated_emails}
    
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
    validation_file = output_file.replace('.csv', '_validation.csv')
    all_validation_results = []
    for result in results:
        all_validation_results.extend(result.validation_results)
    
    if all_validation_results:
        with open(validation_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_validation_results[0].to_dict().keys())
            writer.writeheader()
            writer.writerows([r.to_dict() for r in all_validation_results])
```

## Validation Stages

### Stage 1: Syntax Check (0.4 points)

Validates email format:
- Contains exactly one `@`
- Valid local part (before @)
- Valid domain part (after @)
- No illegal characters
- Length <= 254 characters (RFC 5321)

**Rejects:**
- `invalid@` (no domain)
- `@example.com` (no local part)
- `user@.com` (invalid domain)
- `user name@example.com` (space)

### Stage 2: Disposable Domain Check (0.2 points)

Checks against known temporary email providers:
- mailinator.com
- 10minutemail.com
- tempmail.com
- guerrillamail.com
- And 15+ others

**Rejects:** Any email from disposable domains

### Stage 3: MX Record Check (0.4 points)

Verifies domain has valid mail exchange records:
- Performs DNS lookup for MX records
- Confirms domain can receive email
- Handles DNS timeouts gracefully

**Rejects:** Domains with no MX records

### Stage 4: SMTP Verification (0.2 points, optional)

Non-intrusive SMTP check:
- Connects to domain's mail server
- Sends RCPT TO command
- Checks if server accepts email

**Note:** Disabled by default (rate-limiting risk)

## Confidence Scoring

### Score Calculation

```
Base: 0.0

+ 0.4 if syntax valid
+ 0.2 if not disposable
+ 0.4 if MX records exist
+ 0.2 if SMTP verification succeeds (optional)

= Final score (capped at 1.0)
```

### Thresholds

- **Valid email:** confidence >= 0.6
- **High confidence:** >= 0.8 (safe for outreach)
- **Medium confidence:** 0.5-0.8 (verify before use)
- **Low confidence:** < 0.5 (likely invalid)

### Examples

```
contact@example.com
- Syntax: ✓ (+0.4)
- Not disposable: ✓ (+0.2)
- MX exists: ✓ (+0.4)
- SMTP: ✓ (+0.2)
= 1.0 (High confidence)

test@mailinator.com
- Syntax: ✓ (+0.4)
- Not disposable: ✗ (0)
= 0.4 (Low confidence, rejected)

invalid@
- Syntax: ✗ (0)
= 0.0 (Invalid)
```

## Output Format

### Validation Result

```python
EmailValidationResult(
    email='contact@example.com',
    is_valid=True,
    confidence_score=0.95,
    reason=ValidationReason.VALID,
    syntax_valid=True,
    mx_exists=True,
    is_disposable=False,
    smtp_verified=False,
    validation_timestamp='2025-11-23T23:30:00.123456'
)
```

### CSV Export

```csv
email,is_valid,confidence_score,reason,syntax_valid,mx_exists,is_disposable,smtp_verified,validation_timestamp
contact@example.com,True,0.95,valid,True,True,False,False,2025-11-23T23:30:00.123456
test@mailinator.com,False,0.4,disposable_domain,True,True,True,False,2025-11-23T23:30:01.234567
invalid@,False,0.0,invalid_syntax,False,False,False,False,2025-11-23T23:30:02.345678
```

### Summary Statistics

```python
ValidationSummary(
    total_emails=10,
    valid_emails=7,
    invalid_emails=3,
    average_confidence=0.72,
    high_confidence_emails=['contact@example.com', 'sales@company.com'],
    medium_confidence_emails=['info@example.org'],
    low_confidence_emails=['test@temp.com']
)
```

## Configuration Options

### EmailValidator Parameters

```python
EmailValidator(
    enable_smtp_check=False,           # Enable SMTP verification
    smtp_timeout=5,                    # SMTP timeout in seconds
    domain_whitelist={'example.com'},  # Only allow these domains
    domain_blacklist={'spam.com'},     # Never allow these domains
    custom_disposable_domains={...},   # Additional temp domains
    scraper_confidence=0.5             # Base confidence from scraper
)
```

### Factory Function

```python
create_validator(
    enable_smtp=False,
    domain_whitelist=['example.com'],
    domain_blacklist=['spam.com'],
    custom_disposable=['temp.com']
)
```

## Logging

### Log Levels

- **DEBUG:** Detailed validation steps, rejected emails
- **INFO:** Valid emails, summaries, configuration
- **WARNING:** Validation errors, timeouts
- **ERROR:** Critical failures

### Example Logs

```
INFO - Valid email: contact@example.com (confidence: 0.95) from https://example.com
DEBUG - Syntax invalid: invalid@ from https://example.com
DEBUG - Disposable domain: test@mailinator.com from https://example.com
DEBUG - No MX record: contact@invalid-domain.com from https://example.com
INFO - Validation Summary for https://example.com: Total=10, Valid=7, Invalid=3, AvgConfidence=0.72
```

### Thread-Safe Logging

All logging is protected by locks for safe multi-threaded operation:

```python
with _log_lock:
    email_validator_logger.log(level, message)
```

## Advanced Usage

### Custom Disposable Domains

```python
custom_temp = ['company-temp.com', 'internal-test.com']
validator = create_validator(custom_disposable=custom_temp)
```

### Domain Whitelist (Strict Mode)

```python
# Only accept emails from these domains
whitelist = ['example.com', 'company.com', 'partner.org']
validator = create_validator(domain_whitelist=whitelist)
```

### Domain Blacklist

```python
# Never accept emails from these domains
blacklist = ['spam.com', 'phishing.net']
validator = create_validator(domain_blacklist=blacklist)
```

### SMTP Verification (Advanced)

```python
# Enable SMTP for highest accuracy (slower)
validator = create_validator(enable_smtp=True)

# Validate with SMTP
results, summary = validator.validate_emails(emails, url)
# Results will include smtp_verified field
```

## Performance Considerations

### Speed

- **Syntax check:** < 1ms per email
- **Disposable check:** < 1ms per email
- **MX lookup:** 50-500ms per domain (cached by DNS)
- **SMTP check:** 1-5s per email (disabled by default)

### Optimization Tips

1. **Disable SMTP** for large batches (default)
2. **Use domain whitelist** to skip validation for known domains
3. **Batch similar domains** to reuse DNS cache
4. **Run in parallel** with ThreadPoolExecutor

### Example: Parallel Validation

```python
from concurrent.futures import ThreadPoolExecutor

validator = create_validator()

def validate_batch(emails, url):
    results, summary = validator.validate_emails(emails, url)
    return results

# Validate multiple websites in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(validate_batch, emails, url): url
        for url, emails in website_emails.items()
    }
    
    for future in futures:
        results = future.result()
```

## Troubleshooting

### DNS Lookup Failures

**Problem:** MX record checks timing out

**Solution:**
```python
# Increase timeout or disable MX check
validator = create_validator()
# DNS uses system timeout (usually 5s)
```

### SMTP Rate Limiting

**Problem:** SMTP verification failing on many emails

**Solution:**
```python
# Disable SMTP (default)
validator = create_validator(enable_smtp=False)
```

### False Positives

**Problem:** Valid emails marked as invalid

**Solution:**
```python
# Lower confidence threshold
high_conf = [r for r in results if r.confidence_score >= 0.5]

# Or use whitelist
validator = create_validator(domain_whitelist=['example.com'])
```

## Integration Checklist

- [ ] Install dnspython: `pip install dnspython`
- [ ] Import EmailValidator in scraper.py
- [ ] Initialize validator in WebScraper.__init__()
- [ ] Call validate_emails() after extraction
- [ ] Export validation results to CSV
- [ ] Test with sample emails
- [ ] Configure domain whitelist/blacklist if needed
- [ ] Monitor logs for validation issues
- [ ] Adjust confidence thresholds as needed

## Examples

### Example 1: Basic Validation

```python
from email_validator import create_validator

validator = create_validator()
emails = ['contact@example.com', 'test@mailinator.com']
results, summary = validator.validate_emails(emails, 'https://example.com')

for result in results:
    if result.is_valid:
        print(f"✓ {result.email} ({result.confidence_score:.2f})")
    else:
        print(f"✗ {result.email} ({result.reason.value})")
```

### Example 2: Scraper Integration

```python
# In scraper.py
from email_validator import create_validator, EmailValidationPipeline

class WebScraper:
    def __init__(self, ...):
        self.validator = create_validator()
        self.pipeline = EmailValidationPipeline(self.validator)
    
    def scrape_url(self, url):
        # ... existing code ...
        emails = self.extractor.extract_emails(html)
        
        # Validate emails
        validation = self.pipeline.process_scraper_result(
            emails=list(emails),
            website_url=url
        )
        
        # Use validated emails
        validated = validation['validated_emails']
        return validated
```

### Example 3: Export to CSV

```python
import csv
from email_validator import create_validator

validator = create_validator()
results, summary = validator.validate_emails(emails, url)

# Export to CSV
with open('email_validation.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
    writer.writeheader()
    writer.writerows([r.to_dict() for r in results])
```

## Summary

The email validator provides:
- ✅ Multi-stage validation (syntax, MX, disposable, SMTP)
- ✅ Confidence scoring (0.0-1.0)
- ✅ Thread-safe logging
- ✅ CSV integration
- ✅ Extensible design
- ✅ High performance
- ✅ Easy integration

Perfect for ensuring high-quality email data from web scraping!
