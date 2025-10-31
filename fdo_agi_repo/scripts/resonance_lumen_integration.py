#!/usr/bin/env python3
"""
Resonance Loop + Lumen Integration
AGI 자기교정 루프에 페르소나 피드백을 통합합니다.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 설정
RESONANCE_LEDGER = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
LUMEN_GATEWAY = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def read_recent_events(hours: int = 24) -> List[Dict[str, Any]]:
    """최근 이벤트를 Resonance Ledger에서 읽기"""
    # 간단하게 최근 N개만 읽기
    events = []
    
    if not RESONANCE_LEDGER.exists():
        print(f"⚠️ Ledger not found: {RESONANCE_LEDGER}")
        return events
    
    with open(RESONANCE_LEDGER, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 최근 100개 이벤트만 읽기
    for line in lines[-100:]:
        try:
            event = json.loads(line.strip())
            events.append(event)
        except Exception as e:
            continue
    
    return events

def analyze_with_persona(events: List[Dict], persona_name: str) -> str:
    """페르소나에게 이벤트 분석 요청"""
    # 이벤트 요약 생성
    total_events = len(events)
    health_checks = sum(1 for e in events if e.get('event') == 'health_check')
    all_green_count = sum(1 for e in events if e.get('all_green') == True)
    
    summary = f"""
    최근 24시간 AGI 시스템 활동:
    - 총 이벤트: {total_events}개
    - 건강 체크: {health_checks}회
    - 정상 상태: {all_green_count}회
    
    {persona_name}, 이 데이터를 분석하고 시스템 개선을 위한 핵심 제안 1가지를 간단히 제시해주세요.
    """
    
    payload = {"message": summary.strip()}
    
    try:
        response = requests.post(
            LUMEN_GATEWAY,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result.get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

def save_feedback(persona: str, feedback: str, timestamp: str):
    """페르소나 피드백 저장"""
    output_file = OUTPUT_DIR / "resonance_lumen_feedback.jsonl"
    
    entry = {
        "timestamp": timestamp,
        "persona": persona,
        "feedback": feedback,
        "integrated": False
    }
    
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ 피드백 저장: {output_file}")

def main():
    print("\n🎯 Resonance Loop + 루멘 통합\n")
    print("=" * 60)
    
    # 1. 최근 이벤트 수집
    print("\n1️⃣ Resonance Ledger에서 최근 이벤트 수집...")
    events = read_recent_events(hours=24)
    print(f"   수집된 이벤트: {len(events)}개")
    
    if len(events) == 0:
        print("   ⚠️ 분석할 이벤트가 없습니다.")
        return
    
    # 2. 세나에게 분석 요청
    print("\n2️⃣ 세나 (✒️)에게 분석 요청...")
    feedback = analyze_with_persona(events, "세나")
    print(f"\n   세나의 피드백:\n   {feedback[:200]}...")
    
    # 3. 피드백 저장
    print("\n3️⃣ 피드백 저장...")
    timestamp = datetime.now().isoformat()
    save_feedback("세나", feedback, timestamp)
    
    # 4. 요약 리포트 생성
    print("\n4️⃣ 통합 리포트 생성...")
    report_file = OUTPUT_DIR / "resonance_lumen_integration_latest.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Resonance Loop + 루멘 통합 리포트

**생성 시각**: {timestamp}

## 📊 시스템 활동 분석

- **분석 기간**: 최근 24시간
- **총 이벤트**: {len(events)}개
- **분석 페르소나**: 세나 (✒️)

## 💡 페르소나 피드백

{feedback}

## 🔄 다음 단계

1. 피드백 검토 및 우선순위 결정
2. 개선 사항 구현 계획 수립
3. 자동 반영 메커니즘 활성화

---

*이 리포트는 Resonance Loop + 루멘 통합 시스템에 의해 자동 생성되었습니다.*
""")
    
    print(f"   리포트 저장: {report_file}")
    
    print("\n" + "=" * 60)
    print("🎊 Resonance Loop + 루멘 통합 완료!\n")
    print(f"📋 리포트: {report_file}")
    print(f"📝 피드백 로그: {OUTPUT_DIR / 'resonance_lumen_feedback.jsonl'}")

if __name__ == "__main__":
    main()
