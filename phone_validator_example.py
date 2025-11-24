"""
Phone Validator Integration Examples
Demonstrates how to use the phone validator with the web scraper
"""

from phone_validator import (
    PhoneValidator,
    PhoneValidationPipeline,
    create_validator,
    PhoneType,
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
# Example 1: Basic Phone Validation
# ============================================================================

def example_basic_validation():
    """Basic phone validation with default settings"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Phone Validation")
    print("="*70)
    
    # Create validator
    validator = create_validator()
    
    # Sample phone numbers
    phones = [
        '415-123-4567',
        '(415) 123-4567',
        '+1 415 123 4567',
        '415123456',  # Too short
        '123',  # Too short
        '555-1234567890123',  # Too long
        'invalid-phone',
        '+1-415-123-4567'
    ]
    
    # Validate
    results, summary = validator.validate_phones(phones, 'https://example.com')
    
    # Display results
    print(f"\nValidation Results:")
    print(f"{'Original':<25} {'Normalized':<20} {'Valid':<8} {'Confidence':<12} {'Reason':<20}")
    print("-" * 85)
    
    for result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"{result.phone:<25} {result.normalized_phone:<20} {status:<8} "
              f"{result.confidence_score:<12.2f} {result.reason.value:<20}")
    
    # Display summary
    print(f"\nSummary:")
    print(f"  Total phones: {summary.total_phones}")
    print(f"  Valid: {summary.valid_phones}")
    print(f"  Invalid: {summary.invalid_phones}")
    print(f"  Average confidence: {summary.average_confidence:.2f}")
    print(f"  Mobile: {summary.mobile_count}")
    print(f"  Fixed line: {summary.fixed_line_count}")
    print(f"  VoIP: {summary.voip_count}")


# ============================================================================
# Example 2: Country-Specific Validation
# ============================================================================

def example_country_validation():
    """Validate phones with country-specific rules"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Country-Specific Validation")
    print("="*70)
    
    # Test different countries
    test_cases = [
        ('US', ['415-123-4567', '+1-415-123-4567', '(415) 123-4567']),
        ('UK', ['+44 20 7946 0958', '020 7946 0958', '+442079460958']),
        ('AU', ['+61 2 9999 9999', '02 9999 9999', '+61299999999']),
        ('DE', ['+49 30 12345678', '030 12345678', '+493012345678']),
    ]
    
    for country, phones in test_cases:
        validator = create_validator(default_country=country)
        results, summary = validator.validate_phones(phones, f'https://example.{country.lower()}')
        
        print(f"\n{country} Validation:")
        for result in results:
            status = "✓" if result.is_valid else "✗"
            print(f"  {status} {result.phone:<25} → {result.normalized_phone:<20} "
                  f"(confidence: {result.confidence_score:.2f})")


# ============================================================================
# Example 3: VoIP Detection and Rejection
# ============================================================================

def example_voip_detection():
    """Detect and optionally reject VoIP numbers"""
    print("\n" + "="*70)
    print("EXAMPLE 3: VoIP Detection and Rejection")
    print("="*70)
    
    # Sample phones including toll-free (VoIP)
    phones = [
        '415-123-4567',  # Regular
        '1-800-555-1234',  # Toll-free (VoIP)
        '1-888-123-4567',  # Toll-free (VoIP)
        '+1-415-987-6543',  # Regular
    ]
    
    # Test 1: Allow VoIP
    print("\nTest 1: Allow VoIP Numbers")
    validator = create_validator(reject_voip=False)
    results, summary = validator.validate_phones(phones, 'https://example.com')
    
    for result in results:
        voip_label = " (VoIP)" if result.is_voip else ""
        print(f"  {result.normalized_phone:<20} Valid: {result.is_valid}{voip_label}")
    
    # Test 2: Reject VoIP
    print("\nTest 2: Reject VoIP Numbers")
    validator = create_validator(reject_voip=True)
    results, summary = validator.validate_phones(phones, 'https://example.com')
    
    for result in results:
        voip_label = " (VoIP)" if result.is_voip else ""
        print(f"  {result.normalized_phone:<20} Valid: {result.is_valid}{voip_label}")


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
    pipeline = PhoneValidationPipeline(validator)
    
    # Simulate scraper results
    scraper_phones = [
        '415-123-4567',
        '(415) 123-4567',
        '123',  # Too short
        '+1-415-987-6543',
        'invalid'
    ]
    
    # Process through pipeline
    result = pipeline.process_scraper_result(
        phones=scraper_phones,
        website_url='https://example.com',
        country_hint='US',
        scraper_confidence=0.75
    )
    
    print(f"\nScraper Results:")
    print(f"  Website: {result['website_url']}")
    print(f"  Country: {result['country_hint']}")
    print(f"  Scraper confidence: {result['scraper_confidence']}")
    print(f"  Phones extracted: {len(scraper_phones)}")
    
    print(f"\nValidation Results:")
    print(f"  Valid phones: {len(result['validated_phones'])}")
    print(f"  Rejected phones: {len(result['rejected_phones'])}")
    
    print(f"\nValidated Phones:")
    for phone_result in result['validated_phones']:
        print(f"  ✓ {phone_result.normalized_phone} (confidence: {phone_result.confidence_score:.2f})")
    
    print(f"\nRejected Phones:")
    for phone_result in result['rejected_phones']:
        print(f"  ✗ {phone_result.phone} ({phone_result.reason.value})")
    
    # Get best phones for outreach
    best_phones = pipeline.get_best_phones(
        result['validation_results'],
        min_confidence=0.8
    )
    print(f"\nBest phones for outreach (confidence ≥ 0.8):")
    for phone in best_phones:
        print(f"  • {phone}")


