#!/usr/bin/env python3
"""
Intelligent Feedback Applicator
페르소나 피드백을 이해하고 실행 가능한 코드 변경을 생성합니다.
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 설정
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"
LUMEN_GATEWAY = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"

class IntelligentApplicator:
    """지능형 피드백 적용기"""
    
    def __init__(self):
        self.feedback_sources = [
            WORKSPACE_ROOT / "fdo_agi_repo" / "outputs" / "resonance_lumen_integration_latest.md",
            WORKSPACE_ROOT / "fdo_agi_repo" / "outputs" / "bqi_lumen_integration_latest.md",
        ]
    
    def collect_feedback(self) -> List[str]:
        """피드백 수집"""
        feedbacks = []
        
        for source in self.feedback_sources:
            if not source.exists():
                continue
            
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # "핵심 제안" 섹션 추출
            if "핵심 제안:" in content or "제안:" in content:
                feedbacks.append(content)
        
        return feedbacks
    
    def ask_persona_for_implementation(self, feedback_text: str) -> str:
        """페르소나에게 구현 방안 문의"""
        
        prompt = f"""루빗, 다음 피드백을 실제로 구현하려면 어떤 코드/설정을 변경해야 할까요?

피드백:
{feedback_text[:500]}

구체적인 구현 방안을 3가지 이내로 제시해주세요:
1. 설정 파일 경로
2. 변경할 파라미터
3. 권장 값
"""
        
        payload = {"message": prompt}
        
        try:
            response = requests.post(
                LUMEN_GATEWAY,
                json=payload,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_implementation_plan(self, feedbacks: List[str]) -> Dict[str, Any]:
        """구현 계획 생성"""
        plan = {
            "timestamp": datetime.now().isoformat(),
            "feedbacks_analyzed": len(feedbacks),
            "implementation_steps": [],
        }
        
        for i, feedback in enumerate(feedbacks, 1):
            print(f"\n  📋 피드백 {i} 분석 중...")
            
            # 페르소나에게 구현 방안 문의
            implementation = self.ask_persona_for_implementation(feedback)
            
            step = {
                "feedback_summary": feedback[:200] + "...",
                "implementation_advice": implementation[:300] + "...",
                "status": "planned",
            }
            
            plan["implementation_steps"].append(step)
            
            print(f"     ✅ 구현 방안 수집 완료")
        
        return plan

def main():
    print("\n🧠 지능형 피드백 적용 시스템\n")
    print("=" * 60)
    
    applicator = IntelligentApplicator()
    
    # 1. 피드백 수집
    print("\n1️⃣ 페르소나 피드백 수집...")
    feedbacks = applicator.collect_feedback()
    print(f"   수집된 피드백: {len(feedbacks)}개")
    
    if not feedbacks:
        print("\n⚠️ 피드백이 없습니다.")
        return
    
    # 2. 구현 계획 생성
    print("\n2️⃣ 루빗에게 구현 방안 문의...")
    plan = applicator.generate_implementation_plan(feedbacks)
    
    # 3. 계획 저장
    print("\n3️⃣ 구현 계획 저장...")
    
    # JSON 저장
    json_file = OUTPUT_DIR / "feedback_implementation_plan.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"   ✅ JSON: {json_file}")
    
    # 마크다운 리포트
    md_file = OUTPUT_DIR / "feedback_implementation_plan.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"""# 피드백 구현 계획

**생성 시각**: {plan['timestamp']}

## 📊 요약

- **분석된 피드백**: {plan['feedbacks_analyzed']}개
- **구현 단계**: {len(plan['implementation_steps'])}개

---

## 🔧 구현 단계

""")
        
        for i, step in enumerate(plan['implementation_steps'], 1):
            f.write(f"""### 단계 {i}

**피드백 요약**:
{step['feedback_summary']}

**구현 방안** (루빗의 조언):
{step['implementation_advice']}

**상태**: {step['status']}

---

""")
        
        f.write("\n*이 계획은 지능형 피드백 적용 시스템에 의해 생성되었습니다.*\n")
    
    print(f"   ✅ 리포트: {md_file}")
    
    print("\n" + "=" * 60)
    print("🎊 구현 계획 생성 완료!\n")
    
    print(f"📋 총 {plan['feedbacks_analyzed']}개 피드백 분석")
    print(f"🔧 {len(plan['implementation_steps'])}개 구현 단계 생성\n")
    
    print("💡 다음 단계:")
    print("  1. 리포트 검토")
    print("  2. 안전한 변경 사항 선택")
    print("  3. 수동 또는 자동 적용\n")

if __name__ == "__main__":
    main()
