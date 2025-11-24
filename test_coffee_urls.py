"""
Test the coffee shop URLs to find which one returns "30"
"""

import requests
import json

urls = [
    'https://www.slatecafe.com',
    'https://conwellcoffeehall.com',
    'https://www.unionsquarecafe.com',
    'https://www.littlecollinsnyc.com',
    'https://www.birchcoffee.com'
]

API_URL = 'http://127.0.0.1:5000/api/scrape'

print("Testing coffee shop URLs for phone extraction...")
print("=" * 70)

for i, url in enumerate(urls, 1):
    print(f"\n{i}. Testing: {url}")
    print("-" * 70)
    
    try:
        response = requests.post(API_URL, json={'url': url}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            phones = data.get('phones', [])
            
            print(f"Status: {data['status']}")
            print(f"Phones found: {len(phones)}")
            
            if phones:
                for phone in phones:
                    digits = ''.join(c for c in phone if c.isdigit())
                    print(f"  - {phone} ({len(digits)} digits)")
                    
                    # Check if "30" is in the results
                    if phone == "30" or "30" in phone:
                        print(f"    ⚠️  FOUND '30' IN PHONE!")
            else:
                print("  (no phones)")
                
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

print("\n" + "=" * 70)
print("Test completed!")
