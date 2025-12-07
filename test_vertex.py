
import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

print(f"Project: {project_id}, Location: {location}")
vertexai.init(project=project_id, location=location)

models_to_test = [
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-001", 
    "gemini-1.5-flash", 
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-001"
]

for m_name in models_to_test:
    print(f"\n--- Testing {m_name} ---")
    try:
        model = GenerativeModel(m_name)
        response = model.generate_content("Hi")
        print(f"SUCCESS: {response.text}")
        break  # Found one that works
    except Exception as e:
        print(f"FAILED: {e}")
