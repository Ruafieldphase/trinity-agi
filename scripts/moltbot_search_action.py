
import asyncio
import sys
import os
from pathlib import Path

# Add current dir to path to import services
sys.path.append(str(Path("c:/workspace/agi")))

from services.external_ai_bridge import ExternalAIBridge, AITarget

async def main():
    bridge = ExternalAIBridge()
    target = AITarget.PERPLEXITY
    
    query = """
    2026년 1월 31일 기준, 한국 중고거래 시장(중고나라, 당근마켓, 닥터헤드폰, 뮬)에서의 다음 제품들의 실시간 최신 시세와 거래 동향을 조사해줘. 
    특히 신형 출시 소식이나 덤핑 소식이 있는지도 확인해줘.
    
    1. FiiO JM21 (동글 DAC)
    2. Black Lion Audio PG-P Type K (파워 컨디셔너)
    3. Hifiman HE-R10D (다이나믹 헤드폰)
    4. Klipsch R-8SW (8인치 서브우퍼)
    5. Polk Audio PSW 111 (8인치 서브우퍼)
    
    조사 결과를 바탕으로 가장 빠르게 현금을 확보할 수 있는 '급매가'와 '적정가'를 구분해서 정리해줘.
    """
    
    print(f"[*] Moltbot launching Perplexity Search for current market data...")
    
    # Send message and wait for response
    # Default identity is None, context is None
    response = await bridge.send_message(
        target=target,
        message=query,
        timeout_sec=120
    )
    
    if response:
        print("\n[+] Moltbot Search Result Received. Proceeding with Ollama Analysis...")
        print("-" * 50)
        
        # Post-process with Gemini (API)
        analysis_query = f"""
        다음은 최신 오디오 장비 시장 검색 결과야.
        이 데이터를 기반으로 '급매가(Urgent Sale Price)'와 '적정 시장가(Fair Market Value)'를 구분해서 분석해줘.
        또한, 자본 확보를 위한 가장 즉각적인 판매 전략을 제안해줘.
        
        검색 데이터:
        {response}
        """
        
        analysis = await bridge.send_message(
            target=AITarget.GEMINI,
            message=analysis_query,
            identity="당신은 자산 유동화와 시장 분석 전문가인 몰트봇(Moltbot)입니다."
        )
        
        if analysis:
            print("\n[+] Moltbot Market Analysis (Gemini):")
            print(analysis)
            print("-" * 50)
            
            output_path = Path("c:/workspace/agi/outputs/moltbot_real_search_result.md")
            # datetime is imported in __main__ block, but available global if imported at top
            from datetime import datetime
            final_content = f"# Moltbot Real-time Market Analysis\n\nDate: {datetime.now().strftime('%Y-%m-%d')}\n\n## Summary & Strategy\n{analysis}\n\n## Raw Research Data\n{response}"
            output_path.write_text(final_content, encoding="utf-8")
            print(f"\n[!] Saved final analysis to: {output_path}")
        else:
            print("\n[-] Gemini Analysis Failed.")
    else:
        print("\n[-] Moltbot Search Failed or Timed out.")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
