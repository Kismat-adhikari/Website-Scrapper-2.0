"""
Email Validator Integration Examples
Demonstrates how to use the email validator with the web scraper
"""

from email_validator import (
    EmailValidator,
    EmailValidationPipeline,
    create_validator,
    ValidationReason
)
import csv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# Example 1: Basic Email Validation
# ============================================================================

def example_basic_validation():
    """Basic email validation with default settings"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Email Validation")
    print("="*70)
    
    # Create validator
    validator = create_validator()
    
    # Sample emails
    emails = [
        'contact@example.com',
        'sales@company.org',
        'test@mailinator.com',  # Disposable
        'invalid@',  # Invalid syntax
        'noreply@example.com',
        'support@github.com'
    ]
    
    # Validate
    results, summary = validator.validate_emails(emails, 'https://example.com')
    
    # Display results
    print(f"\nValidation Results:")
    print(f"{'Email':<30} {'Valid':<8} {'Confidence':<12} {'Reason':<20}")
    print("-" * 70)
    
    for result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"{result.email:<30} {status:<8} {result.confidence_score:<12.2f} {result.reason.value:<20}")
    
    # Display summary
    print(f"\nSummary:")
    print(f"  Total emails: {summary.total_emails}")
    print(f"  Valid: {summary.valid_emails}")
    print(f"  Invalid: {summary.invalid_emails}")
    print(f"  Average confidence: {summary.average_confidence:.2f}")
    print(f"  High confidence (≥0.8): {len(summary.high_confidence_emails)}")
    print(f"  Medium confidence (0.5-0.8): {len(summary.medium_confidence_emails)}")
    print(f"  Low confidence (<0.5): {len(summary.low_confidence_emails)}")


# ============================================================================
# Example 2: Validation with Domain Whitelist
# ============================================================================

def example_domain_whitelist():
    """Validate emails with domain whitelist (strict mode)"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Domain Whitelist (Strict Mode)")
    print("="*70)
    
    # Create validator with whitelist
    validator = create_validator(
        domain_whitelist=['example.com', 'company.org', 'github.com']
    )
    
    emails = [
        'contact@example.com',      # Allowed
        'sales@company.org',        # Allowed
        'support@github.com',       # Allowed
        'info@unknown.com',         # Not in whitelist
        'test@mailinator.com'       # Not in whitelist
    ]
    
    results, summary = validator.validate_emails(emails, 'https://example.com')
    
    print(f"\nWhitelist: example.com, company.org, github.com")
    print(f"\nResults:")
    for result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {result.email:<30} {result.reason.value}")
    
    print(f"\nValid emails: {summary.valid_emails}/{summary.total_emails}")


# ============================================================================
# Example 3: Validation with Domain Blacklist
# ============================================================================

def example_domain_blacklist():
    """Validate emails with domain blacklist"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Domain Blacklist")
    print("="*70)
    
    # Create validator with blacklist
    validator = create_validator(
        domain_blacklist=['spam.com', 'phishing.net', 'mailinator.com']
    )
    
    emails = [
        'contact@example.com',      # Allowed
        'admin@spam.com',           # Blacklisted
        'user@phishing.net',        # Blacklisted
        'test@mailinator.com'       # Blacklisted (also disposable)
    ]
    
    results, summary = validator.validate_emails(emails, 'https://example.com')
    
    print(f"\nBlacklist: spam.com, phishing.net, mailinator.com")
    print(f"\nResults:")
    for result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {result.email:<30} {result.reason.value}")


# ============================================================================
# Example 4: Pipeline Integration with Scraper
# ============================================================================

def example_pipeline_integration():
    """Demonstrate pipeline integration with scraper results"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Pipeline Integration with Scraper")
    print("="*70)
    
    # Create validator and pipeline
    validator = create_validator()
    pipeline = EmailValidationPipeline(validator)
    
    # Simulate scraper results
    scraper_emails = [
        'contact@example.com',
        'sales@example.com',
        'test@mailinator.com',
        'invalid@',
        'support@example.com'
    ]
    
    # Process through pipeline
    result = pipeline.process_scraper_result(
        emails=scraper_emails,
        website_url='https://example.com',
        scraper_confidence=0.75
    )
    
    print(f"\nScraper Results:")
    print(f"  Website: {result['website_url']}")
    print(f"  Scraper confidence: {result['scraper_confidence']}")
    print(f"  Emails extracted: {len(scraper_emails)}")
    
    print(f"\nValidation Results:")
    print(f"  Valid emails: {len(result['validated_emails'])}")
    print(f"  Rejected emails: {len(result['rejected_emails'])}")
    
    print(f"\nValidated Emails:")
    for email_result in result['validated_emails']:
        print(f"  ✓ {email_result.email} (confidence: {email_result.confidence_score:.2f})")
    
    print(f"\nRejected Emails:")
    for email_result in result['rejected_emails']:
        print(f"  ✗ {email_result.email} ({email_result.reason.value})")
    
    # Get best emails for outreach
    best_emails = pipeline.get_best_emails(
        result['validation_results'],
        min_confidence=0.8
    )
    print(f"\nBest emails for outreach (confidence ≥ 0.8):")
    for email in best_emails:
        print(f"  • {email}")


