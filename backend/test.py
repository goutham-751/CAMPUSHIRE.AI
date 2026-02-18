# test_gemini.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"Key format: {'OLD' if api_key.startswith('AIzaSy') else 'NEW'}")
try:
    # NEW API: Create client directly
    client = genai.Client(api_key=api_key)
    
    # NEW API: Generate content
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Hello, please respond with 'API key works!'"
    )
    
    print("✅ API key works!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")