# ============================================================================
# Example 5: Mobile Phone Detection
# ============================================================================

def example_mobile_detection():
    """Detect and extract mobile phone numbers"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Mobile Phone Detection")
    print("="*70)
    
    validator = create_validator(enable_library_check=True)
    pipeline = PhoneValidationPipeline(validator)
    
    phones = [
        '415-123-4567',
        '(415) 123-4567',
        '+1-415-987-6543',
        '1-800-555-1234',  # Toll-free
    ]
    
    result = pipeline.process_scraper_result(
        phones=phones,
        website_url='https://example.com',
        country_hint='US'
    )
    
    print(f"\nPhone Type Analysis:")
    for phone_result in result['validation_results']:
        if phone_result.is_valid:
            print(f"  {phone_result.normalized_phone:<20} Type: {phone_result.phone_type.value}")
    
    # Get mobile phones
    mobile_phones = pipeline.get_mobile_phones(
        result['validation_results'],
        min_confidence=0.7
    )
    
    print(f"\nMobile Phones (confidence ≥ 0.7):")
    for phone in mobile_phones:
        print(f"  • {phone}")


# ============================================================================
# Example 6: Export to CSV
# ============================================================================

def example_csv_export():
    """Export validation results to CSV"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Export to CSV")
    print("="*70)
    
    validator = create_validator()
    
    phones = [
        '415-123-4567',
        '(415) 123-4567',
        '123',
        '+1-415-987-6543',
        'invalid'
    ]
    
    results, summary = validator.validate_phones(phones, 'https://example.com')
    
    # Export to CSV
    csv_file = 'phone_validation_example.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
        writer.writeheader()
        writer.writerows([r.to_dict() for r in results])
    
    print(f"\nExported {len(results)} validation results to {csv_file}")
    print(f"\nCSV Preview:")
    print(f"{'Phone':<20} {'Normalized':<20} {'Valid':<8} {'Confidence':<12} {'Type':<15}")
    print("-" * 75)
    
    for result in results:
        status = "Yes" if result.is_valid else "No"
        print(f"{result.phone:<20} {result.normalized_phone:<20} {status:<8} "
              f"{result.confidence_score:<12.2f} {result.phone_type.value:<15}")


# ============================================================================
# Example 7: Confidence Score Analysis
# ============================================================================

def example_confidence_analysis():
    """Analyze confidence scores across different phone types"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Confidence Score Analysis")
    print("="*70)
    
    validator = create_validator()
    
    test_cases = [
        ('415-123-4567', 'Valid US number'),
        ('123', 'Too short'),
        ('invalid-phone', 'Invalid format'),
        ('+1-415-987-6543', 'Valid with country code'),
        ('1-800-555-1234', 'Toll-free (VoIP)'),
    ]
    
    print(f"\n{'Phone':<25} {'Type':<30} {'Confidence':<12} {'Valid':<8}")
    print("-" * 75)
    
    for phone, phone_type in test_cases:
        result = validator.validate_phone(phone, 'https://example.com')
        status = "Yes" if result.is_valid else "No"
        print(f"{phone:<25} {phone_type:<30} {result.confidence_score:<12.2f} {status:<8}")


# ============================================================================
# Example 8: Batch Processing Multiple Websites
# ============================================================================

def example_batch_processing():
    """Process phones from multiple websites"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Batch Processing Multiple Websites")
    print("="*70)
    
    validator = create_validator()
    pipeline = PhoneValidationPipeline(validator)
    
    # Simulate scraper results from multiple websites
    websites = {
        'https://example.com': [
            '415-123-4567',
            '(415) 123-4567',
            '123'
        ],
        'https://company.org': [
            '+1-415-987-6543',
            '1-800-555-1234',
            'invalid'
        ],
        'https://business.net': [
            '415-111-2222',
            '415-333-4444'
        ]
    }
    
    # Process each website
    all_results = []
    for website_url, phones in websites.items():
        result = pipeline.process_scraper_result(
            phones=phones,
            website_url=website_url,
            country_hint='US'
        )
        all_results.append(result)
        
        summary = result['summary']
        print(f"\n{website_url}")
        print(f"  Total: {summary.total_phones} | Valid: {summary.valid_phones} | "
              f"Invalid: {summary.invalid_phones} | Avg Confidence: {summary.average_confidence:.2f}")
    
    # Overall statistics
    total_phones = sum(len(phones) for phones in websites.values())
    total_valid = sum(r['summary'].valid_phones for r in all_results)
    avg_confidence = sum(r['summary'].average_confidence for r in all_results) / len(all_results)
    
    print(f"\n{'='*70}")
    print(f"Overall Statistics:")
    print(f"  Total phones: {total_phones}")
    print(f"  Valid phones: {total_valid}")
    print(f"  Validation rate: {(total_valid/total_phones*100):.1f}%")
    print(f"  Average confidence: {avg_confidence:.2f}")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("PHONE VALIDATOR - INTEGRATION EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_basic_validation()
    example_country_validation()
    example_voip_detection()
    example_pipeline_integration()
    example_mobile_detection()
    example_csv_export()
    example_confidence_analysis()
    example_batch_processing()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
