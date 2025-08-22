#!/usr/bin/env python3
"""
Simple local test for Gemini API
"""
import os
import google.generativeai as genai

# Load environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

print(f"Testing Gemini API with model: {GEMINI_MODEL}")
print(f"API Key present: {'Yes' if GEMINI_API_KEY else 'No'}")

if GEMINI_API_KEY and GEMINI_API_KEY != "mock_mode":
    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Test Mystery Search
    prompt = """
    You are a mystical curator for quanBuy, a mindful marketplace.
    User's recent searches: vintage, bohemian, handmade
    
    Generate a surprising product discovery in JSON format:
    {
        "product_name": "unique name",
        "reason": "why it matches their soul",
        "description": "poetic 2 sentence description",
        "category": "one word",
        "price_range": "$XX-XX"
    }
    """
    
    try:
        response = model.generate_content(prompt)
        print("\n✅ Gemini API Test Successful!")
        print("\nResponse:")
        print(response.text)
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n⚠️ No API key found. Using mock response:")
    print("""
    {
        "product_name": "Serendipity Stone",
        "reason": "Sometimes the universe chooses for you",
        "description": "A moment of unexpected discovery. Let curiosity guide you.",
        "category": "mystery",
        "price_range": "$30-80"
    }
    """)

print("\n🎉 Test complete!")
