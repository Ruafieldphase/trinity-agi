
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key[:5]}...")

genai.configure(api_key=api_key)

print("Listing models...")
for m in genai.list_models():
    if "gemini" in m.name:
        print(m.name)

print("\n--- Testing gemini-1.5-flash ---")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hello from AI Studio")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILED: {e}")
