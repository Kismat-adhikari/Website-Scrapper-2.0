#!/usr/bin/env python3
"""
Test Apify actor locally without Apify CLI
Simulates Apify environment for quick testing
"""

import asyncio
import json
import sys
from pathlib import Path

# Mock Apify Actor for local testing
class MockActor:
    """Mock Apify Actor for local testing"""
    
    class log:
        @staticmethod
        def info(msg):
            print(f"[INFO] {msg}")
        
        @staticmethod
        def warning(msg):
            print(f"[WARNING] {msg}")
        
        @staticmethod
        def error(msg):
            print(f"[ERROR] {msg}")
    
    @staticmethod
    async def get_input():
        """Load input from input.json"""
        input_file = Path('input.json')
        if input_file.exists():
            with open(input_file) as f:
                return json.load(f)
        return {}
    
    @staticmethod
    async def push_data(data):
        """Save data to results.json"""
        results_file = Path('results.json')
        
        # Load existing results
        results = []
        if results_file.exists():
            with open(results_file) as f:
                try:
                    results = json.load(f)
                except:
                    results = []
        
        # Append new data
        results.append(data)
        
        # Save
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Saved result for {data.get('url')}")
    
    @staticmethod
    async def create_proxy_configuration(**kwargs):
        """Mock proxy configuration"""
        class MockProxy:
            async def new_url(self):
                return None
        return MockProxy()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


# Monkey patch the Actor import
import sys
sys.modules['apify'] = type(sys)('apify')
sys.modules['apify'].Actor = MockActor


async def test_local():
    """Test the actor locally"""
    print("=" * 60)
    print("Testing Apify Actor Locally")
    print("=" * 60)
    
    # Create test input if it doesn't exist
    input_file = Path('input.json')
    if not input_file.exists():
        test_input = {
            "urls": [
                "https://example.com"
            ],
            "fastMode": True,
            "maxPages": 1,
            "maxConcurrency": 2
        }
        with open(input_file, 'w') as f:
            json.dump(test_input, f, indent=2)
        print(f"✓ Created test input.json")
    
    # Import and run main
    from main import main
    
    # Clear previous results
    results_file = Path('results.json')
    if results_file.exists():
        results_file.unlink()
    
    # Run the actor
    await main()
    
    # Show results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    
    if results_file.exists():
        with open(results_file) as f:
            results = json.load(f)
        
        print(f"\nProcessed {len(results)} URLs:\n")
        
        for result in results:
            print(f"URL: {result.get('url')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Emails: {len(result.get('emails', []))}")
            print(f"  Phones: {len(result.get('phones', []))}")
            print(f"  Company: {result.get('company_name', 'N/A')}")
            print(f"  Confidence: {result.get('confidence_score', 0)}")
            print()
        
        print(f"✓ Results saved to results.json")
    else:
        print("✗ No results generated")


if __name__ == '__main__':
    asyncio.run(test_local())
