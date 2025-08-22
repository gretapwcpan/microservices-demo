#!/usr/bin/env python3
"""
Test for custom Gemini-compatible API (TrendMicro)
"""
import os
import json
import requests

# Load environment variables
API_KEY = os.getenv("GEMINI_API_KEY")
API_ENDPOINT = os.getenv("GEMINI_API_ENDPOINT", "https://api.rdsec.trendmicro.com/prod/aiendpoint/v1/")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

print(f"Testing Custom API")
print(f"Endpoint: {API_ENDPOINT}")
print(f"Model: {MODEL}")
print(f"Token present: {'Yes' if API_KEY else 'No'}")

if API_KEY:
    # Prepare the request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test prompt
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": """You are a mystical curator for quanBuy, a mindful marketplace.
                User's recent searches: vintage, bohemian, handmade
                
                Generate a surprising product discovery in JSON format:
                {
                    "product_name": "unique name",
                    "reason": "why it matches their soul",
                    "description": "poetic 2 sentence description",
                    "category": "one word",
                    "price_range": "$XX-XX"
                }"""
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        # Make the API call
        url = f"{API_ENDPOINT.rstrip('/')}/chat/completions"
        print(f"\nCalling: {url}")
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("\n✅ API Test Successful!")
            result = response.json()
            
            # Extract the content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print("\nResponse:")
                print(content)
            else:
                print("\nFull response:")
                print(json.dumps(result, indent=2))
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n⚠️ No API key found in environment")

print("\n🎉 Test complete!")
