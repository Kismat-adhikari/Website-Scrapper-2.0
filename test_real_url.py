"""Test with a real URL"""
import requests
import json

url = "https://graybox.co"
print(f"Testing: {url}")

r = requests.post('http://localhost:5000/api/scrape', json={'url': url}, timeout=45)
data = r.json()

print(f"\nStatus: {data['status']}")
print(f"Emails: {len(data['emails'])}")
print(f"Phones: {len(data['phones'])}")
print(f"Addresses: {len(data['addresses'])}")
print(f"Company: {data['company_name']}")
print(f"Description: {data['company_description'][:100] if data['company_description'] else 'None'}...")

if data['addresses']:
    print("\nAddresses found:")
    for a in data['addresses']:
        print(f"  - {a}")
else:
    print("\n⚠️ No addresses found")

print(f"\nPages scanned: {data['pages_scanned']}")
print(f"Confidence: {data['confidence_score']}")
