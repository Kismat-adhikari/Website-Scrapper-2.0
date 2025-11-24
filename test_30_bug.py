"""
Test to see how "30" could be extracted as a phone number
"""

from scraper import ContactExtractor, DataValidator

# Test if "30" passes validation
print("Testing if '30' passes validation:")
print(f"is_valid_phone('30'): {DataValidator.is_valid_phone('30')}")
print()

# Test extraction from various texts
test_texts = [
    "We've been in business for 30 years.",
    "Call us at 30",
    "Phone: 30",
    "Contact: 30",
    "30",
    "Open 9am-5pm, 30 days a week",
    "Price: $30",
    "30 Main Street",
]

print("Testing extraction from various texts:")
print("=" * 70)

for text in test_texts:
    phones = ContactExtractor.extract_phones(text)
    if phones:
        print(f"✗ FOUND: '{text}' -> {phones}")
    else:
        print(f"✓ OK: '{text}' -> (no phones)")

print("\n" + "=" * 70)

# Test with actual phone patterns
print("\nTesting phone patterns:")
import re

US_PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b')
INTL_PHONE_PATTERN = re.compile(r'\+[0-9]{1,3}[-.\s]?(?:\(?[0-9]{2,4}\)?[-.\s]?)?[0-9]{3,4}[-.\s]?[0-9]{3,4}(?:[-.\s]?[0-9]{1,4})?')

for text in test_texts:
    us_matches = US_PHONE_PATTERN.findall(text)
    intl_matches = INTL_PHONE_PATTERN.findall(text)
    
    if us_matches or intl_matches:
        print(f"Pattern matched: '{text}'")
        print(f"  US: {us_matches}")
        print(f"  INTL: {intl_matches}")
