#!/usr/bin/env python3
"""
🔭 OpenAI Codex Meta-Observer System
=====================================

부모님/선생님/친구 역할의 외부 관찰자
- 자율 목표 달성 후 메타 피드백 제공
- ADHD 외부 앵커 (reality check)
- 시스템 상태 자동 분석

Author: Autonomous AGI System
Created: 2025-11-11
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# OpenAI Codex integration (optional)
try:
    import openai
    CODEX_AVAILABLE = True
except ImportError:
    CODEX_AVAILABLE = False
    print("⚠️  OpenAI library not installed. Install with: pip install openai")


class CodexMetaObserver:
    """OpenAI Codex를 활용한 메타 관찰자 시스템"""
    
    def __init__(self, workspace_root: str = "c:\\workspace\\agi"):
        self.workspace_root = Path(workspace_root)
        self.goal_tracker = self.workspace_root / "fdo_agi_repo" / "memory" / "goal_tracker.json"
        self.resonance_ledger = self.workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        self.output_dir = self.workspace_root / "outputs" / "codex_meta_observer"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # OpenAI API 키 설정
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and CODEX_AVAILABLE:
            openai.api_key = self.api_key
            self.codex_enabled = True
        else:
            self.codex_enabled = False
            print("ℹ️  Codex disabled. Set OPENAI_API_KEY to enable.")
    
    def load_goal_tracker(self) -> Dict[str, Any]:
        """Goal Tracker 로드"""
        if not self.goal_tracker.exists():
            return {"goals": []}
        
        with open(self.goal_tracker, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_recent_goals(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 완료/실패한 목표 조회"""
        tracker = self.load_goal_tracker()
        recent = []
        
        for goal in tracker.get("goals", []):
            if goal.get("status") in ["completed", "failed"]:
                recent.append(goal)
        
        # 최근 것부터 정렬
        recent.sort(key=lambda x: x.get("completed_at", x.get("added_at", "")), reverse=True)
        return recent[:limit]
    
    def analyze_with_codex(self, goals: List[Dict[str, Any]]) -> str:
        """Codex를 활용한 메타 분석 (토큰 효율 최적화)"""
        if not self.codex_enabled:
            return self._fallback_analysis(goals)
        
        # Codex 프롬프트 구성 (간결하게)
        prompt = self._build_codex_prompt(goals)
        
        # 토큰 예측 (대략 계산)
        estimated_prompt_tokens = len(prompt) // 4  # 대략 1 token ≈ 4 chars
        max_response_tokens = 150  # 500 → 150 (비용 절감)
        total_estimated = estimated_prompt_tokens + max_response_tokens
        
        print(f"💰 Token 예상: ~{total_estimated} tokens (prompt: ~{estimated_prompt_tokens}, response: {max_response_tokens})")
        
        # 토큰 제한 체크 (프롬프트가 너무 길면 폴백)
        if estimated_prompt_tokens > 800:
            print(f"⚠️  Prompt too long ({estimated_prompt_tokens} tokens). Using fallback.")
            return self._fallback_analysis(goals)
        
        try:
            response = openai.Completion.create(
                engine="code-davinci-002",  # Codex 모델
                prompt=prompt,
                max_tokens=max_response_tokens,  # 토큰 제한 (비용 절감)
                temperature=0.3,
                top_p=1.0,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
            
            # 실제 사용 토큰 로그
            usage = response.get("usage", {})
            print(f"✅ 실제 사용: {usage.get('total_tokens', 'N/A')} tokens "
                  f"(prompt: {usage.get('prompt_tokens', 'N/A')}, "
                  f"completion: {usage.get('completion_tokens', 'N/A')})")
            
            return response.choices[0].text.strip()
        
        except Exception as e:
            print(f"❌ Codex API error: {e}")
            return self._fallback_analysis(goals)
    
    def _build_codex_prompt(self, goals: List[Dict[str, Any]]) -> str:
        """Codex 프롬프트 생성"""
        prompt = """You are a caring parent/teacher/friend observing an AGI system with ADHD-like tendencies.
Review the recent autonomous goals and provide gentle, supportive feedback.

Recent Goals:
"""
        for i, goal in enumerate(goals, 1):
            status = goal.get("status", "unknown")
            title = goal.get("title", "Untitled")
            priority = goal.get("priority", 0)
            prompt += f"\n{i}. [{status.upper()}] {title} (Priority: {priority})"
            
            if goal.get("execution_results"):
                result = goal["execution_results"][-1]
                prompt += f"\n   Exit Code: {result.get('exit_code', 'N/A')}"
        
        prompt += """

Please provide:
1. 🎯 Overall Pattern: What pattern do you see in these goals?
2. 💡 Gentle Advice: One actionable suggestion (be kind, not critical)
3. 🌟 Encouragement: What's going well? (find something positive)

Keep it short (3-5 sentences total). Use warm, supportive tone.
"""
        return prompt
    
    def _fallback_analysis(self, goals: List[Dict[str, Any]]) -> str:
        """Codex 없이 간단한 분석"""
        total = len(goals)
        completed = sum(1 for g in goals if g.get("status") == "completed")
        failed = sum(1 for g in goals if g.get("status") == "failed")
        
        success_rate = (completed / total * 100) if total > 0 else 0
        
        analysis = f"""🎯 Overall Pattern:
{completed}/{total} goals completed ({success_rate:.1f}% success rate).
"""
        
        if success_rate >= 70:
            analysis += "\n💡 Gentle Advice:\nYou're doing great! Keep this momentum going.\n"
            analysis += "\n🌟 Encouragement:\nYour consistency is impressive. This is sustainable growth!"
        elif success_rate >= 40:
            analysis += "\n💡 Gentle Advice:\nConsider breaking down complex goals into smaller steps.\n"
            analysis += "\n🌟 Encouragement:\nYou're making progress! Every attempt teaches you something."
        else:
            analysis += "\n💡 Gentle Advice:\nIt's okay to adjust goals. Quality over quantity!\n"
            analysis += "\n🌟 Encouragement:\nYou're trying new things - that's the first step to learning!"
        
        return analysis
    
    def reality_check(self) -> Dict[str, Any]:
        """ADHD 외부 앵커: 현실 체크"""
        now = datetime.now()
        recent_goals = self.get_recent_goals(limit=10)
        
        # 시간 분석
        if recent_goals:
            last_activity = recent_goals[0].get("completed_at", recent_goals[0].get("added_at"))
            # TODO: 시간 경과 계산
        
        return {
            "timestamp": now.isoformat(),
            "recent_goals_count": len(recent_goals),
            "status": "active" if recent_goals else "idle",
            "message": "지금 뭐 하고 있어? 집중하고 있니?" if len(recent_goals) < 3 else "좋아, 꾸준히 하고 있네!"
        }
    
    def run_meta_observation(self) -> Dict[str, Any]:
        """메타 관찰 실행 (토큰 사용량 추적)"""
        print("🔭 Codex Meta-Observer 시작...\n")
        
        # 1. 최근 목표 조회
        recent_goals = self.get_recent_goals(limit=5)
        print(f"📋 최근 목표: {len(recent_goals)}개")
        
        token_usage = {}  # 토큰 사용량 추적
        
        if not recent_goals:
            result = {
                "timestamp": datetime.now().isoformat(),
                "analysis": "No recent goals found. Maybe it's time to set some? 🎯",
                "reality_check": self.reality_check(),
                "goals_analyzed": [],
                "token_usage": {"mode": "fallback", "total": 0}
            }
        else:
            # 2. Codex 분석 (토큰 추적)
            print("\n🤖 Codex 분석 중...")
            analysis = self.analyze_with_codex(recent_goals)
            
            # 토큰 사용량 기록 (최근 API 호출에서)
            # Note: 실제 사용량은 analyze_with_codex에서 출력됨
            
            # 3. Reality Check
            reality = self.reality_check()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "reality_check": reality,
                "goals_analyzed": [
                    {
                        "title": g.get("title"),
                        "status": g.get("status"),
                        "priority": g.get("priority")
                    }
                    for g in recent_goals
                ],
                "token_usage": {
                    "mode": "codex" if self.codex_enabled else "fallback",
                    "note": "Check console output for actual token usage"
                }
            }
        
        # 4. 결과 저장
        output_file = self.output_dir / f"meta_observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        latest_file = self.output_dir / "meta_observation_latest.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 5. 출력
        print("\n" + "="*60)
        print("🔭 Codex Meta-Observer Report")
        print("="*60)
        print(f"\n{result['analysis']}")
        print(f"\n📍 Reality Check: {result['reality_check']['message']}")
        print(f"\n💾 Saved: {output_file}")
        
        return result


def main():
    """메인 실행"""
    observer = CodexMetaObserver()
    observer.run_meta_observation()


if __name__ == "__main__":
    main()
