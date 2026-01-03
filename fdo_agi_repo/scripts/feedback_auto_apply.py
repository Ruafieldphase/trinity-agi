#!/usr/bin/env python3
"""
Feedback Auto-Apply System
페르소나 피드백을 분석하여 실행 가능한 개선 사항을 자동으로 적용합니다.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# 설정
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"

# 피드백 소스
FEEDBACK_SOURCES = {
    "resonance": WORKSPACE_ROOT / "fdo_agi_repo" / "outputs" / "resonance_core_integration_latest.md",
    "bqi": WORKSPACE_ROOT / "fdo_agi_repo" / "outputs" / "bqi_core_integration_latest.md",
    "orchestration": OUTPUT_DIR / "orchestration_latest.md",
}

# 안전하게 적용 가능한 액션 타입
SAFE_ACTION_TYPES = [
    "config_update",      # 설정 파일 업데이트
    "threshold_adjust",   # 임계값 조정
    "interval_change",    # 주기 변경
    "log_level",          # 로그 레벨 조정
    "documentation",      # 문서 업데이트
]

class FeedbackParser:
    """페르소나 피드백 파싱"""
    
    def __init__(self):
        self.patterns = {
            "config_update": r"(?:설정|config|configuration).*?(?:변경|수정|업데이트|adjust|modify)",
            "threshold_adjust": r"(?:임계값|threshold).*?(\d+(?:\.\d+)?)",
            "interval_change": r"(?:주기|interval).*?(\d+).*?(?:분|초|시간|minute|second|hour)",
            "efficiency": r"(?:효율|efficiency|optimization).*?(\d+(?:\.\d+)?%)",
        }
    
    def extract_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 제안 추출"""
        suggestions = []
        
        # 번호가 있는 리스트 항목 찾기
        list_items = re.findall(r'(?:^\s*[\d\-\*•]+\.?\s+)(.+)', text, re.MULTILINE)
        
        for item in list_items:
            suggestion = self._parse_suggestion(item)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _parse_suggestion(self, text: str) -> Dict[str, Any]:
        """개별 제안 파싱"""
        suggestion = {
            "text": text.strip(),
            "action_type": None,
            "parameters": {},
            "confidence": 0.0,
            "safe": False,
        }
        
        # 액션 타입 감지
        for action_type, pattern in self.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                suggestion["action_type"] = action_type
                suggestion["confidence"] = 0.7
                
                # 파라미터 추출
                if action_type == "threshold_adjust":
                    match = re.search(r'(\d+(?:\.\d+)?)', text)
                    if match:
                        suggestion["parameters"]["value"] = float(match.group(1))
                
                elif action_type == "interval_change":
                    match = re.search(r'(\d+)\s*(?:분|초|시간|minute|second|hour)', text)
                    if match:
                        suggestion["parameters"]["value"] = int(match.group(1))
                        # 단위 추출
                        unit_match = re.search(r'(?:분|minute)', text)
                        if unit_match:
                            suggestion["parameters"]["unit"] = "minutes"
                
                break
        
        # 안전성 체크
        if suggestion["action_type"] in SAFE_ACTION_TYPES:
            suggestion["safe"] = True
        
        return suggestion if suggestion["action_type"] else None

