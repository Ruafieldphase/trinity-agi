#!/usr/bin/env python3
import os, sys
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root()))
"""
자동화된 오케스트레이션 스크립트
페르소나 협업을 자동으로 실행하고 통합 솔루션을 도출합니다.
"""

import requests
from utils.request_guard import post_json
from utils.validator import core_chat_schema
from utils.atomic_write import atomic_write


import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 설정
CORE_GATEWAY = "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat"
OUTPUT_DIR = get_workspace_root() / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def query_persona(persona_name: str, question: str) -> str:
    """페르소나에게 질문"""
    prompt = f"{persona_name}, {question}"
    payload = {"message": prompt}
    
    try:
        response = post_json(CORE_GATEWAY, payload, schema=core_chat_schema, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

def orchestrate_analysis(topic: str) -> Dict[str, Any]:
    """3단계 오케스트레이션 실행"""
    print(f"\n🎯 주제: {topic}\n")
    print("=" * 60)
    
    results = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "personas": {}
    }
    
    # 1단계: 세나 - 현재 상태 분석
    print("\n1️⃣ 세나 (✒️) - 현재 상태 분석...")
    sena_response = query_persona("세나", f"{topic}에 대한 현재 상태를 분석해주세요.")
    results["personas"]["sena"] = sena_response
    print(f"   응답: {sena_response[:100]}...")
    
    # 2단계: 루빗 - 기술적 접근 방법
    print("\n2️⃣ 루빗 (🪨) - 기술적 접근 방법...")
    rubit_prompt = f"{topic}에 대해, 세나가 다음과 같이 분석했습니다:\n\n{sena_response[:300]}...\n\n3가지 기술적 접근 방법을 제시해주세요."
    rubit_response = query_persona("루빗", rubit_prompt)
    results["personas"]["rubit"] = rubit_response
    print(f"   응답: {rubit_response[:100]}...")
    
    # 3단계: 비노슈 - 통합 권장안
    print("\n3️⃣ 비노슈 (🔮) - 최종 통합 권장안...")
    binoche_prompt = f"""
    {topic}에 대해:
    
    세나의 분석: {sena_response[:200]}...
    루빗의 제안: {rubit_response[:200]}...
    
    이 두 관점을 통합하여 최종 권장안을 제시해주세요.
    """
    binoche_response = query_persona("비노슈", binoche_prompt)
    results["personas"]["Binoche_Observer"] = binoche_response
    print(f"   응답: {binoche_response[:100]}...")
    
    return results

def save_orchestration_result(results: Dict[str, Any]):
    """오케스트레이션 결과 저장"""
    # JSONL 로그
    log_file = OUTPUT_DIR / "orchestration_log.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(results, ensure_ascii=False) + '\n')
    
    # 마크다운 리포트
    report_file = OUTPUT_DIR / "orchestration_latest.md"
    
    report_content = f"""# 오케스트레이션 리포트

**주제**: {results['topic']}
**생성 시각**: {results['timestamp']}

---

## 1️⃣ 세나 (✒️) - 현재 상태 분석

{results['personas'].get('sena', 'N/A')}

---

## 2️⃣ 루빗 (🪨) - 기술적 접근 방법

{results['personas'].get('rubit', 'N/A')}

---

## 3️⃣ 비노슈 (🔮) - 최종 통합 권장안

{results['personas'].get('Binoche_Observer', 'N/A')}

---

*이 리포트는 자동화된 오케스트레이션 시스템에 의해 생성되었습니다.*
"""
    
    atomic_write(str(report_file), report_content)
    
    print(f"\n✅ 결과 저장:")
    print(f"   로그: {log_file}")
    print(f"   리포트: {report_file}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("\n사용법: python auto_orchestration.py '<주제>'")
        print("\n예시:")
        print("  python auto_orchestration.py 'AGI 시스템 최적화 방법'")
        print("  python auto_orchestration.py 'Core 통합 다음 단계'")
        return
    
    topic = " ".join(sys.argv[1:])
    
    print("\n🎭 자동화된 오케스트레이션 시작")
    print("=" * 60)
    
    # 오케스트레이션 실행
    results = orchestrate_analysis(topic)
    
    # 결과 저장
    save_orchestration_result(results)
    
    print("\n" + "=" * 60)
    print("🎊 오케스트레이션 완료!\n")

if __name__ == "__main__":
    main()



