#!/usr/bin/env python3
"""
Session Handover System

세션 간 작업 전달을 위한 핸드오버 시스템.
토큰 제한 도달 시 현재 작업 상태를 저장하고,
다음 세션에서 비노체 페르소나를 통해 작업을 자동으로 재개.

Usage:
    from session_memory.session_handover import SessionHandoverManager
    
    # Session 1: 핸드오버 생성
    manager = SessionHandoverManager()
    handover = manager.create_handover(
        task_description="Universal AGI Phase 1 작성",
        current_progress="ROADMAP 완성",
        next_steps=["Phase 1 가이드", "Phase 2 가이드"],
        context={"phase": 1},
        resonance_key="p4_e:focus_r:document"
    )
    
    # Session 2: 핸드오버 로드
    handover = manager.get_latest_handover()
    if handover:
        print(f"Resuming: {handover.task_description}")
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


@dataclass
class SessionHandover:
    """세션 간 작업 전달 데이터"""
    
    session_id: str
    timestamp: str  # ISO format
    task_description: str
    current_progress: str
    next_steps: List[str]
    context: Dict[str, Any]
    resonance_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    def save(self, path: Path):
        """핸드오버 저장"""
        path.parent.mkdir(parents=True, exist_ok=True)
        # UTF-8 BOM 없이 저장 (PowerShell ConvertFrom-Json 호환)
        with open(path, 'w', encoding='utf-8-sig') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> 'SessionHandover':
        """핸드오버 로드"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionHandover':
        """딕셔너리에서 생성"""
        return cls(**data)


