
import os
import google.generativeai as genai
from pathlib import Path

def list_models():
    # Load key from .env_credentials
    api_key = None
    # Force use of wave_ key from memory
    api_key = 'wave_oqmqci0z-ymwu4j2z-m188fsu2-ayj6qasr'
        
    genai.configure(api_key=api_key)
    
    print(f"Listing models for API key: {api_key[:5]}...{api_key[-5:]}")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} ({m.display_name})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
