#!/usr/bin/env python3
"""
음악 패턴과 리듬 상태 상관관계 분석기
Music Pattern & Rhythm State Correlator

음악 라이브러리의 리듬 상태 태그를 현재 시스템 리듬 상태와 연결하여
자동 음악 추천 및 분위기 매칭을 제공합니다.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

WORKSPACE = Path(__file__).parent.parent
MUSIC_PATTERN = WORKSPACE / "outputs" / "music_pattern_analysis.json"
RHYTHM_STATUS = WORKSPACE / "outputs" / "RHYTHM_SYSTEM_STATUS_REPORT.md"
SELF_CARE = WORKSPACE / "outputs" / "self_care_metrics_summary.json"
OUTPUT_JSON = WORKSPACE / "outputs" / "music_rhythm_correlation_latest.json"
OUTPUT_MD = WORKSPACE / "outputs" / "music_rhythm_correlation_latest.md"


def load_music_patterns() -> Dict[str, Any]:
    """음악 패턴 분석 데이터 로드"""
    if not MUSIC_PATTERN.exists():
        return {}
    
    with open(MUSIC_PATTERN, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_current_rhythm_state() -> str:
    """현재 리듬 상태 감지 (파일 기반)"""
    # 1. RHYTHM 파일들 확인
    rhythm_files = list(WORKSPACE.glob("outputs/RHYTHM_*_PHASE_*.md"))
    
    if rhythm_files:
        latest = max(rhythm_files, key=lambda p: p.stat().st_mtime)
        name = latest.stem.lower()
        
        if 'rest' in name or 'resting' in name:
            return 'resting'
        elif 'deep_rest' in name:
            return 'deep_rest'
        elif 'focus' in name or 'learning' in name:
            return 'learning'
        elif 'flow' in name:
            return 'flow'
    
    # 2. Self-Care 메트릭 확인
    if SELF_CARE.exists():
        with open(SELF_CARE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            stagnation = data.get('stagnation_avg', 0)
            
            if stagnation > 0.5:
                return 'deep_rest'  # 높은 정체 → 깊은 휴식 필요
            elif stagnation > 0.3:
                return 'resting'    # 중간 정체 → 휴식
            else:
                return 'learning'   # 낮은 정체 → 활동 가능
    
    return 'unknown'


def correlate_music_with_rhythm(
    music_data: Dict[str, Any],
    current_state: str
) -> Dict[str, Any]:
    """음악 패턴과 리듬 상태 상관관계 분석"""
    
    patterns = music_data.get('patterns', {})
    rhythm_counts = patterns.get('by_rhythm_state', {})
    theme_groups = patterns.get('by_theme', {})
    creator_groups = patterns.get('by_creators', {})
    
    # 현재 상태와 일치하는 음악 개수
    matching_count = rhythm_counts.get(current_state, 0)
    
    # 추천 음악 생성 (실제 파일명은 없으므로 count만 사용)
    recommendations = []
    if matching_count > 0:
        recommendations.append({
            'count': matching_count,
            'reason': f'리듬 상태 일치: {current_state}'
        })
    
    # 테마별 대안 추천 (count만)
    theme_recommendations = {
        theme: count
        for theme, count in theme_groups.items()
        if count > 0
    }
    
    # 통계
    total_music = music_data.get('total_files', 0)
    match_rate = (matching_count / total_music * 100) if total_music > 0 else 0
    
    return {
        'current_rhythm_state': current_state,
        'total_music_library': total_music,
        'matching_music_count': matching_count,
        'match_rate_percent': round(match_rate, 1),
        'direct_recommendations': recommendations,
        'theme_recommendations': theme_recommendations,
        'rhythm_distribution': rhythm_counts,
        'creator_distribution': creator_groups,
        'generated_at': datetime.now().isoformat()
    }


def generate_markdown_report(correlation: Dict[str, Any]) -> str:
    """마크다운 리포트 생성"""
    
    lines = [
        "# 🎵 음악-리듬 상관관계 리포트",
        "",
        f"**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 현재 상태",
        "",
        f"- **현재 리듬**: `{correlation['current_rhythm_state']}`",
        f"- **전체 음악 라이브러리**: {correlation['total_music_library']}곡",
        f"- **일치하는 음악**: {correlation['matching_music_count']}곡 ({correlation['match_rate_percent']}%)",
        "",
        "## 🎧 직접 추천 (현재 리듬에 맞는 음악)",
        ""
    ]
    
    recommendations = correlation.get('direct_recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. **{rec['count']}곡 available**")
            lines.append(f"   - 이유: {rec['reason']}")
            lines.append("")
    else:
        lines.append("*현재 상태와 일치하는 음악이 없습니다.*")
        lines.append("")
    
    # 테마별 추천
    lines.extend([
        "## 🎨 테마별 음악 분포",
        ""
    ])
    
    theme_recs = correlation.get('theme_recommendations', {})
    for theme, count in sorted(theme_recs.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- **{theme}**: {count}곡")
    
    # 리듬 분포
    lines.extend([
        "## 📊 리듬 상태 분포",
        ""
    ])
    
    distribution = correlation.get('rhythm_distribution', {})
    for state, count in sorted(distribution.items(), key=lambda x: -x[1]):
        lines.append(f"- **{state}**: {count}곡")
    
    lines.extend([
        "",
        "---",
        "*자동 생성: music_rhythm_correlator.py*"
    ])
    
    return "\n".join(lines)


def main():
    print("🎵 음악-리듬 상관관계 분석 시작...")
    
    # 1. 데이터 로드
    music_data = load_music_patterns()
    if not music_data:
        print("❌ 음악 패턴 데이터를 찾을 수 없습니다.")
        print(f"   예상 경로: {MUSIC_PATTERN}")
        return 1
    
    print(f"✅ 음악 라이브러리 로드: {music_data.get('total_files', 0)}곡")
    
    # 2. 현재 리듬 상태 감지
    current_state = detect_current_rhythm_state()
    print(f"🌊 현재 리듬 상태: {current_state}")
    
    # 3. 상관관계 분석
    correlation = correlate_music_with_rhythm(music_data, current_state)
    
    # 4. JSON 저장
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(correlation, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON 저장: {OUTPUT_JSON}")
    
    # 5. 마크다운 리포트 생성
    markdown = generate_markdown_report(correlation)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"📄 Markdown 저장: {OUTPUT_MD}")
    
    # 6. 요약 출력
    print("\n📊 분석 결과:")
    print(f"   - 일치하는 음악: {correlation['matching_music_count']}곡")
    print(f"   - 추천 가능: {len(correlation['direct_recommendations'])}개")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
