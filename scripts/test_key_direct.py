import google.generativeai as genai
import os
from pathlib import Path

def test_direct():
    key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        print(f"Testing key: {key[:10]}...")
        response = model.generate_content("Hi")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_direct()
