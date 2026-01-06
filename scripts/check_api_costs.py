import os
import sys
from pathlib import Path
from workspace_root import get_workspace_root

def _load_dotenv_value(key: str) -> str:
    root = get_workspace_root()
    for env_path in (root / ".env_credentials", root / ".env"):
        if not env_path.exists():
            continue
        try:
            for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("'").strip('"')
        except: pass
    return ""

def check_costs():
    print("🔍 GCP / API Cost Analysis Diagnostic")
    print("======================================")
    
    # 1. Credentials Check
    google_key = os.getenv("GOOGLE_API_KEY") or _load_dotenv_value("GOOGLE_API_KEY")
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or _load_dotenv_value("GOOGLE_CLOUD_PROJECT")
    gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or _load_dotenv_value("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"🔹 Google API Key (AI Studio): {'MASKED' if google_key else 'Missing'}")
    print(f"🔹 GCP Project (Vertex AI): {gcp_project or 'Missing'}")
    print(f"🔹 GCP Credentials Path: {gcp_creds or 'Missing'}")
    print("-" * 40)

    # 2. Script Provider Audit
    scripts_to_check = [
        "llm_client.py",
        "youtube_feeling_learner.py",
        "vision_motor_bridge.py",
        "gemini_chat.py",
        "ai_model_router.py",
        "extract_ui_actions.py",
        "analyze_obs_report.py"
    ]
    
    scripts_dir = get_workspace_root() / "scripts"
    print("📋 Script Configuration Audit:")
    
    for script_name in scripts_to_check:
        path = scripts_dir / script_name
        if not path.exists():
            print(f"  - {script_name:25}: ❓ File not found")
            continue
            
        content = path.read_text(encoding="utf-8", errors="replace")
        
        has_vertex = "import vertexai" in content
        has_genai = "import google.generativeai" in content or "google-ai-studio" in content
        uses_fallback = "backend" in content or "provider" in content
        
        # Inference of default provider
        provider = "Free AI Studio"
        if has_vertex and not has_genai:
            status = "🔴 Paid (Vertex Only)"
            provider = "Vertex AI"
        elif has_vertex and has_genai:
            status = "✅ Safe (Free First)"
            provider = "AI Studio -> Vertex Fallback"
        elif has_genai:
            status = "✅ Safe (Free)"
            provider = "AI Studio"
        else:
            status = "❓ Unknown"
            provider = "Unknown"

        print(f"  - {script_name:25}: {status:20} | Provider: {provider}")

    print("-" * 40)
    print("💡 Diagnosis:")
    print("  1. Vertex AI calls trigger 'GCP Billing' events, requiring card validation.")
    print("  2. AI Studio (Gemini API) via API Key is free within limits and avoids GCP Billing issues.")
    print("  3. Your Mastercard decline blocks the GCP project even if you have $1.4M credits.")
    print("\n🚀 Proposed FIX: Migrate secondary scripts to 'Free Tier' AI Studio where possible.")

if __name__ == "__main__":
    check_costs()
