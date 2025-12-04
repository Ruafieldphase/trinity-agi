#!/bin/bash
cat <<'EOF' > ~/agi/scripts/execute_proposal.py
import json
import os
import sys
import time
import google.generativeai as genai
from pathlib import Path

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
PROPOSALS_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "proposals.json")
LOG_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "execution.log")

# Configure Gemini
def load_api_key():
    try:
        from dotenv import load_dotenv
        # Try loading from WORKSPACE_ROOT/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))
        # Try loading from WORKSPACE_ROOT/fdo_agi_repo/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", ".env"))
    except ImportError:
        pass

    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

API_KEY = load_api_key()

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("Warning: No API_KEY found (checked GOOGLE_API_KEY and GEMINI_API_KEY)")

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def load_proposals():
    if os.path.exists(PROPOSALS_FILE):
        try:
            with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_proposals(proposals):
    with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)

def execute_refactor(file_path, instruction):
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
        prompt = f"""
        You are an expert AI software engineer.
        Your task is to REFACTOR the following code based on the instruction.
        
        **Instruction:** {instruction}
        
        **File Path:** {file_path}
        
        **Code Content:**
        ```
        {content}
        ```
        
        Return ONLY the full, modified code. Do not include markdown code blocks (```) if possible, or I will strip them.
        Do not add conversational text.
        """
        
        response = model.generate_content(prompt)
        new_content = response.text.strip()
        
        # Clean up markdown
        if new_content.startswith("```"):
            lines = new_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            new_content = "\n".join(lines)
            
        # Backup original
        backup_path = f"{file_path}.bak.{int(time.time())}"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Write new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return True, f"Refactored successfully. Backup saved to {backup_path}"
        
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python execute_proposal.py <proposal_id>")
        return

    proposal_id = int(sys.argv[1])
    proposals = load_proposals()
    
    target_proposal = None
    for p in proposals:
        if p.get("id") == proposal_id:
            target_proposal = p
            break
            
    if not target_proposal:
        print(f"Proposal {proposal_id} not found.")
        return

    log(f"Executing proposal {proposal_id}: {target_proposal['type']} on {target_proposal.get('file')}")
    
    # Update status to executing
    target_proposal["status"] = "executing"
    save_proposals(proposals)
    
    success = False
    message = ""
    
    if target_proposal["type"] == "REFACTOR":
        file_path = target_proposal.get("file").replace("\\", "/") # Normalize path for Linux
        # Ensure absolute path using WORKSPACE_ROOT
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE_ROOT, file_path)
            
        instruction = target_proposal.get("observation") # Use observation as instruction
        success, message = execute_refactor(file_path, instruction)
    else:
        success = True
        message = f"Simulated execution for type {target_proposal['type']}"
        
    # Update final status
    target_proposal["status"] = "completed" if success else "failed"
    target_proposal["result"] = message
    save_proposals(proposals)
    
    log(f"Execution finished: {success} - {message}")

if __name__ == "__main__":
    main()
EOF
echo "✅ execute_proposal.py updated successfully!"
