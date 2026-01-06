import os
import google.generativeai as genai
from PIL import Image
import io

def test_vision():
    api_key = "AIzaSyAF5KquOJmisabOzX1O2xxiNLVI6qa1s88"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Create a small dummy image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_data = buf.getvalue()
    
    try:
        response = model.generate_content([
            "What is in this image?",
            {"mime_type": "image/png", "data": img_data}
        ])
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_vision()
