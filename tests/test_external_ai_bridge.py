"""
External AI Bridge 테스트
"""
import asyncio
import sys
sys.path.insert(0, "c:/workspace/agi/services")

from external_ai_bridge import ExternalAIBridge, AITarget

async def test_bridge():
    print("=" * 60)
    print("External AI Bridge Test")
    print("=" * 60)
    
    bridge = ExternalAIBridge()
    
    # 현재 열린 AI 세션 확인
    active = bridge.get_active_sessions()
    print(f"\n현재 열린 AI 세션: {[t.value for t in active]}")
    
    # 테스트할 대상 선택
    print("\n테스트할 대상을 선택하세요:")
    print("1. ChatGPT")
    print("2. Claude")
    print("3. Comet")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    targets = {
        "1": AITarget.CHATGPT,
        "2": AITarget.CLAUDE,
        "3": AITarget.COMET,
    }
    
    target = targets.get(choice, AITarget.CHATGPT)
    print(f"\n선택됨: {target.value}")
    
    input("\nEnter를 누르면 테스트를 시작합니다...")
    
    # 메시지 전송 테스트
    response = await bridge.send_message(
        target=target,
        message="안녕! 테스트 메시지야. 간단히 '안녕'이라고 답해줘.",
        identity="안녕, 나는 Trinity야.",
        timeout_sec=45
    )
    
    print("\n" + "=" * 60)
    print("Response:")
    print("=" * 60)
    print(response or "(No response)")

if __name__ == "__main__":
    asyncio.run(test_bridge())
