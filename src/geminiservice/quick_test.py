#!/usr/bin/env python3
import os
import json
import requests

# Get credentials from environment
API_KEY = os.getenv("GEMINI_API_KEY")
API_ENDPOINT = os.getenv("GEMINI_API_ENDPOINT")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

print(f"Endpoint: {API_ENDPOINT}")
print(f"Model: {MODEL}")
print(f"Token (first 20 chars): {API_KEY[:20]}..." if API_KEY else "No token")

if API_KEY and API_ENDPOINT:
    url = f"{API_ENDPOINT.rstrip('/')}/chat/completions"
    print(f"\nTesting: {url}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say hello in 5 words"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            print(json.dumps(response.json(), indent=2)[:500])
        else:
            print(f"❌ Error: {response.text[:500]}")
    except requests.Timeout:
        print("❌ Request timed out after 10 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("Missing API_KEY or API_ENDPOINT")
