"""Test description length"""
import requests

r = requests.post('http://localhost:5000/api/scrape', json={'url': 'https://graybox.co'}, timeout=45)
data = r.json()

desc = data.get('company_description', '')
print(f"Description length: {len(desc)} characters")
print(f"\nFull description:\n{desc}")
print(f"\nFirst 150 chars: {desc[:150]}")
print(f"\nShould show 'Read More': {len(desc) > 150}")
