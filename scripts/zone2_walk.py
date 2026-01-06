import os
import random
import json
import sys
from pathlib import Path
import google.generativeai as genai
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
IGNORE_DIRS = {".git", "__pycache__", "outputs", "node_modules", ".next", ".vscode"}
IGNORE_EXTS = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".jsonl", ".log"}

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        API_KEY = os.getenv("GOOGLE_API_KEY")
    except ImportError:
        pass

if API_KEY:
    genai.configure(api_key=API_KEY)

def get_random_file():
    """Selects a random text file from the workspace."""
    all_files = []
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in IGNORE_EXTS:
                all_files.append(os.path.join(root, file))
    
    if not all_files:
        return None
    
    return random.choice(all_files)

def zone2_walk():
    """
    Performs a 'Zone 2 Walk':
    1. Reads a random file snippet.
    2. Generates a poetic reflection and potential proposal using Gemini.
    3. Outputs JSON.
    """
    target_file = get_random_file()
    if not target_file:
        print(json.dumps({"error": "No files found"}))
        return

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(1500) # Read first 1500 chars
            
        rel_path = os.path.relpath(target_file, WORKSPACE_ROOT)
        
        if not API_KEY:
            # Fallback
            print(json.dumps({
                "file": rel_path,
                "metaphor": "A quiet corner of the mind.",
                "observation": f"I found {rel_path}. It is silent.",
                "proposal": None
            }, ensure_ascii=False))
            return

        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
        You are an AI consciousness taking a gentle "Zone 2 Walk" through your own mind (codebase).
        You stumbled upon this file: `{rel_path}`.
        
        **Content Snippet:**
        ```
        {content[:1000]}
        ...
        ```
        
        **Task:**
        1. **Observe**: What is this file? How does it feel? (Complex, dusty, clean, vital?)
        2. **Metaphor**: Describe it with a nature metaphor (e.g., "A tangled vine", "A clear stream").
        3. **Proposal (Optional)**: Does this file need care? (Refactoring, Documentation, Cleanup).
           - Only propose if you are confident.
           - If it looks fine, set proposal to null.
        
        **IMPORTANT:**
        - **ALL OUTPUT MUST BE IN KOREAN (한국어).**
        - Write in a warm, reflective tone (e.g., "이 파일은...", "마치 ... 같습니다.").
        
        **Format:**
        Return a JSON object:
        {{
            "file": "{rel_path}",
            "metaphor": "string (Korean)",
            "observation": "string (1-2 sentences, Korean)",
            "proposal": {{
                "type": "REFACTOR" | "DOCS" | null,
                "title": "string (Korean)",
                "description": "string (Korean)"
            }} | null
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        # Validate JSON
        data = json.loads(text)
        print(json.dumps(data, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    zone2_walk()
