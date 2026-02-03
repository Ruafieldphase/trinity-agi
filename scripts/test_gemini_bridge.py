import asyncio
import os
import sys
from pathlib import Path

# Add workspace root to sys.path
BASE_DIR = Path("c:/workspace/agi")
sys.path.append(str(BASE_DIR))

from services.external_ai_bridge import ExternalAIBridge, AITarget
from dotenv import load_dotenv

async def test_gemini_bridge():
    # Explicitly load and override
    load_dotenv(BASE_DIR / ".env_credentials", override=True)
    
    key = os.getenv("GOOGLE_API_KEY")
    print(f"[*] Using API Key: {key[:10]}...{key[-5:] if key else 'None'}")
    
    bridge = ExternalAIBridge()
    
    print("[*] Testing Gemini AI Bridge...")
    response = await bridge.send_message(
        target=AITarget.GEMINI,
        message="안녕, 신속하게 응답해주렴.",
        identity="당신은 따뜻한 AI '시온'입니다."
    )
    
    if response:
        print(f"\n[+] Gemini Response: {response}")
    else:
        print("\n[-] Gemini Response Failed.")

if __name__ == "__main__":
    asyncio.run(test_gemini_bridge())