# ============================================================================
# Example 5: Export to CSV
# ============================================================================

def example_csv_export():
    """Export validation results to CSV"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Export to CSV")
    print("="*70)
    
    validator = create_validator()
    
    emails = [
        'contact@example.com',
        'sales@company.org',
        'test@mailinator.com',
        'invalid@',
        'support@github.com'
    ]
    
    results, summary = validator.validate_emails(emails, 'https://example.com')
    
    # Export to CSV
    csv_file = 'email_validation_example.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
        writer.writeheader()
        writer.writerows([r.to_dict() for r in results])
    
    print(f"\nExported {len(results)} validation results to {csv_file}")
    print(f"\nCSV Preview:")
    print(f"{'Email':<30} {'Valid':<8} {'Confidence':<12} {'Reason':<20}")
    print("-" * 70)
    
    for result in results:
        status = "Yes" if result.is_valid else "No"
        print(f"{result.email:<30} {status:<8} {result.confidence_score:<12.2f} {result.reason.value:<20}")


# ============================================================================
# Example 6: Confidence Score Analysis
# ============================================================================

def example_confidence_analysis():
    """Analyze confidence scores across different email types"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Confidence Score Analysis")
    print("="*70)
    
    validator = create_validator()
    
    test_cases = [
        ('contact@example.com', 'Valid corporate email'),
        ('test@mailinator.com', 'Disposable email'),
        ('invalid@', 'Invalid syntax'),
        ('user@nonexistent-domain-xyz.com', 'Non-existent domain'),
        ('support@github.com', 'Real company email'),
        ('noreply@example.com', 'No-reply email'),
    ]
    
    print(f"\n{'Email':<35} {'Type':<30} {'Confidence':<12} {'Valid':<8}")
    print("-" * 85)
    
    for email, email_type in test_cases:
        result = validator.validate_email(email, 'https://example.com')
        status = "Yes" if result.is_valid else "No"
        print(f"{email:<35} {email_type:<30} {result.confidence_score:<12.2f} {status:<8}")


# ============================================================================
# Example 7: Batch Processing Multiple Websites
# ============================================================================

def example_batch_processing():
    """Process emails from multiple websites"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Batch Processing Multiple Websites")
    print("="*70)
    
    validator = create_validator()
    pipeline = EmailValidationPipeline(validator)
    
    # Simulate scraper results from multiple websites
    websites = {
        'https://example.com': [
            'contact@example.com',
            'sales@example.com',
            'test@mailinator.com'
        ],
        'https://company.org': [
            'info@company.org',
            'support@company.org',
            'invalid@'
        ],
        'https://github.com': [
            'contact@github.com',
            'support@github.com'
        ]
    }
    
    # Process each website
    all_results = []
    for website_url, emails in websites.items():
        result = pipeline.process_scraper_result(
            emails=emails,
            website_url=website_url
        )
        all_results.append(result)
        
        summary = result['summary']
        print(f"\n{website_url}")
        print(f"  Total: {summary.total_emails} | Valid: {summary.valid_emails} | "
              f"Invalid: {summary.invalid_emails} | Avg Confidence: {summary.average_confidence:.2f}")
    
    # Overall statistics
    total_emails = sum(len(emails) for emails in websites.values())
    total_valid = sum(r['summary'].valid_emails for r in all_results)
    avg_confidence = sum(r['summary'].average_confidence for r in all_results) / len(all_results)
    
    print(f"\n{'='*70}")
    print(f"Overall Statistics:")
    print(f"  Total emails: {total_emails}")
    print(f"  Valid emails: {total_valid}")
    print(f"  Validation rate: {(total_valid/total_emails*100):.1f}%")
    print(f"  Average confidence: {avg_confidence:.2f}")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("EMAIL VALIDATOR - INTEGRATION EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_basic_validation()
    example_domain_whitelist()
    example_domain_blacklist()
    example_pipeline_integration()
    example_csv_export()
    example_confidence_analysis()
    example_batch_processing()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