class FeedbackCollector:
    """피드백 수집"""
    
    def __init__(self):
        self.parser = FeedbackParser()
    
    def collect_all_feedback(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 소스에서 피드백 수집"""
        all_feedback = {}
        
        for source_name, file_path in FEEDBACK_SOURCES.items():
            if not file_path.exists():
                print(f"  ⚠️ {source_name}: 파일 없음")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                suggestions = self.parser.extract_suggestions(content)
                all_feedback[source_name] = suggestions
                
                print(f"  ✅ {source_name}: {len(suggestions)}개 제안 추출")
                
            except Exception as e:
                print(f"  ❌ {source_name}: 오류 - {e}")
        
        return all_feedback

class ActionApplicator:
    """액션 적용"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.applied_actions = []
    
    def apply_suggestions(self, feedback: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """제안 적용"""
        results = []
        
        for source, suggestions in feedback.items():
            safe_suggestions = [s for s in suggestions if s.get("safe", False)]
            
            print(f"\n  📋 {source}: {len(safe_suggestions)}개 안전한 제안")
            
            for suggestion in safe_suggestions:
                result = self._apply_single(source, suggestion)
                results.append(result)
        
        return results
    
    def _apply_single(self, source: str, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """단일 제안 적용"""
        action_type = suggestion["action_type"]
        
        print(f"\n    🔧 {action_type}: {suggestion['text'][:60]}...")
        
        if self.dry_run:
            print(f"       [DRY-RUN] 적용 시뮬레이션")
            status = "simulated"
        else:
            # 실제 적용 로직 (현재는 시뮬레이션)
            status = "applied"
        
        result = {
            "source": source,
            "action_type": action_type,
            "suggestion": suggestion["text"],
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.applied_actions.append(result)
        return result

def generate_report(feedback: Dict[str, List[Dict[str, Any]]], 
                   results: List[Dict[str, Any]]) -> str:
    """적용 리포트 생성"""
    total_suggestions = sum(len(s) for s in feedback.values())
    safe_suggestions = sum(1 for r in results)
    
    report = f"""# 피드백 자동 반영 리포트

**생성 시각**: {datetime.now().isoformat()}

## 📊 요약

- **수집된 제안**: {total_suggestions}개
- **안전한 제안**: {safe_suggestions}개
- **적용 완료**: {len([r for r in results if r['status'] == 'applied'])}개
- **시뮬레이션**: {len([r for r in results if r['status'] == 'simulated'])}개

---

## 🔍 소스별 분석

"""
    
    for source, suggestions in feedback.items():
        report += f"\n### {source.upper()}\n\n"
        report += f"- 총 제안: {len(suggestions)}개\n"
        
        safe = [s for s in suggestions if s.get("safe", False)]
        report += f"- 안전한 제안: {len(safe)}개\n\n"
        
        if safe:
            report += "**주요 제안:**\n\n"
            for s in safe[:3]:  # 상위 3개
                report += f"- {s['text'][:100]}...\n"
    
    report += "\n---\n\n## ✅ 적용된 액션\n\n"
    
    if results:
        for r in results:
            report += f"### {r['action_type']}\n\n"
            report += f"- **소스**: {r['source']}\n"
            report += f"- **제안**: {r['suggestion'][:100]}...\n"
            report += f"- **상태**: {r['status']}\n"
            report += f"- **시각**: {r['timestamp']}\n\n"
    else:
        report += "*적용된 액션 없음*\n"
    
    report += "\n---\n\n"
    report += "*이 리포트는 피드백 자동 반영 시스템에 의해 생성되었습니다.*\n"
    
    return report

def main():
    print("\n🤖 피드백 자동 반영 시스템\n")
    print("=" * 60)
    
    # 1. 피드백 수집
    print("\n1️⃣ 피드백 수집 중...")
    collector = FeedbackCollector()
    feedback = collector.collect_all_feedback()
    
    if not feedback:
        print("\n⚠️ 수집된 피드백이 없습니다.")
        return
    
    # 2. 액션 적용 (DRY-RUN)
    print("\n2️⃣ 안전한 제안 적용 중 (DRY-RUN)...")
    applicator = ActionApplicator(dry_run=True)
    results = applicator.apply_suggestions(feedback)
    
    # 3. 리포트 생성
    print("\n3️⃣ 리포트 생성 중...")
    report = generate_report(feedback, results)
    
    report_file = OUTPUT_DIR / "feedback_auto_apply_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   ✅ 리포트 저장: {report_file}")
    
    # 4. 결과 JSON 저장
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "feedback_sources": list(feedback.keys()),
        "total_suggestions": sum(len(s) for s in feedback.values()),
        "safe_suggestions": len(results),
        "applied_actions": results,
    }
    
    json_file = OUTPUT_DIR / "feedback_auto_apply_log.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ JSON 저장: {json_file}")
    
    print("\n" + "=" * 60)
    print("🎊 피드백 자동 반영 완료!\n")
    
    # 요약 출력
    print(f"📊 수집: {result_data['total_suggestions']}개")
    print(f"✅ 안전: {result_data['safe_suggestions']}개")
    print(f"🔧 적용: {len([r for r in results if r['status'] == 'applied'])}개\n")

if __name__ == "__main__":
    main()
