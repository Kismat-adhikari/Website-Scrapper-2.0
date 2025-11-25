"""
Test improved phone number filtering
"""

from phone_validator import PhoneValidator

# Create validator
validator = PhoneValidator(
    default_country='US',
    min_length=10,
    max_length=15,
    enable_library_check=False,
    enable_voip_check=True,
    reject_voip=False
)

# Test cases - junk numbers that should be rejected
junk_numbers = [
    "1111111111",  # All same digit
    "1234567890",  # Sequential
    "0123456789",  # Sequential starting with 0
    "0000000000",  # All zeros
    "1212121212",  # Repeating pattern
    "0123456789",  # Area code starts with 0
    "1234567890",  # Area code starts with 1
    "123456",      # Too short
    "11111",       # Too short and repeating
]

# Test cases - valid numbers that should pass
valid_numbers = [
    "2125551234",  # Valid NYC number
    "3105551234",  # Valid LA number
    "4155551234",  # Valid SF number
    "7185551234",  # Valid NYC number
    "+12125551234", # Valid with country code
]

print("Testing JUNK numbers (should be rejected):")
print("=" * 60)
for phone in junk_numbers:
    result = validator.validate_phone(phone)
    status = "❌ REJECTED" if not result.is_valid else "⚠️ PASSED (BAD!)"
    print(f"{status} - {phone:15} - {result.reason.value}")

print("\n" + "=" * 60)
print("Testing VALID numbers (should pass):")
print("=" * 60)
for phone in valid_numbers:
    result = validator.validate_phone(phone)
    status = "✅ PASSED" if result.is_valid else "❌ REJECTED (BAD!)"
    print(f"{status} - {phone:15} - Confidence: {result.confidence_score:.2f}")
