import base64
import json
import requests
import os
import sys
import time
from PIL import Image
import io
from typing import Optional, List

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from services.config import LINUX_HOST
except ImportError:
    LINUX_HOST = "192.168.119.128"

OLLAMA_URL = f"http://{LINUX_HOST}:11434/api/generate"

def analyze_image_locally(image_path: str, prompt: str, model: str = "llava:7b") -> Optional[str]:
    """
    Analyzes an image using a local vision model on the Linux VM.
    """
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"

    try:
        start_time = time.time()
        
        # Performance Optimization: Image Compression
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (Ollama prefers standard RGB)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Compress image to reduce network latency
            output = io.BytesIO()
            # 80-90% quality for better CAD element detection on small local models
            img.save(output, format="JPEG", quality=85, optimize=True)
            img_bytes = output.getvalue()
            
        encode_time = time.time() - start_time
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "images": [img_base64]
        }

        print(f"Sending request to local vision model ({model}) at {OLLAMA_URL}...")
        request_start = time.time()
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        request_time = time.time() - request_start
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            total_time = time.time() - start_time
            print(f"--- Vision Metrics ---")
            print(f"Encode time: {encode_time:.2f}s")
            print(f"Request/Inference time: {request_time:.2f}s")
            print(f"Total time: {total_time:.2f}s")
            print(f"Payload size: {len(img_base64)/1024:.1f} KB")
            print(f"----------------------")
            return response_text
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

if __name__ == "__main__":
    # Test call
    import sys
    test_img = "c:/workspace/agi/outputs/arch_analysis/frame_10.jpg"
    test_prompt = "What architectural modeling tools are visible in this screenshot?"
    if len(sys.argv) > 1:
        test_img = sys.argv[1]
    
    print(analyze_image_locally(test_img, test_prompt))
