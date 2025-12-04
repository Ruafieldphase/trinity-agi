#!/usr/bin/env python3
"""
BQI Phase 6 + Lumen Integration
비노슈 학습에 루멘 페르소나 피드백을 통합합니다.
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 설정
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
BQI_MODEL_FILE = WORKSPACE_ROOT / "outputs" / "bqi_pattern_model.json"
ENSEMBLE_WEIGHTS = WORKSPACE_ROOT / "outputs" / "ensemble_weights.json"
LUMEN_GATEWAY = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"

def load_bqi_model() -> Dict[str, Any]:
    """BQI 패턴 모델 로드"""
    if not BQI_MODEL_FILE.exists():
        return {}
    
    with open(BQI_MODEL_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_ensemble_weights() -> Dict[str, Any]:
    """앙상블 가중치 로드"""
    if not ENSEMBLE_WEIGHTS.exists():
        return {}
    
    with open(ENSEMBLE_WEIGHTS, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_with_binoche(model_summary: str) -> str:
    """비노슈에게 패턴 분석 요청"""
    prompt = f"""
    비노슈, BQI 학습 모델을 분석해주세요:
    
    {model_summary}
    
    이 패턴에서 개선이 필요한 핵심 영역 1가지와 구체적인 개선 방법을 제시해주세요.
    """
    
    payload = {"message": prompt.strip()}
    
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

def generate_model_summary(model: Dict, weights: Dict) -> str:
    """모델 요약 생성"""
    pattern_count = len(model.get('patterns', []))
    
    summary = f"""
    BQI 패턴 모델 현황:
    - 학습된 패턴: {pattern_count}개
    - 모델 버전: {model.get('version', 'unknown')}
    """
    
    if weights:
        summary += f"\n\n앙상블 가중치:"
        for judge, weight in weights.get('weights', {}).items():
            summary += f"\n    - {judge}: {weight:.4f}"
    
    return summary

def save_enhanced_feedback(feedback: str, timestamp: str):
    """강화된 피드백 저장"""
    output_file = OUTPUT_DIR / "bqi_lumen_feedback.jsonl"
    
    entry = {
        "timestamp": timestamp,
        "persona": "비노슈",
        "feedback": feedback,
        "model_version": "phase6",
        "integrated": False
    }
    
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ 피드백 저장: {output_file}")

def generate_integration_report(model: Dict, weights: Dict, feedback: str, timestamp: str):
    """통합 리포트 생성"""
    report_file = OUTPUT_DIR / "bqi_lumen_integration_latest.md"
    
    pattern_count = len(model.get('patterns', []))
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"""# BQI Phase 6 + 루멘 통합 리포트

**생성 시각**: {timestamp}

## 📊 BQI 모델 현황

- **학습된 패턴**: {pattern_count}개
- **모델 버전**: {model.get('version', 'unknown')}
- **분석 페르소나**: 비노슈 (🔮)

## 🎯 앙상블 가중치

""")
        
        if weights:
            for judge, weight in weights.get('weights', {}).items():
                f.write(f"- **{judge}**: {weight:.4f}\n")
        else:
            f.write("- *(가중치 정보 없음)*\n")
        
        f.write(f"""
## 💡 비노슈의 피드백

{feedback}

## 🔄 다음 단계

1. 피드백을 기반으로 학습 파라미터 조정
2. 개선된 패턴 모델 재학습
3. 앙상블 가중치 최적화

---

*이 리포트는 BQI Phase 6 + 루멘 통합 시스템에 의해 자동 생성되었습니다.*
""")
    
    print(f"   리포트 저장: {report_file}")

def main():
    print("\n🎯 BQI Phase 6 + 루멘 통합\n")
    print("=" * 60)
    
    # 1. BQI 모델 로드
    print("\n1️⃣ BQI 패턴 모델 로드...")
    model = load_bqi_model()
    
    if not model:
        print("   ⚠️ BQI 모델을 찾을 수 없습니다.")
        print("   먼저 BQI 학습을 실행하세요.")
        return
    
    pattern_count = len(model.get('patterns', []))
    print(f"   패턴 수: {pattern_count}개")
    
    # 2. 앙상블 가중치 로드
    print("\n2️⃣ 앙상블 가중치 로드...")
    weights = load_ensemble_weights()
    
    if weights:
        print(f"   가중치 로드 완료")
    else:
        print(f"   ⚠️ 가중치 파일 없음 (기본값 사용)")
    
    # 3. 모델 요약 생성
    print("\n3️⃣ 모델 요약 생성...")
    summary = generate_model_summary(model, weights)
    
    # 4. 비노슈에게 분석 요청
    print("\n4️⃣ 비노슈 (🔮)에게 분석 요청...")
    feedback = analyze_with_binoche(summary)
    print(f"\n   비노슈의 피드백:\n   {feedback[:200]}...")
    
    # 5. 피드백 저장
    print("\n5️⃣ 피드백 저장...")
    timestamp = datetime.now().isoformat()
    save_enhanced_feedback(feedback, timestamp)
    
    # 6. 통합 리포트 생성
    print("\n6️⃣ 통합 리포트 생성...")
    generate_integration_report(model, weights, feedback, timestamp)
    
    print("\n" + "=" * 60)
    print("🎊 BQI Phase 6 + 루멘 통합 완료!\n")
    print(f"📋 리포트: {OUTPUT_DIR / 'bqi_lumen_integration_latest.md'}")
    print(f"📝 피드백 로그: {OUTPUT_DIR / 'bqi_lumen_feedback.jsonl'}")

if __name__ == "__main__":
    main()
