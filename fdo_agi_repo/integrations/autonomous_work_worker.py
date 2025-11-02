#!/usr/bin/env python3
"""
Autonomous Work Queue Worker

자율 작업 큐 워커:
- autonomous_work_planner에서 다음 작업 확인
- auto_execute=True인 작업 자동 실행
- 결과를 resonance_ledger에 기록
- Task Queue Server와 통합 가능
"""

import sys
import time
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.autonomous_work_planner import AutonomousWorkPlanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class AutonomousWorkWorker:
    """자율 작업 워커"""
    
    def __init__(
        self,
        interval_seconds: int = 300,  # 5분
        workspace_folder: Optional[Path] = None
    ):
        self.interval = interval_seconds
        self.workspace = workspace_folder or Path(__file__).parent.parent.parent
        
        # Work queue 경로
        work_queue_path = self.workspace / 'fdo_agi_repo' / 'outputs' / 'autonomous_work_queue.json'
        self.planner = AutonomousWorkPlanner(work_queue_path)
        self.running = True
        
        logger.info(f"🤖 Autonomous Work Worker initialized")
        logger.info(f"   Workspace: {self.workspace}")
        logger.info(f"   Interval: {interval_seconds}s")
    
    def get_next_auto_task(self) -> Optional[Dict[str, Any]]:
        """다음 자동 실행 작업 가져오기"""
        try:
            items = self.planner.list_items(status='pending')
            
            # auto_execute=True인 작업만 필터
            auto_items = [
                item for item in items 
                if item.get('auto_execute', False)
            ]
            
            if not auto_items:
                return None
            
            # 우선순위 정렬
            auto_items.sort(key=lambda x: x.get('priority', 0), reverse=True)
            
            return auto_items[0]
            
        except Exception as e:
            logger.error(f"❌ Failed to get next task: {e}")
            return None
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """작업 실행"""
        task_id = task.get('id', 'unknown')
        title = task.get('title', 'Unknown Task')
        
        logger.info(f"🎯 Executing: {title} (id={task_id})")
        
        try:
            # 작업별 실행 로직
            category = task.get('category', '')
            
            if category == 'monitoring':
                success = self._execute_monitoring_task(task)
            elif category == 'optimization':
                success = self._execute_optimization_task(task)
            elif category == 'maintenance':
                success = self._execute_maintenance_task(task)
            else:
                logger.warning(f"⚠️  Unknown category: {category}")
                success = False
            
            # 완료 표시
            if success:
                self.planner.mark_completed(task_id, success=True)
                logger.info(f"✅ Task completed: {task_id}")
            else:
                logger.error(f"❌ Task failed: {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Task execution error: {e}")
            self.planner.mark_completed(task_id, success=False, error=str(e))
            return False
    
    def _execute_monitoring_task(self, task: Dict[str, Any]) -> bool:
        """모니터링 작업 실행"""
        task_id = task.get('id', '')
        
        script_map = {
            'system_health_check': 'system_health_check.ps1',
            'monitor_24h': 'generate_monitoring_report.ps1 -Hours 24',
            'autopoietic_report': 'generate_autopoietic_report.ps1 -Hours 24',
            'performance_dashboard': 'generate_performance_dashboard.ps1 -WriteLatest',
        }
        
        script = script_map.get(task_id)
        if not script:
            logger.warning(f"⚠️  No script for task: {task_id}")
            return False
        
        script_path = self.workspace / 'scripts' / script.split()[0]
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        # PowerShell 실행
        cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
        if len(script.split()) > 1:
            cmd.extend(script.split()[1:])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Script executed: {script}")
                return True
            else:
                logger.error(f"❌ Script failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Script timeout: {script}")
            return False
        except Exception as e:
            logger.error(f"❌ Script error: {e}")
            return False
    
    def _execute_optimization_task(self, task: Dict[str, Any]) -> bool:
        """최적화 작업 실행"""
        logger.info(f"🔧 Optimization task: {task.get('title')}")
        # TODO: 최적화 작업 구현
        return True
    
    def _execute_maintenance_task(self, task: Dict[str, Any]) -> bool:
        """유지보수 작업 실행"""
        logger.info(f"🛠️  Maintenance task: {task.get('title')}")
        # TODO: 유지보수 작업 구현
        return True
    
    def run_once(self) -> bool:
        """한 번 실행"""
        logger.info("🔍 Checking for next auto task...")
        
        task = self.get_next_auto_task()
        
        if not task:
            logger.info("📭 No auto tasks pending")
            return False
        
        logger.info(f"📋 Found task: {task.get('title')} (priority={task.get('priority')})")
        
        return self.execute_task(task)
    
    def run_loop(self):
        """계속 실행 (루프)"""
        logger.info(f"🔄 Starting autonomous work loop (interval={self.interval}s)")
        
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                logger.info(f"━━━ Cycle #{cycle_count} ━━━")
                
                executed = self.run_once()
                
                if executed:
                    logger.info(f"✅ Cycle #{cycle_count} completed with execution")
                else:
                    logger.info(f"⏭️  Cycle #{cycle_count} completed (no execution)")
                
                logger.info(f"💤 Sleeping for {self.interval}s...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️  Worker stopped by user")
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
            raise
        finally:
            logger.info("🛑 Worker shutdown")
    
    def stop(self):
        """워커 중지"""
        self.running = False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Work Queue Worker')
    parser.add_argument('--interval', type=int, default=300,
                        help='Check interval in seconds (default: 300)')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit')
    parser.add_argument('--workspace', type=str,
                        help='Workspace folder path')
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    worker = AutonomousWorkWorker(
        interval_seconds=args.interval,
        workspace_folder=workspace
    )
    
    if args.once:
        logger.info("🎯 Running once...")
        executed = worker.run_once()
        sys.exit(0 if executed else 1)
    else:
        logger.info("🔄 Running in loop mode...")
        worker.run_loop()


if __name__ == '__main__':
    main()
