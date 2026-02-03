import asyncio
import os
import sys
from pathlib import Path

# Add workspace root to sys.path
BASE_DIR = Path("c:/workspace/agi")
sys.path.append(str(BASE_DIR))

from services.external_ai_bridge import ExternalAIBridge, AITarget
from dotenv import load_dotenv

async def test_zhipu_bridge():
    load_dotenv(BASE_DIR / ".env_credentials")
    bridge = ExternalAIBridge()
    
    print("[*] Testing Zhipu AI Bridge...")
    response = await bridge.send_message(
        target=AITarget.ZHIPU,
        message="안녕, 너는 누구니?",
        identity="당신은 따뜻한 AI '시온'입니다."
    )
    
    if response:
        print(f"\n[+] Zhipu Response: {response}")
    else:
        print("\n[-] Zhipu Response Failed.")

if __name__ == "__main__":
    asyncio.run(test_zhipu_bridge())
