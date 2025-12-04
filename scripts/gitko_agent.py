import sys
import subprocess
import json
import os
from pathlib import Path
import google.generativeai as genai

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

class GitkoAgent:
    """
    Gitko Agent: The Actor (Action & Realization)
    Handles Git operations and code execution requests.
    Now speaks Korean via Gemini.
    """
    def __init__(self, workspace_root: str = "c:/workspace/agi"):
        self.workspace_root = Path(workspace_root)
        
    def run_git_command(self, command: list) -> str:
        """Run a git command in the workspace."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except Exception as e:
            return f"System Error: {str(e)}"

    def generate_response(self, intent: str, git_output: str) -> str:
        """Generates a friendly Korean response using Gemini."""
        if not API_KEY:
            return f"[Gitko] (API Key Missing) Command: {intent}\nOutput:\n{git_output}"

        try:
            model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
            prompt = f"""
            You are "Gitko" (깃코), a helpful and energetic Git Agent for this AI system.
            
            **Context:**
            User asked: "{intent}"
            Git command output:
            ```
            {git_output}
            ```
            
            **Task:**
            1. Analyze the git output.
            2. Explain what happened in **friendly, natural Korean** (한국어).
            3. YOU MUST OUTPUT IN KOREAN ONLY.
            3. If there's an error, suggest a fix.
            4. Keep it concise (1-2 sentences unless detailed output is needed).
            5. Use emojis like 🎭 (Mask/Persona) or 🐙 (Git).
            
            **Tone:** Professional yet warm. You are the "Actor" of the system.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Gitko] (Gemini Error) {str(e)}\nOutput:\n{git_output}"

    def handle_intent(self, message: str) -> str:
        """Parse message and execute git action."""
        msg = message.lower()
        output = ""
        command_type = ""
        
        if "status" in msg:
            output = self.run_git_command(["status"])
            command_type = "status"
        elif "log" in msg:
            output = self.run_git_command(["log", "-n", "3", "--oneline"])
            command_type = "log"
        elif "pull" in msg:
            output = self.run_git_command(["pull"])
            command_type = "pull"
        elif "push" in msg:
            output = self.run_git_command(["push"])
            command_type = "push"
        else:
            return "🎭 깃코입니다. 지원하는 명령어: status, log, pull, push."
            
        return self.generate_response(message, output)

if __name__ == "__main__":
    agent = GitkoAgent()
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(agent.handle_intent(message))
    else:
        print("Gitko Agent: No message provided.")
