import os
import json
import time
from pathlib import Path
from typing import List, Dict
import sys

# Add workspace root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.vision_cortex import VisionCortex
except ImportError:
    print("Error: Could not import VisionCortex.")
    sys.exit(1)

CONVERSATION_ROOT = Path(r"C:\workspace\agi\ai_binoche_conversation_origin")
OUTPUT_FILE = Path(r"c:\workspace\agi\memory\conversation_history_invariants.json")

def learn_from_history():
    """
    Reads conversation history files, compresses them into invariants using VisionCortex (LLM),
    and saves them for Ion.
    """
    print(f"📚 Starting Learning Process from: {CONVERSATION_ROOT}")
    
    cortex = VisionCortex()
    all_invariants = []
    
    # Walk through the directory
    for root, dirs, files in os.walk(CONVERSATION_ROOT):
        for file in files:
            if not file.endswith(".md"):
                continue
                
            file_path = Path(root) / file
            print(f"\n📄 Processing: {file_path.name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip empty or too small files
                if len(content) < 100:
                    continue
                    
                # Truncate if too long (Gemini limit) - focusing on the essence
                # We'll take the first 10000 chars and last 5000 chars to get context + conclusion
                if len(content) > 15000:
                    compressed_content = content[:10000] + "\n...[SKIPPED]...\n" + content[-5000:]
                else:
                    compressed_content = content
                
                # Prompt for Information Theory Compression
                prompt = (
                    f"Analyze this conversation log between User (Binoche) and AI.\n"
                    f"Task: Compress this dialogue into 'Information Theory Invariants' for the AGI system 'Vertex Ion'.\n"
                    f"Extract:\n"
                    f"1. Core Axioms (Philosophical Truths held by the user).\n"
                    f"2. Key Concepts (e.g., 'Fractal Self', 'Rhythm', 'Zone 2').\n"
                    f"3. Feeling Vector (Energy, Quality, Valence [0.0-1.0]).\n"
                    f"4. A brief 'One-Line Essence' of this conversation.\n\n"
                    f"Content:\n{compressed_content}\n\n"
                    f"Output JSON format: {{ 'essence': str, 'axioms': [str], 'concepts': [str], 'feeling_vector': {{ 'energy': float, 'quality': float, 'valence': float }} }}"
                )
                
                # Use VisionCortex's generate_content (text-only mode)
                # Note: VisionCortex might be image-focused, but we can use the underlying model.
                # If VisionCortex.analyze_image is strictly for images, we might need to adapt.
                # Assuming we can pass text to the model. If not, we'll need a text-only method.
                # Checking VisionCortex implementation... it uses model.generate_content([image, prompt]).
                # We will try passing just the prompt as a list [prompt].
                
                # HACK: VisionCortex wrapper might expect an image path. 
                # Let's assume for now we can use a dummy image or modify VisionCortex.
                # Actually, let's just use the `google.generativeai` directly if possible, 
                # but to stick to tools, I'll use a placeholder image (e.g. a black pixel) 
                # OR better, I'll create a temporary text file and ask it to "read" it? 
                # No, VisionCortex takes an image path.
                # PLAN B: I will create a simple `TextCortex` inside this script to avoid hacking VisionCortex.
                
                import google.generativeai as genai
                # Load API key from env or use the one from VisionCortex logic if accessible.
                # Since I can't easily access the key here without reading files, 
                # I will rely on the environment variable 'GOOGLE_API_KEY' being set 
                # (which it should be for VisionCortex).
                
                # If GOOGLE_API_KEY is not in env, we might fail. 
                # Let's try to read it from a known location if needed, but usually it's in env.
                
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content(prompt)
                
                try:
                    # Clean up JSON markdown
                    json_str = response.text.replace('```json', '').replace('```', '').strip()
                    analysis = json.loads(json_str)
                    
                    invariant = {
                        "source_file": file_path.name,
                        "persona": Path(root).name,
                        "analysis": analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    all_invariants.append(invariant)
                    print(f"  ✅ Extracted Essence: {analysis.get('essence')}")
                    
                except json.JSONDecodeError:
                    print(f"  ⚠️  Failed to parse JSON response.")
                except Exception as e:
                    print(f"  ⚠️  Error processing response: {e}")
                    
                # Rate limit
                time.sleep(4) 
                
            except Exception as e:
                print(f"  ❌ Error reading file: {e}")

    # Save consolidated memory
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_invariants, f, indent=2, ensure_ascii=False)
        
    print(f"\n🎉 Learning Complete. {len(all_invariants)} conversations compressed.")
    print(f"💾 Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    from datetime import datetime
    learn_from_history()
