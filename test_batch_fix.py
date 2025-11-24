"""
Test script to verify batch scraping is working
"""

import requests
import json
import time

# Test URLs
test_urls = [
    'https://example.com',
    'https://google.com',
    'https://github.com'
]

print("Testing batch scraping endpoint...")
print(f"URLs to scrape: {len(test_urls)}")
print("-" * 60)

# Start Flask server first: python app.py
API_URL = 'http://localhost:5000/api/batch'

try:
    # Send batch request
    print("\n1. Sending batch request...")
    response = requests.post(API_URL, json={'urls': test_urls}, timeout=120)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        total = data.get('total', 0)
        
        print(f"\n✓ Batch scraping completed!")
        print(f"Total results: {total}")
        print("-" * 60)
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['url']}")
            print(f"   Status: {result['status']}")
            print(f"   Emails: {len(result.get('emails', []))} found")
            print(f"   Phones: {len(result.get('phones', []))} found")
            print(f"   Confidence: {result.get('confidence_score', 0)}")
            
            if result['status'] == 'failed':
                print(f"   Reason: {result.get('reason', 'Unknown')}")
            else:
                if result.get('emails'):
                    print(f"   Emails: {', '.join(result['emails'][:3])}")
                if result.get('phones'):
                    print(f"   Phones: {', '.join(result['phones'][:3])}")
        
        # Summary
        successful = sum(1 for r in results if r['status'] != 'failed')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        print("\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"  Successful: {successful}/{total}")
        print(f"  Failed: {failed}/{total}")
        print("=" * 60)
        
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n✗ Error: Could not connect to Flask server")
    print("Make sure Flask is running: python app.py")
except requests.exceptions.Timeout:
    print("\n✗ Error: Request timed out")
    print("Batch scraping is taking too long")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