class SessionHandoverManager:
    """세션 핸드오버 관리자"""
    
    def __init__(self, handover_dir: Optional[Path] = None):
        """
        Args:
            handover_dir: 핸드오버 저장 디렉토리 (기본값: session_memory/handovers)
        """
        if handover_dir is None:
            # 현재 파일 기준으로 handovers 디렉토리 설정
            handover_dir = Path(__file__).parent / "handovers"
        
        self.handover_dir = Path(handover_dir)
        self.handover_dir.mkdir(parents=True, exist_ok=True)
    
    def create_handover(
        self,
        task_description: str,
        current_progress: str,
        next_steps: List[str],
        context: Dict[str, Any],
        resonance_key: str
    ) -> SessionHandover:
        """
        현재 세션 상태를 다음 세션에 전달하기 위한 핸드오버 생성
        
        Args:
            task_description: 작업 설명
            current_progress: 현재 진행 상황
            next_steps: 다음 단계 목록
            context: 추가 컨텍스트 (files_created, current_phase 등)
            resonance_key: 파동키 (BQI)
            
        Returns:
            SessionHandover: 생성된 핸드오버
        """
        session_id = f"handover_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        handover = SessionHandover(
            session_id=session_id,
            timestamp=timestamp,
            task_description=task_description,
            current_progress=current_progress,
            next_steps=next_steps,
            context=context,
            resonance_key=resonance_key
        )
        
        # 핸드오버 파일 저장
        handover_path = self.handover_dir / f"{session_id}.json"
        handover.save(handover_path)
        
        # 최신 핸드오버 심볼릭 링크 업데이트 (Windows: 복사)
        latest_path = self.handover_dir / "latest_handover.json"
        if latest_path.exists():
            latest_path.unlink()
        
        import shutil
        shutil.copy(handover_path, latest_path)
        
        return handover
    
    def get_latest_handover(self) -> Optional[SessionHandover]:
        """
        최신 핸드오버 로드
        
        Returns:
            SessionHandover: 최신 핸드오버 (없으면 None)
        """
        latest_path = self.handover_dir / "latest_handover.json"
        if not latest_path.exists():
            return None
        
        try:
            return SessionHandover.load(latest_path)
        except Exception as e:
            print(f"[Warning] Failed to load handover: {e}")
            return None
    
    def get_handover(self, session_id: str) -> Optional[SessionHandover]:
        """
        특정 세션 ID의 핸드오버 로드
        
        Args:
            session_id: 세션 ID
            
        Returns:
            SessionHandover: 핸드오버 (없으면 None)
        """
        handover_path = self.handover_dir / f"{session_id}.json"
        if not handover_path.exists():
            return None
        
        try:
            return SessionHandover.load(handover_path)
        except Exception as e:
            print(f"[Warning] Failed to load handover {session_id}: {e}")
            return None
    
    def list_handovers(self) -> List[SessionHandover]:
        """
        모든 핸드오버 목록 반환
        
        Returns:
            List[SessionHandover]: 핸드오버 목록 (최신순)
        """
        handovers = []
        
        for path in sorted(self.handover_dir.glob("handover_*.json"), reverse=True):
            try:
                handover = SessionHandover.load(path)
                handovers.append(handover)
            except Exception as e:
                print(f"[Warning] Failed to load {path.name}: {e}")
        
        return handovers
    
    def clear_handover(self, session_id: str) -> bool:
        """
        완료된 핸드오버 삭제
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        handover_path = self.handover_dir / f"{session_id}.json"
        if handover_path.exists():
            handover_path.unlink()
            return True
        return False
    
    def clear_all_handovers(self):
        """모든 핸드오버 삭제"""
        for path in self.handover_dir.glob("*.json"):
            path.unlink()
    
    def get_handover_summary(self) -> Dict[str, Any]:
        """
        핸드오버 상태 요약
        
        Returns:
            Dict: 요약 정보
        """
        handovers = self.list_handovers()
        latest = self.get_latest_handover()
        
        return {
            "total_handovers": len(handovers),
            "latest_handover": {
                "session_id": latest.session_id,
                "task": latest.task_description,
                "timestamp": latest.timestamp
            } if latest else None,
            "handover_dir": str(self.handover_dir),
            "recent_handovers": [
                {
                    "session_id": h.session_id,
                    "task": h.task_description,
                    "timestamp": h.timestamp
                }
                for h in handovers[:5]
            ]
        }


def main():
    """테스트 및 CLI 인터페이스"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Session Handover Manager")
    parser.add_argument("command", choices=["create", "load", "list", "clear", "summary"],
                        help="Command to execute")
    parser.add_argument("--task", type=str, help="Task description")
    parser.add_argument("--progress", type=str, help="Current progress")
    parser.add_argument("--next", type=str, nargs="+", help="Next steps")
    parser.add_argument("--session-id", type=str, help="Session ID")
    
    args = parser.parse_args()
    
    manager = SessionHandoverManager()
    
    if args.command == "create":
        if not args.task or not args.progress or not args.next:
            print("Error: --task, --progress, --next are required for create")
            return 1
        
        handover = manager.create_handover(
            task_description=args.task,
            current_progress=args.progress,
            next_steps=args.next,
            context={},
            resonance_key="p4_e:focus_r:continuation"
        )
        print(f"✅ Handover created: {handover.session_id}")
        print(f"   Task: {handover.task_description}")
        print(f"   Saved to: {manager.handover_dir}")
    
    elif args.command == "load":
        handover = manager.get_latest_handover()
        if handover:
            print(f"✅ Latest handover:")
            print(f"   Session: {handover.session_id}")
            print(f"   Task: {handover.task_description}")
            print(f"   Progress: {handover.current_progress}")
            print(f"   Next steps:")
            for i, step in enumerate(handover.next_steps, 1):
                print(f"     {i}. {step}")
        else:
            print("❌ No handover found")
    
    elif args.command == "list":
        handovers = manager.list_handovers()
        print(f"📋 Total handovers: {len(handovers)}")
        for h in handovers:
            print(f"   - {h.session_id}: {h.task_description} ({h.timestamp})")
    
    elif args.command == "clear":
        if args.session_id:
            success = manager.clear_handover(args.session_id)
            if success:
                print(f"✅ Cleared handover: {args.session_id}")
            else:
                print(f"❌ Handover not found: {args.session_id}")
        else:
            manager.clear_all_handovers()
            print("✅ All handovers cleared")
    
    elif args.command == "summary":
        summary = manager.get_handover_summary()
        print("📊 Handover Summary:")
        print(f"   Total: {summary['total_handovers']}")
        if summary['latest_handover']:
            print(f"   Latest: {summary['latest_handover']['session_id']}")
            print(f"           {summary['latest_handover']['task']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
