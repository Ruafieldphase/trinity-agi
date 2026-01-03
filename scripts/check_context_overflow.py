#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGI 컨텍스트 오버플로우 감지 시스템
채팅 컨텍스트가 너무 길어지면 자동으로 새 채팅창 전환을 트리거합니다.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from workspace_root import get_workspace_root


class ContextMonitor:
    """컨텍스트 길이 모니터링"""
    
    def __init__(
        self,
        workspace_root: Path,
        max_tokens: int = 100000,
        check_interval: int = 60,
        state_file: str = "outputs/context_monitor_state.json"
    ):
        self.workspace_root = Path(workspace_root)
        self.max_tokens = max_tokens
        self.check_interval = check_interval
        self.state_file = self.workspace_root / state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """상태 로드"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "last_check": None,
            "current_tokens": 0,
            "last_switch": None,
            "switch_count": 0
        }
    
    def _save_state(self):
        """상태 저장"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def estimate_tokens(self) -> int:
        """
        현재 채팅 컨텍스트 토큰 수 추정
        
        실제로는 GitHub Copilot API를 호출해야 하지만,
        여기서는 간단한 휴리스틱 사용:
        - 최근 작업 파일들 크기
        - 레저 로그 크기
        - 시간 기반 추정
        """
        total_chars = 0
        
        # 1. 최근 리포트 파일 크기
        report_files = [
            "outputs/session_continuity_latest.md",
            "outputs/.copilot_context_summary.md",
            "fdo_agi_repo/memory/resonance_ledger.jsonl"
        ]
        
        for report in report_files:
            path = self.workspace_root / report
            if path.exists():
                total_chars += path.stat().st_size
        
        # 2. 간단한 토큰 추정 (1 token ≈ 4 chars)
        estimated_tokens = total_chars // 4
        
        # 3. 최근 활동 시간 기반 보정
        if self.state["last_switch"]:
            last_switch = datetime.fromisoformat(self.state["last_switch"])
            hours_since_switch = (datetime.now() - last_switch).total_seconds() / 3600
            # 1시간당 약 5000 토큰씩 증가 가정
            time_based_tokens = int(hours_since_switch * 5000)
            estimated_tokens += time_based_tokens
        
        return estimated_tokens
    
    def should_switch_chat(self) -> bool:
        """새 채팅창으로 전환해야 하는지 판단"""
        current_tokens = self.estimate_tokens()
        self.state["current_tokens"] = current_tokens
        self.state["last_check"] = datetime.now().isoformat()
        self._save_state()
        
        # 토큰 임계값 초과 체크
        if current_tokens > self.max_tokens:
            print(f"⚠️ 컨텍스트 오버플로우 감지!")
            print(f"   현재 토큰: {current_tokens:,}")
            print(f"   임계값: {self.max_tokens:,}")
            return True
        
        return False
    
    def record_switch(self):
        """채팅 전환 기록"""
        self.state["last_switch"] = datetime.now().isoformat()
        self.state["switch_count"] += 1
        self.state["current_tokens"] = 0  # 리셋
        self._save_state()
        
        print(f"✅ 채팅 전환 기록됨 (총 {self.state['switch_count']}회)")
    
    def get_status(self) -> Dict:
        """현재 상태 반환"""
        current_tokens = self.estimate_tokens()
        usage_percent = (current_tokens / self.max_tokens) * 100
        
        return {
            "current_tokens": current_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "should_switch": current_tokens > self.max_tokens,
            "last_check": self.state.get("last_check"),
            "last_switch": self.state.get("last_switch"),
            "switch_count": self.state.get("switch_count", 0)
        }


def check_and_auto_switch(
    workspace_root: str = None,
    max_tokens: int = 100000,
    auto_switch: bool = False
) -> bool:
    """
    컨텍스트 체크 및 자동 전환
    
    Args:
        workspace_root: 워크스페이스 루트 경로
        max_tokens: 최대 토큰 수
        auto_switch: True면 자동으로 채팅 전환 실행
    
    Returns:
        전환이 필요한지 여부
    """
    if workspace_root is None:
        workspace_root = get_workspace_root()
    
    monitor = ContextMonitor(workspace_root, max_tokens)
    status = monitor.get_status()
    
    print("=" * 60)
    print("📊 AGI 컨텍스트 모니터")
    print("=" * 60)
    print(f"현재 토큰: {status['current_tokens']:,} / {status['max_tokens']:,}")
    print(f"사용률: {status['usage_percent']:.1f}%")
    print(f"마지막 전환: {status['last_switch'] or 'N/A'}")
    print(f"전환 횟수: {status['switch_count']}회")
    print("=" * 60)
    
    if status['should_switch']:
        print()
        print("🔔 새 채팅창 전환이 필요합니다!")
        
        if auto_switch:
            print()
            print("🎮 자동 전환 실행 중...")
            
            # auto_switch_chat.py 실행
            import subprocess
            import sys
            
            script_path = Path(__file__).parent / "auto_switch_chat.py"
            result = subprocess.run(
                [sys.executable, str(script_path), "--delay", "3"],
                capture_output=False
            )
            
            if result.returncode == 0:
                monitor.record_switch()
                print("✅ 자동 전환 완료!")
                return True
            else:
                print("❌ 자동 전환 실패")
                return False
        else:
            print()
            print("💡 수동으로 전환하려면:")
            print("   VS Code Task: 🎮 Chat: Auto Switch (Python 게임 봇!)")
            return True
    else:
        print()
        print(f"✅ 컨텍스트 여유 있음 ({100 - status['usage_percent']:.1f}% 남음)")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AGI 컨텍스트 오버플로우 감지 및 자동 전환'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=100000,
        help='최대 토큰 수 (기본: 100000)'
    )
    parser.add_argument(
        '--auto-switch',
        action='store_true',
        help='자동으로 채팅 전환 실행'
    )
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='상태만 출력 (전환 없음)'
    )
    
    args = parser.parse_args()
    
    if args.status_only:
        workspace_root = get_workspace_root()
        monitor = ContextMonitor(workspace_root, args.max_tokens)
        status = monitor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        need_switch = check_and_auto_switch(
            max_tokens=args.max_tokens,
            auto_switch=args.auto_switch
        )
        return 0 if not need_switch else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
