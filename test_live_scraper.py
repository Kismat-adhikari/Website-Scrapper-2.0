"""
Test the live scraper to see what it's actually returning
"""

import requests
import json

# Test URL - replace with the URL that's showing "30"
test_url = input("Enter the URL that's showing '30' as a phone: ").strip()

if not test_url:
    test_url = "https://example.com"

print(f"\nTesting: {test_url}")
print("=" * 70)

try:
    response = requests.post(
        'http://127.0.0.1:5000/api/scrape',
        json={'url': test_url},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nStatus: {data['status']}")
        print(f"Phones found: {len(data.get('phones', []))}")
        
        if data.get('phones'):
            print("\nPhone numbers:")
            for i, phone in enumerate(data['phones'], 1):
                print(f"  {i}. {phone} (length: {len(phone)} chars, digits: {len([c for c in phone if c.isdigit()])})")
        else:
            print("\nNo phones found")
        
        print(f"\nFull response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {str(e)}")
