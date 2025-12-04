#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Program Learning Agent
사용자의 프로그램 사용 패턴을 학습하고 자동화하는 에이전트
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "fdo_agi_repo"))

try:
    import pygetwindow as gw
    import pyautogui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    print("⚠️ pygetwindow/pyautogui not available. GUI features disabled.")


class SenaCache:
    """간단한 메모리 캐시 (Sena Cache 호환)"""
    
    def __init__(self):
        self.cache = {}
        self.expiry = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key not in self.cache:
            return None
        
        if time.time() > self.expiry.get(key, 0):
            # 만료됨
            del self.cache[key]
            del self.expiry[key]
            return None
        
        return self.cache[key]
    
    def delete(self, key: str):
        """캐시에서 값 삭제"""
        self.cache.pop(key, None)
        self.expiry.pop(key, None)


class ProgramLearningAgent:
    """프로그램 사용 패턴 학습 및 자동화 에이전트"""
    
    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or (project_root / "fdo_agi_repo" / "memory" / "program_patterns")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache = SenaCache()
        self.patterns_file = self.memory_dir / "learned_patterns.jsonl"
        self.metadata_file = self.memory_dir / "program_metadata.json"
        
        # 학습된 패턴 로드
        self.patterns = self._load_patterns()
        self.metadata = self._load_metadata()
    
    def _load_patterns(self) -> List[Dict]:
        """학습된 패턴 로드"""
        if not self.patterns_file.exists():
            return []
        
        patterns = []
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    patterns.append(json.loads(line))
        return patterns
    
    def _load_metadata(self) -> Dict:
        """프로그램 메타데이터 로드"""
        if not self.metadata_file.exists():
            return {}
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_pattern(self, pattern: Dict):
        """패턴 저장"""
        with open(self.patterns_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pattern, ensure_ascii=False) + '\n')
        
        self.patterns.append(pattern)
    
    def _save_metadata(self):
        """메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def extract_metadata(self, program: str) -> Dict[str, Any]:
        """프로그램 메타데이터 추출"""
        metadata = {
            "program": program,
            "timestamp": datetime.now().isoformat(),
            "window_title": None,
            "window_size": None,
            "state": "unknown"
        }
        
        if not HAS_GUI:
            return metadata
        
        try:
            # 활성 창 찾기
            windows = gw.getWindowsWithTitle(program)
            if windows:
                win = windows[0]
                metadata.update({
                    "window_title": win.title,
                    "window_size": (win.width, win.height),
                    "state": "active" if win.isActive else "background"
                })
        except Exception as e:
            print(f"⚠️ 메타데이터 추출 실패: {e}")
        
        return metadata
    
    def learn_pattern(self, interaction: Dict):
        """사용자 인터랙션 패턴 학습"""
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "program": interaction.get("program"),
            "action": interaction.get("action"),
            "context": interaction.get("context", {}),
            "success": interaction.get("success", True)
        }
        
        self._save_pattern(pattern)
        
        # Sena 캐시에도 저장
        cache_key = f"program_pattern_{pattern['program']}_{int(time.time())}"
        self.cache.set(cache_key, pattern, ttl=86400 * 7)  # 7일
        
        return pattern
    
    def analyze_patterns(self, program: str, hours: int = 24) -> List[Dict]:
        """특정 프로그램의 패턴 분석"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        relevant = []
        for pattern in self.patterns:
            ts = datetime.fromisoformat(pattern["timestamp"])
            if ts >= cutoff and pattern.get("program") == program:
                relevant.append(pattern)
        
        return relevant
    
    def suggest_automation(self, program: str) -> Dict[str, Any]:
        """자동화 제안 생성"""
        patterns = self.analyze_patterns(program, hours=24*7)  # 최근 7일
        
        if not patterns:
            return {
                "program": program,
                "suggestions": [],
                "confidence": 0.0
            }
        
        # 패턴 빈도 분석
        action_freq = {}
        for p in patterns:
            action = p.get("action")
            if action:
                action_freq[action] = action_freq.get(action, 0) + 1
        
        # 상위 3개 액션
        top_actions = sorted(action_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        suggestions = []
        for action, count in top_actions:
            suggestions.append({
                "action": action,
                "frequency": count,
                "confidence": count / len(patterns),
                "automation_feasible": count >= 3  # 3회 이상 반복 시 자동화 가능
            })
        
        return {
            "program": program,
            "total_patterns": len(patterns),
            "suggestions": suggestions,
            "confidence": len(patterns) / max(len(self.patterns), 1)
        }
    
    def save_to_cache(self, data: Dict, ttl: int = 86400) -> str:
        """Sena 캐시에 저장"""
        key = f"program_learning_{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()}"
        self.cache.set(key, data, ttl=ttl)
        return key
    
    def load_from_cache(self, key: str) -> Optional[Dict]:
        """Sena 캐시에서 로드"""
        return self.cache.get(key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        programs = {}
        for pattern in self.patterns:
            prog = pattern.get("program")
            if prog:
                programs[prog] = programs.get(prog, 0) + 1
        
        return {
            "total_patterns": len(self.patterns),
            "unique_programs": len(programs),
            "top_programs": sorted(programs.items(), key=lambda x: x[1], reverse=True)[:5],
            "oldest_pattern": self.patterns[0]["timestamp"] if self.patterns else None,
            "newest_pattern": self.patterns[-1]["timestamp"] if self.patterns else None
        }


def main():
    """CLI 메인 진입점"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Program Learning Agent")
    parser.add_argument("--program", help="프로그램 이름")
    parser.add_argument("--mode", choices=["learn", "analyze", "suggest", "stats"], 
                       default="stats", help="실행 모드")
    parser.add_argument("--hours", type=int, default=24, help="분석 기간 (시간)")
    
    args = parser.parse_args()
    
    agent = ProgramLearningAgent()
    
    if args.mode == "stats":
        stats = agent.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.mode == "analyze" and args.program:
        patterns = agent.analyze_patterns(args.program, hours=args.hours)
        print(f"\n📊 {args.program} 패턴 분석 (최근 {args.hours}시간)")
        print(f"총 {len(patterns)}개 패턴 발견")
        print(json.dumps(patterns, indent=2, ensure_ascii=False))
    
    elif args.mode == "suggest" and args.program:
        suggestions = agent.suggest_automation(args.program)
        print(f"\n💡 {args.program} 자동화 제안")
        print(json.dumps(suggestions, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
