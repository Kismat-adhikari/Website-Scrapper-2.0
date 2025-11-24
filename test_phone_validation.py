"""
Test phone validation improvements
"""

from scraper import DataValidator, ContactExtractor

# Test cases
test_cases = [
    # Valid phones
    ("555-123-4567", True, "Valid US phone"),
    ("+1-555-123-4567", True, "Valid US phone with country code"),
    ("+44 20 7123 4567", True, "Valid UK phone"),
    ("(555) 123-4567", True, "Valid US phone with parens"),
    
    # Invalid phones (should be filtered)
    ("30", False, "Too short"),
    ("123", False, "Too short"),
    ("1234567", False, "Too short (7 digits)"),
    ("555-555-5555", True, "Fake pattern but valid format"),  # Will be caught by fake pattern
    ("111-111-1111", False, "All same digits"),
    ("123-456-7890", True, "Sequential but valid format"),
    ("000-000-0000", False, "All zeros"),
    ("2024", False, "Looks like year"),
    ("1999", False, "Looks like year"),
]

print("Testing Phone Validation")
print("=" * 70)

for phone, expected_valid, description in test_cases:
    is_valid = DataValidator.is_valid_phone(phone)
    status = "✓" if is_valid == expected_valid else "✗"
    result = "VALID" if is_valid else "INVALID"
    
    print(f"{status} {phone:20s} -> {result:10s} ({description})")

print("\n" + "=" * 70)

# Test extraction from text
test_text = """
Contact us at 555-123-4567 or call (555) 987-6543.
Our office is open from 9am to 5pm, Monday through Friday.
We've been in business for 30 years.
Prices start at $1999.
International: +44 20 7123 4567
"""

print("\nExtracting phones from text:")
print("-" * 70)
print(test_text)
print("-" * 70)

phones = ContactExtractor.extract_phones(test_text)
print(f"\nExtracted {len(phones)} phone(s):")
for phone in sorted(phones):
    print(f"  - {phone}")

print("\n" + "=" * 70)
print("✓ Test completed!")
