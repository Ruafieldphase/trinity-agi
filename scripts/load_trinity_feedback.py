"""
Trinity 피드백 로더 - 정반합 권장사항을 다른 시스템에 제공

목적:
- Trinity Cycle (Lua → Elo → Lumen) 결과를 읽음
- HIGH 우선순위 권장사항 추출
- Autonomous Goal Generator, Adaptive Rhythm 등에 제공

사용:
    from load_trinity_feedback import load_trinity_high_priority
    
    high_priority_items = load_trinity_high_priority()
    # ["Refactor Core Components", "Improve Documentation", ...]
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def load_trinity_high_priority(
    max_age_hours: int = 48,
    min_priority: str = "HIGH"
) -> List[str]:
    """
    Trinity 권장사항 중 HIGH 우선순위만 추출
    
    Args:
        max_age_hours: 최대 파일 나이 (시간 단위, 기본 48시간)
        min_priority: 최소 우선순위 (HIGH, MEDIUM, LOW)
    
    Returns:
        HIGH 우선순위 권장사항 제목 리스트
    """
    trinity_file = Path(__file__).parent.parent / "outputs" / "trinity_synthesis_latest.json"
    
    if not trinity_file.exists():
        logger.warning(f"Trinity synthesis file not found: {trinity_file}")
        return []
    
    # 파일 나이 체크
    file_age = datetime.now() - datetime.fromtimestamp(trinity_file.stat().st_mtime)
    if file_age > timedelta(hours=max_age_hours):
        logger.warning(
            f"Trinity synthesis file is too old: {file_age.total_seconds() / 3600:.1f}h "
            f"(max: {max_age_hours}h)"
        )
        return []
    
    try:
        data = json.loads(trinity_file.read_text(encoding='utf-8'))
        recommendations = data.get("recommendations", [])
        
        # HIGH 우선순위만 필터링
        priority_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        min_level = priority_levels.get(min_priority, 3)
        
        high_priority = [
            rec["title"]
            for rec in recommendations
            if priority_levels.get(rec.get("priority", "LOW"), 1) >= min_level
        ]
        
        logger.info(
            f"Loaded {len(high_priority)} {min_priority}+ priority recommendations "
            f"from Trinity (age: {file_age.total_seconds() / 3600:.1f}h)"
        )
        
        return high_priority
    
    except Exception as e:
        logger.error(f"Failed to load Trinity feedback: {e}")
        return []


def load_trinity_full_feedback(max_age_hours: int = 48) -> Dict[str, Any]:
    """
    Trinity 전체 피드백 로드 (상세 정보 포함)
    
    Args:
        max_age_hours: 최대 파일 나이 (시간 단위)
    
    Returns:
        Trinity 피드백 전체 딕셔너리
    """
    trinity_file = Path(__file__).parent.parent / "outputs" / "trinity_synthesis_latest.json"
    
    if not trinity_file.exists():
        logger.warning(f"Trinity synthesis file not found: {trinity_file}")
        return {"recommendations": [], "metadata": {"loaded": False}}
    
    # 파일 나이 체크
    file_age = datetime.now() - datetime.fromtimestamp(trinity_file.stat().st_mtime)
    if file_age > timedelta(hours=max_age_hours):
        logger.warning(
            f"Trinity synthesis file is too old: {file_age.total_seconds() / 3600:.1f}h"
        )
        return {"recommendations": [], "metadata": {"loaded": False, "too_old": True}}
    
    try:
        data = json.loads(trinity_file.read_text(encoding='utf-8'))
        data["metadata"] = {
            "loaded": True,
            "file_age_hours": file_age.total_seconds() / 3600,
            "loaded_at": datetime.now().isoformat()
        }
        
        logger.info(f"Loaded full Trinity feedback (age: {file_age.total_seconds() / 3600:.1f}h)")
        return data
    
    except Exception as e:
        logger.error(f"Failed to load Trinity feedback: {e}")
        return {"recommendations": [], "metadata": {"loaded": False, "error": str(e)}}


def get_trinity_urgency_boost(goal_title: str, max_age_hours: int = 48) -> float:
    """
    Trinity 권장사항에 포함된 목표에 대한 긴급도 부스트 계산
    
    Args:
        goal_title: 목표 제목
        max_age_hours: 최대 Trinity 파일 나이
    
    Returns:
        긴급도 부스트 값 (0.0 ~ 5.0)
        - HIGH 우선순위: +3.0
        - MEDIUM 우선순위: +1.5
        - LOW 우선순위: +0.5
        - Trinity 없음: +0.0
    """
    trinity_data = load_trinity_full_feedback(max_age_hours=max_age_hours)
    
    if not trinity_data.get("metadata", {}).get("loaded"):
        return 0.0
    
    recommendations = trinity_data.get("recommendations", [])
    
    # 목표 제목이 Trinity 권장사항에 포함되는지 확인
    for rec in recommendations:
        rec_title = rec.get("title", "")
        
        # 부분 매칭 (키워드 기반)
        keywords = rec_title.lower().split()
        if any(keyword in goal_title.lower() for keyword in keywords if len(keyword) > 3):
            priority = rec.get("priority", "LOW")
            
            boost_map = {
                "HIGH": 3.0,
                "MEDIUM": 1.5,
                "LOW": 0.5
            }
            
            boost = boost_map.get(priority, 0.0)
            logger.info(
                f"Trinity boost for '{goal_title}': +{boost} "
                f"(matched: '{rec_title}', priority: {priority})"
            )
            return boost
    
    return 0.0


def get_session_resonance(max_age_hours: int = 24) -> Optional[float]:
    """
    최근 세션의 Resonance Score 가져오기
    
    Args:
        max_age_hours: 최대 세션 나이 (시간 단위)
    
    Returns:
        Resonance Score (0.0 ~ 1.0) 또는 None
    """
    session_dir = Path(__file__).parent.parent / "outputs" / "session_memory"
    
    if not session_dir.exists():
        logger.warning(f"Session memory directory not found: {session_dir}")
        return None
    
    # 가장 최근 세션 파일 찾기
    session_files = sorted(session_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not session_files:
        logger.warning("No session files found")
        return None
    
    latest_session = session_files[0]
    
    # 파일 나이 체크
    file_age = datetime.now() - datetime.fromtimestamp(latest_session.stat().st_mtime)
    if file_age > timedelta(hours=max_age_hours):
        logger.warning(
            f"Latest session is too old: {file_age.total_seconds() / 3600:.1f}h "
            f"(max: {max_age_hours}h)"
        )
        return None
    
    try:
        data = json.loads(latest_session.read_text(encoding='utf-8'))
        resonance = data.get("resonance_score")
        
        if resonance is not None:
            logger.info(
                f"Loaded session resonance: {resonance:.2f} "
                f"(age: {file_age.total_seconds() / 3600:.1f}h)"
            )
            return float(resonance)
        
        return None
    
    except Exception as e:
        logger.error(f"Failed to load session resonance: {e}")
        return None


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Trinity Feedback Loader Test\n")
    
    # 1. HIGH 우선순위 추출
    high_priority = load_trinity_high_priority()
    print(f"✅ HIGH Priority Recommendations ({len(high_priority)}):")
    for item in high_priority:
        print(f"   - {item}")
    
    print()
    
    # 2. 전체 피드백 로드
    full_data = load_trinity_full_feedback()
    if full_data.get("metadata", {}).get("loaded"):
        print(f"✅ Full Trinity Feedback Loaded:")
        print(f"   - Total recommendations: {len(full_data.get('recommendations', []))}")
        print(f"   - File age: {full_data['metadata']['file_age_hours']:.1f}h")
    else:
        print("❌ Trinity Feedback Not Available")
    
    print()
    
    # 3. 긴급도 부스트 계산
    test_goal = "Refactor Core Components for Better Clarity"
    boost = get_trinity_urgency_boost(test_goal)
    print(f"✅ Urgency Boost for '{test_goal}': +{boost}")
    
    print()
    
    # 4. 세션 Resonance 가져오기
    resonance = get_session_resonance()
    if resonance is not None:
        print(f"✅ Latest Session Resonance: {resonance:.2f}")
    else:
        print("❌ Session Resonance Not Available")
