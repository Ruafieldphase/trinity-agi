import os
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    print(f"API Key prefix: {api_key[:5]}...")
    try:
        genai.configure(api_key=api_key)
        print("Listing models with 'generateContent' method...")
        
        working_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                working_models.append(m.name)
        
        if not working_models:
            print("WARNING: No models found with 'generateContent' capability.")
        else:
            print(f"\nFound {len(working_models)} suitable models. Testing the first one...")
            test_model = working_models[0]
            try:
                model = genai.GenerativeModel(test_model)
                response = model.generate_content("Hello")
                print(f"SUCCESS: {test_model} worked! Response: {response.text}")
            except Exception as e:
                print(f"FAILED: {test_model} - {e}")

    except Exception as e:
        print(f"ERROR: Script failed: {e}")
else:
    print("ERROR: GOOGLE_API_KEY not found in environment.")
