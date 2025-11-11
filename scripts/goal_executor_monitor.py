#!/usr/bin/env python3
"""
Goal Executor Monitor - Goal Execution 상태 모니터링 및 자동 재시작

Goal Tracker가 너무 오래 업데이트되지 않으면 자동으로 Goal Executor를 재실행합니다.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

# Setup
workspace = Path(__file__).parent.parent
sys.path.insert(0, str(workspace / "fdo_agi_repo"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class GoalExecutorMonitor:
    """Goal Executor 모니터"""
    
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path
        self.tracker_path = workspace_path / "fdo_agi_repo" / "memory" / "goal_tracker.json"
        self.executor_script = workspace_path / "scripts" / "autonomous_goal_executor.py"
        self.python_exe = workspace_path / "fdo_agi_repo" / ".venv" / "Scripts" / "python.exe"
        
        if not self.python_exe.exists():
            self.python_exe = Path("python")
    
    def get_tracker_status(self) -> Tuple[bool, Optional[datetime], Dict]:
        """Goal Tracker 상태 확인"""
        
        if not self.tracker_path.exists():
            return False, None, {"error": "Tracker file not found"}
        
        try:
            with open(self.tracker_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 마지막 업데이트 시간
            last_update_str = data.get("last_update") or data.get("last_updated")
            if last_update_str:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            else:
                last_update = None
            
            return True, last_update, data
            
        except Exception as e:
            logging.error(f"Tracker 읽기 실패: {e}")
            return False, None, {"error": str(e)}
    
    def calculate_staleness(self, last_update: Optional[datetime]) -> Optional[float]:
        """마지막 업데이트 이후 경과 시간 (분)"""
        
        if not last_update:
            return None
        
        now = datetime.now(last_update.tzinfo) if last_update.tzinfo else datetime.now()
        delta = now - last_update
        return delta.total_seconds() / 60.0
    
    def run_executor(self) -> bool:
        """Goal Executor 실행"""
        
        logging.info("🎯 Goal Executor 실행 중...")
        
        try:
            result = subprocess.run(
                [str(self.python_exe), str(self.executor_script)],
                capture_output=True,
                text=True,
                timeout=300,  # 5분 제한
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0:
                logging.info("✅ Goal Executor 성공")
                logging.info(f"출력: {result.stdout[:500]}")
                return True
            else:
                logging.error(f"❌ Goal Executor 실패 (exit code: {result.returncode})")
                logging.error(f"에러: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error("⏰ Goal Executor 타임아웃 (5분 초과)")
            return False
        except Exception as e:
            logging.error(f"💥 Goal Executor 실행 오류: {e}")
            return False
    
    def monitor_and_fix(self, threshold_minutes: float = 60.0, dry_run: bool = False) -> Dict:
        """모니터링 및 자동 수정"""
        
        logging.info("🔍 Goal Executor 모니터링 시작...")
        logging.info(f"  임계값: {threshold_minutes}분")
        logging.info(f"  Dry-run: {dry_run}")
        
        # 1. Tracker 상태 확인
        exists, last_update, data = self.get_tracker_status()
        
        if not exists:
            logging.warning("⚠️  Goal Tracker가 존재하지 않음")
            if not dry_run:
                logging.info("🚀 Goal Executor 실행 (초기화)")
                success = self.run_executor()
            else:
                logging.info("🧪 Dry-run: Goal Executor 실행 스킵")
                success = False
            
            return {
                "status": "initialized" if success else "failed",
                "action_taken": "run_executor" if not dry_run else "none",
                "success": success
            }
        
        # 2. 경과 시간 계산
        staleness = self.calculate_staleness(last_update)
        
        if staleness is None:
            logging.warning("⚠️  마지막 업데이트 시간 없음")
            staleness_str = "unknown"
            needs_fix = True
        else:
            staleness_str = f"{staleness:.1f}분"
            needs_fix = staleness > threshold_minutes
        
        # 3. 상태 출력
        logging.info(f"📊 Tracker 상태:")
        logging.info(f"  마지막 업데이트: {last_update or 'unknown'}")
        logging.info(f"  경과 시간: {staleness_str}")
        logging.info(f"  목표 수: {len(data.get('goals', []))}")
        logging.info(f"  수정 필요: {needs_fix}")
        
        # 4. 자동 수정
        if needs_fix:
            if not dry_run:
                logging.warning(f"⚡ 임계값 초과 ({staleness_str} > {threshold_minutes}분)")
                logging.info("🚀 Goal Executor 재실행...")
                success = self.run_executor()
            else:
                logging.info(f"🧪 Dry-run: Goal Executor 재실행 스킵")
                success = False
            
            return {
                "status": "fixed" if success else "failed",
                "staleness_minutes": staleness,
                "action_taken": "run_executor" if not dry_run else "none",
                "success": success
            }
        else:
            logging.info(f"✅ 정상 상태 ({staleness_str} < {threshold_minutes}분)")
            return {
                "status": "healthy",
                "staleness_minutes": staleness,
                "action_taken": "none",
                "success": True
            }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Goal Executor Monitor")
    parser.add_argument("--threshold", type=float, default=60.0,
                       help="Staleness threshold in minutes (default: 60)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Check only, don't execute")
    parser.add_argument("--log", type=str,
                       help="Log file path (optional)")
    
    args = parser.parse_args()
    
    # Configure logging to file if specified
    if args.log:
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logging.getLogger().addHandler(file_handler)
    
    # Run
    monitor = GoalExecutorMonitor(workspace)
    result = monitor.monitor_and_fix(
        threshold_minutes=args.threshold,
        dry_run=args.dry_run
    )
    
    # Exit code
    if result["success"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
