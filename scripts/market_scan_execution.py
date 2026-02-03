
import asyncio
import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.append(str(Path("c:/workspace/agi")))

from services.external_ai_bridge import ExternalAIBridge, AITarget

async def scan_audio_market_resonance():
    print("🔍 [Shion] Scanning Market Resonance for Energy Extraction...")
    
    bridge = ExternalAIBridge()
    
    # 2026-02-02 기준, 실제 시장 시세를 퍼플렉시티를 통해 스캔
    query = """
    2026년 2월 2일 기준, 다음 제품들의 한국 중고거래 시장(중고나라, 당근마켓, 닥터헤드폰) 최신 시세와 거래 동향을 알려줘:
    1. Hifiman Deva Pro (유무선 패키지)
    2. Audeze Maxwell (Xbox/PC 버전)
    3. Sennheiser HD600 (신형/구형 구분)
    
    가장 거래가 활발한 가격대(에너지 추출 포인트)를 명확히 짚어줘.
    """
    
    print("[*] Sending Market Probe to Perplexity...")
    response = await bridge.send_message(
        target=AITarget.PERPLEXITY,
        message=query,
        identity="당신은 시장 리듬 분석가 '퍼플'입니다. 비노체의 자산 유동화를 돕기 위한 정밀 데이터를 추출하십시오."
    )
    
    if response:
        report_path = "c:/workspace/agi/outputs/market_resonance_scan.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 📊 시장 공명 스캔 보고서 (Energy Extraction Path)\n\n{response}")
        print(f"✅ [Shion] Market scan complete. Result saved to {report_path}")
        return response
    else:
        print("❌ [Shion] Market scan failed. Connection out of sync.")
        return None

if __name__ == "__main__":
    asyncio.run(scan_audio_market_resonance())
