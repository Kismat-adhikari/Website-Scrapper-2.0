"""
Test the unified phone cleaning system
"""

from phone_cleaner import (
    PhoneCleaningPipeline, PhoneNumber, SourceType,
    create_phone_cleaner
)

# Create test phone numbers with different sources
test_numbers = [
    # SHOULD KEEP - High confidence
    PhoneNumber(
        raw="(503) 575-2485",
        normalized="5035752485",
        canonical="+15035752485",
        source_type=SourceType.TEL_LINK,
        source_location='<a href="tel:+15035752485">',
        context_before="Contact us at",
        context_after="for more information",
        page_url="https://example.com/contact"
    ),
    
    PhoneNumber(
        raw="888-246-2598",
        normalized="8882462598",
        canonical="+18882462598",
        source_type=SourceType.SCHEMA_ORG,
        source_location='<script type="application/ld+json">',
        context_before='"telephone": "',
        context_after='", "address"',
        page_url="https://example.com/"
    ),
    
    PhoneNumber(
        raw="214-555-1234",
        normalized="2145551234",
        canonical="+12145551234",
        source_type=SourceType.FOOTER,
        source_location='<footer class="site-footer">',
        context_before="Call us: ",
        context_after=" | Email:",
        page_url="https://example.com/"
    ),
    
    # SHOULD REMOVE - Blacklisted
    PhoneNumber(
        raw="214-748-3647",
        normalized="2147483647",
        canonical="+12147483647",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<div class="demo">',
        context_before="Demo store: ",
        context_after="",
        page_url="https://example.com/"
    ),
    
    # SHOULD REMOVE - From script
    PhoneNumber(
        raw="800-123-4567",
        normalized="8001234567",
        canonical="+18001234567",
        source_type=SourceType.SCRIPT,
        source_location='<script src="bundle.js">',
        context_before="var phone = '",
        context_after="';",
        page_url="https://example.com/"
    ),
    
    # SHOULD REMOVE - Toll-free not in high-confidence location
    PhoneNumber(
        raw="888-999-0000",
        normalized="8889990000",
        canonical="+18889990000",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<div class="content">',
        context_before="",
        context_after="",
        page_url="https://example.com/"
    ),
    
    # SHOULD REMOVE - Invalid pattern (all same digit)
    PhoneNumber(
        raw="111-111-1111",
        normalized="1111111111",
        canonical="+11111111111",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<p>',
        context_before="",
        context_after="",
        page_url="https://example.com/"
    ),
    
    # SHOULD REMOVE - Duplicate (lower confidence)
    PhoneNumber(
        raw="503-575-2485",
        normalized="5035752485",
        canonical="+15035752485",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<p>',
        context_before="",
        context_after="",
        page_url="https://example.com/"
    ),
]

print("=" * 70)
print("PHONE CLEANING SYSTEM TEST")
print("=" * 70)

# Test Fast Mode
print("\n1. FAST MODE (60ms target)")
print("-" * 70)

cleaner_fast = create_phone_cleaner(fast_mode=True)
result_fast = cleaner_fast.clean(test_numbers, business_region='US')

print(f"\nKept {len(result_fast.kept_numbers)} numbers:")
for num in result_fast.kept_numbers:
    print(f"  ✅ {num.raw} (from {num.source_type.value}, confidence: {num.confidence:.2f})")

print(f"\nRemoved {len(result_fast.removed_numbers)} numbers:")
for num, reason in result_fast.removed_numbers:
    print(f"  ❌ {num} - {reason}")

print(f"\nStatistics:")
for key, value in result_fast.stats.items():
    print(f"  {key}: {value}")

# Test Accuracy Mode
print("\n" + "=" * 70)
print("2. ACCURACY MODE (130ms target)")
print("-" * 70)

# Add some numbers with context for accuracy mode testing
test_numbers_accuracy = test_numbers + [
    PhoneNumber(
        raw="555-123-4567",
        normalized="5551234567",
        canonical="+15551234567",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<div>',
        context_before="This is a shopify demo number: ",
        context_after=" for testing",
        page_url="https://example.com/"
    ),
]

cleaner_accuracy = create_phone_cleaner(fast_mode=False)
result_accuracy = cleaner_accuracy.clean(test_numbers_accuracy, business_region='US')

print(f"\nKept {len(result_accuracy.kept_numbers)} numbers:")
for num in result_accuracy.kept_numbers:
    print(f"  ✅ {num.raw} (from {num.source_type.value}, confidence: {num.confidence:.2f})")

print(f"\nRemoved {len(result_accuracy.removed_numbers)} numbers:")
for num, reason in result_accuracy.removed_numbers:
    print(f"  ❌ {num} - {reason}")

print(f"\nStatistics:")
for key, value in result_accuracy.stats.items():
    print(f"  {key}: {value}")

# Test region filtering
print("\n" + "=" * 70)
print("3. REGION FILTERING TEST (Non-US Business)")
print("-" * 70)

test_numbers_uk = [
    PhoneNumber(
        raw="+1-503-575-2485",
        normalized="15035752485",
        canonical="+15035752485",
        source_type=SourceType.VISIBLE_HTML,
        source_location='<p>',
        context_before="",
        context_after="",
        page_url="https://example.co.uk/"
    ),
    PhoneNumber(
        raw="+1-503-575-2485",
        normalized="15035752485",
        canonical="+15035752485",
        source_type=SourceType.TEL_LINK,
        source_location='<a href="tel:+15035752485">',
        context_before="US Office: ",
        context_after="",
        page_url="https://example.co.uk/contact"
    ),
]

cleaner_uk = create_phone_cleaner(fast_mode=False)
result_uk = cleaner_uk.clean(test_numbers_uk, business_region='UK')

print(f"\nKept {len(result_uk.kept_numbers)} numbers:")
for num in result_uk.kept_numbers:
    print(f"  ✅ {num.raw} (from {num.source_type.value})")

print(f"\nRemoved {len(result_uk.removed_numbers)} numbers:")
for num, reason in result_uk.removed_numbers:
    print(f"  ❌ {num} - {reason}")

print("\n" + "=" * 70)
print("✅ PHONE CLEANING SYSTEM TEST COMPLETE")
print("=" * 70)
