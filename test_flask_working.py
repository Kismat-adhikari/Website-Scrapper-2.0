"""
Test Flask API to verify it's working
"""

import requests
import json

API_URL = 'http://127.0.0.1:5000/api/scrape'

test_urls = [
    'https://example.com',
    'https://google.com',
    'https://github.com'
]

print("Testing Flask API with multiple URLs...")
print("=" * 60)

for i, url in enumerate(test_urls, 1):
    print(f"\n{i}. Testing: {url}")
    try:
        response = requests.post(API_URL, json={'url': url}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Status: {data['status']}")
            print(f"   ✓ Emails: {len(data.get('emails', []))} found")
            print(f"   ✓ Phones: {len(data.get('phones', []))} found")
            print(f"   ✓ Load time: {data.get('load_time', 0):.2f}s")
            print(f"   ✓ Company: {data.get('company_name', 'N/A')}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Exception: {str(e)}")

print("\n" + "=" * 60)
print("✓ All tests completed!")
