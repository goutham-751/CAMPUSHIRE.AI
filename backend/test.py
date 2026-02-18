# test_groq.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key found: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"Key format: {'GROQ' if api_key and api_key.startswith('gsk_') else 'UNKNOWN'}")
try:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello, please respond with 'API key works!'"}],
        max_tokens=50,
    )

    print("✅ API key works!")
    print(f"Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")