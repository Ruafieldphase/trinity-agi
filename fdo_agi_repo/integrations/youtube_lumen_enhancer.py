#!/usr/bin/env python3
"""
YouTube Learning + Lumen Enhancement
YouTube 영상 분석 결과에 루멘 페르소나 인사이트를 통합합니다.
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 설정
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
YOUTUBE_OUTPUT_DIR = WORKSPACE_ROOT / "fdo_agi_repo" / "outputs" / "youtube_learner"
LUMEN_GATEWAY = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"

def find_latest_youtube_analysis() -> Path:
    """최신 YouTube 분석 결과 찾기"""
    if not YOUTUBE_OUTPUT_DIR.exists():
        raise FileNotFoundError(f"YouTube output directory not found: {YOUTUBE_OUTPUT_DIR}")
    
    json_files = list(YOUTUBE_OUTPUT_DIR.glob("*_analysis.json"))
    if not json_files:
        raise FileNotFoundError("No YouTube analysis files found")
    
    latest = max(json_files, key=lambda p: p.stat().st_mtime)
    return latest

def load_youtube_analysis(file_path: Path) -> Dict[str, Any]:
    """YouTube 분석 결과 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_analysis_summary(data: Dict[str, Any]) -> str:
    """분석 결과 요약 생성"""
    title = data.get('title', 'Unknown')
    duration = data.get('duration', 0)
    duration_min = int(duration / 60)
    
    # 자막 샘플 추출 (처음 10개)
    subtitles = data.get('subtitles', [])[:10]
    subtitle_text = " ".join([s.get('text', '') for s in subtitles])
    
    summary = f"""
YouTube 영상 분석 결과:

제목: {title}
길이: {duration_min}분
자막 샘플: {subtitle_text[:300]}...

이 영상의 핵심 주제와 학습 가치를 3문장으로 요약해주세요.
"""
    
    return summary.strip()

def query_persona(persona_name: str, analysis_summary: str) -> str:
    """페르소나에게 분석 요청"""
    prompt = f"{persona_name}, {analysis_summary}"
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
        return result.get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

def enhance_with_personas(data: Dict[str, Any]) -> Dict[str, Any]:
    """페르소나 인사이트로 분석 강화"""
    print("\n1️⃣ 분석 요약 생성...")
    summary = generate_analysis_summary(data)
    
    print("\n2️⃣ 세나 (✒️)에게 학습 가치 분석 요청...")
    sena_insight = query_persona("세나", summary)
    print(f"   응답: {sena_insight[:100]}...")
    
    print("\n3️⃣ 루빗 (🪨)에게 실용적 적용 방법 요청...")
    rubit_prompt = f"{summary}\n\n이 지식을 실제로 어떻게 활용할 수 있는지 2가지 방법을 제시해주세요."
    rubit_insight = query_persona("루빗", rubit_prompt)
    print(f"   응답: {rubit_insight[:100]}...")
    
    # 강화된 데이터 생성
    enhanced = {
        "original_data": {
            "video_id": data.get('video_id'),
            "title": data.get('title'),
            "duration": data.get('duration'),
            "subtitles_count": data.get('subtitles_count', 0)
        },
        "timestamp": datetime.now().isoformat(),
        "lumen_insights": {
            "sena_learning_value": sena_insight,
            "rubit_practical_application": rubit_insight
        }
    }
    
    return enhanced

def save_enhanced_result(enhanced: Dict[str, Any], video_id: str):
    """강화된 결과 저장"""
    # JSON 저장
    json_file = OUTPUT_DIR / f"youtube_enhanced_{video_id}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON 저장: {json_file}")
    
    # 마크다운 리포트 생성
    md_file = OUTPUT_DIR / f"youtube_enhanced_{video_id}.md"
    
    with open(md_file, 'w', encoding='utf-8') as f:
        original = enhanced['original_data']
        insights = enhanced['lumen_insights']
        duration_min = int(original['duration'] / 60)
        
        f.write(f"""# YouTube 학습 강화 리포트

**생성 시각**: {enhanced['timestamp']}

## 📺 영상 정보

- **제목**: {original['title']}
- **길이**: {duration_min}분
- **자막 수**: {original['subtitles_count']}개

---

## 💡 세나 (✒️) - 학습 가치 분석

{insights['sena_learning_value']}

---

## 🔧 루빗 (🪨) - 실용적 적용 방법

{insights['rubit_practical_application']}

---

*이 리포트는 YouTube + 루멘 통합 시스템에 의해 자동 생성되었습니다.*
""")
    
    print(f"✅ 리포트 저장: {md_file}")

def main():
    print("\n🎬 YouTube 학습 + 루멘 강화\n")
    print("=" * 60)
    
    # 1. 최신 분석 파일 찾기
    print("\n1️⃣ 최신 YouTube 분석 찾기...")
    try:
        latest_file = find_latest_youtube_analysis()
        print(f"   파일: {latest_file.name}")
    except FileNotFoundError as e:
        print(f"   ⚠️ {e}")
        return
    
    # 2. 분석 데이터 로드
    print("\n2️⃣ 분석 데이터 로드...")
    data = load_youtube_analysis(latest_file)
    print(f"   제목: {data.get('title', 'Unknown')[:60]}...")
    
    # 3. 페르소나 인사이트로 강화
    print("\n3️⃣ 페르소나 인사이트 추출...")
    enhanced = enhance_with_personas(data)
    
    # 4. 결과 저장
    print("\n4️⃣ 강화된 결과 저장...")
    video_id = data.get('video_id', 'unknown')
    save_enhanced_result(enhanced, video_id)
    
    print("\n" + "=" * 60)
    print("🎊 YouTube 학습 강화 완료!\n")
    print(f"📋 리포트: {OUTPUT_DIR / f'youtube_enhanced_{video_id}.md'}")
    print(f"📝 JSON: {OUTPUT_DIR / f'youtube_enhanced_{video_id}.json'}")

if __name__ == "__main__":
    main()
