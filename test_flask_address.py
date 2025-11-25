"""
Test Flask app with a real coffee shop URL to verify address extraction
"""

import requests
import json

# Start by testing if Flask is running
print("Testing Flask App Address Extraction")
print("=" * 60)

# Test URL - a coffee shop that should have an address
test_url = "https://www.bluebottlecoffee.com"

print(f"\nTesting with: {test_url}")
print("Sending request to Flask API...")

try:
    response = requests.post(
        'http://localhost:5000/api/scrape',
        json={'url': test_url},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Status: {data.get('status')}")
        print(f"📧 Emails: {len(data.get('emails', []))}")
        print(f"📞 Phones: {len(data.get('phones', []))}")
        print(f"🏢 Company: {data.get('company_name', 'Not found')}")
        print(f"📍 Addresses: {len(data.get('addresses', []))}")
        
        if data.get('addresses'):
            print("\nAddresses found:")
            for addr in data['addresses']:
                print(f"  - {addr}")
        else:
            print("\n⚠️  No addresses found")
        
        if data.get('company_description'):
            desc = data['company_description']
            print(f"\n📝 Description: {desc[:100]}...")
        
        print(f"\n📊 Confidence: {data.get('confidence_score', 0):.2f}")
        print(f"📄 Pages Scanned: {data.get('pages_scanned', 0)}")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Flask app is not running!")
    print("Please start it with: python app.py")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
