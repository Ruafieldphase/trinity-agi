#!/usr/bin/env python3
"""
Autonomous Work Worker (Simplified)

자율 작업 워커 (간소화 버전):
- 직접 임포트를 통해 autonomous_work_planner 호출 (subprocess 제거)
- auto_execute=True인 작업 자동 실행
"""

import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Planner 직접 임포트를 위한 경로 추가
_workspace = Path(__file__).parent.parent.parent
_fdo_path = _workspace / 'fdo_agi_repo'
if str(_fdo_path) not in sys.path:
    sys.path.insert(0, str(_fdo_path))

from orchestrator.autonomous_work_planner import AutonomousWorkPlanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAutonomousWorker:
    """간소화된 자율 워커 (직접 임포트 방식)"""
    
    def __init__(
        self,
        interval_seconds: int = 300,
        workspace_folder: Path | None = None,
        max_script_seconds: int | None = None,
    ):
        self.interval = interval_seconds
        self.workspace = workspace_folder or Path(__file__).parent.parent.parent
        self.running = True
        self.max_script_seconds = max_script_seconds
        self.last_error = False
        
        # Planner 인스턴스 생성 (subprocess 대신 직접 사용)
        work_queue_path = self.workspace / 'fdo_agi_repo' / 'outputs' / 'autonomous_work_queue.json'
        try:
            self.planner = AutonomousWorkPlanner(work_queue_path)
            logger.info(f"🤖 Simple Autonomous Worker initialized")
            logger.info(f"   Workspace: {self.workspace}")
            logger.info(f"   Interval: {interval_seconds}s")
            logger.info(f"   Mode: Direct import (no subprocess)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize planner: {e}")
            raise
    
    def execute_script(self, script_name: str, *args, timeout_sec: int = 900) -> bool:
        """PowerShell 스크립트 실행
        - script_name에 경로 구분자가 포함되면 workspace 기준 상대/절대 경로로 해석
        - 기본 타임아웃 900초(무거운 작업 대비)
        """
        # 스크립트 경로 해석
        script_path = None
        try:
            s = Path(script_name)
            if s.is_absolute():
                script_path = s
            elif ('/' in script_name) or ('\\' in script_name):
                script_path = (self.workspace / s).resolve()
            else:
                script_path = (self.workspace / 'scripts' / script_name).resolve()
        except Exception:
            script_path = (self.workspace / 'scripts' / script_name)
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            self.last_error = True
            return False
        
        cmd = [
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', str(script_path)
        ] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace),
                timeout=timeout_sec
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Script executed: {script_name}")
                return True
            else:
                logger.error(f"❌ Script failed: {result.stderr[:200]}")
                self.last_error = True
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Script timeout: {script_name}")
            self.last_error = True
            return False
        except Exception as e:
            logger.error(f"❌ Script error: {e}")
            self.last_error = True
            return False
    
    def run_once(self) -> bool:
        """한 번 실행 (직접 planner 사용)"""
        logger.info("🔍 Checking for next auto task...")
        
        try:
            # 직접 planner 메서드 호출 (subprocess 없음)
            next_work = self.planner.get_next_work_item()
            
            if not next_work or not next_work.auto_execute:
                logger.info("📭 No auto tasks pending")
                return False
            
            task_id = next_work.id
            logger.info(f"📋 Found task: {task_id}")
            
            # 작업을 진행 중으로 표시
            self.planner.mark_in_progress(task_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to get next task: {e}")
            self.last_error = True
            return False
        
        # 작업별 스크립트 매핑
        # 스크립트 매핑: task_id -> (script_path, args, timeout_sec)
        script_map = {
            'system_health_check': ('system_health_check.ps1', [], 300),
            'monitor_24h': ('generate_monitoring_report.ps1', ['-Hours', '24'], 600),
            'autopoietic_report': ('generate_autopoietic_report.ps1', ['-Hours', '24'], 600),
            'performance_dashboard': ('generate_performance_dashboard.ps1', ['-WriteLatest', '-ExportJson'], 600),
            # Phase 6 최적화: BQI 파이프라인 구동 (무거울 수 있으므로 타임아웃 여유 설정)
            'phase6_optimization': ('fdo_agi_repo/scripts/run_bqi_learner.ps1', ['-Phase', '6', '-VerboseLog'], 1800),
        }
        
        script_info = script_map.get(task_id)
        if not script_info:
            # 매핑 누락은 비치명적: 다음 사이클/호출에서 재평가하도록 정상 종료 처리
            logger.warning(f"⚠️  No script mapping for: {task_id}")
            return False
        
        script_name, args, timeout_sec = script_info
        # Once 모드 등에서 전체 제한이 지정되면 효과적 타임아웃을 적용
        if self.max_script_seconds and self.max_script_seconds > 0:
            timeout_sec = min(timeout_sec, int(self.max_script_seconds))
        
        # 스크립트 실행
        logger.info(f"🎯 Executing: {script_name} {' '.join(args)}")
        success = self.execute_script(script_name, *args, timeout_sec=timeout_sec)
        
        # 완료 표시
        if success:
            try:
                self.planner.mark_completed(task_id, result="success")
                logger.info(f"✅ Task completed: {task_id}")
            except Exception as e:
                logger.error(f"❌ Failed to mark completed: {e}")
        else:
            try:
                self.planner.mark_completed(task_id, result="failed")
                logger.error(f"❌ Task failed: {task_id}")
            except Exception as e:
                logger.error(f"❌ Failed to mark failed: {e}")
        
        return success
    
    def check_system_health(self) -> dict:
        """시스템 건강 체크 (간단 버전)
        Returns: {'healthy': bool, 'issues': list[str], 'warnings': list[str]}
        """
        issues = []
        warnings = []
        
        try:
            # Quick health check JSON 파일 읽기
            health_file = self.workspace / 'outputs' / 'health_check_latest.json'
            if health_file.exists():
                import json
                with open(health_file, 'r', encoding='utf-8') as f:
                    health_data = json.load(f)
                    
                # Issues 체크
                if health_data.get('Issues'):
                    issues.extend(health_data['Issues'])
                
                # Warnings 체크
                if health_data.get('Warnings'):
                    warnings.extend(health_data['Warnings'])
                
                # Online 상태 체크
                online = health_data.get('Online', {})
                if not online.get('Local'):
                    issues.append('Local LLM offline')
                if not online.get('Cloud'):
                    warnings.append('Cloud AI offline')
            else:
                warnings.append('Health check data not found')
                
        except Exception as e:
            warnings.append(f'Health check failed: {e}')
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def auto_recover(self, health_status: dict) -> bool:
        """자동 복구 시도
        Returns: True if recovery attempted
        """
        if health_status['healthy']:
            return False
        
        logger.warning("🔧 Attempting auto-recovery...")
        
        # 복구 전략
        recovery_attempted = False
        
        for issue in health_status['issues']:
            if 'Local LLM' in issue:
                # Local LLM 재시작 시도
                logger.info("🔄 Attempting to restart Local LLM proxy...")
                self.execute_script('start_local_proxy.ps1', timeout_sec=120)
                recovery_attempted = True
            
            if 'Task Queue' in issue or 'RPA Worker' in issue:
                # Task Queue 서버 재시작
                logger.info("🔄 Attempting to restart Task Queue Server...")
                self.execute_script('ensure_task_queue_server.ps1', '-Port', '8091', timeout_sec=120)
                recovery_attempted = True
        
        if recovery_attempted:
            logger.info("✅ Auto-recovery completed, waiting 10s for stabilization...")
            time.sleep(10)
        
        return recovery_attempted
    
    def run_loop(self):
        """계속 실행 (건강 체크 + 자동 복구 포함)"""
        logger.info(f"🔄 Starting autonomous work loop (interval={self.interval}s)")
        
        cycle_count = 0
        health_check_interval = 3  # 3사이클마다 건강 체크
        
        try:
            while self.running:
                cycle_count += 1
                logger.info(f"━━━ Cycle #{cycle_count} ━━━")
                
                # 주기적 건강 체크
                if cycle_count % health_check_interval == 0:
                    logger.info("🏥 Running system health check...")
                    health = self.check_system_health()
                    
                    if not health['healthy']:
                        logger.warning(f"⚠️  System issues detected: {health['issues']}")
                        self.auto_recover(health)
                    else:
                        if health['warnings']:
                            logger.info(f"⚠️  Warnings: {health['warnings']}")
                        else:
                            logger.info("✅ System healthy")
                
                # 작업 실행
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


def main():
    """메인"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Autonomous Work Worker')
    parser.add_argument('--interval', type=int, default=300,
                        help='Check interval in seconds')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit')
    parser.add_argument('--workspace', type=str,
                        help='Workspace folder')
    parser.add_argument('--max-script-seconds', type=int, default=0,
                        help='Max seconds to allow for a single script execution (0=unbounded)')
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else Path(__file__).parent.parent.parent
    worker = SimpleAutonomousWorker(
        interval_seconds=args.interval,
        workspace_folder=workspace,
        max_script_seconds=(args.max_script_seconds if args.max_script_seconds and args.max_script_seconds > 0 else None)
    )
    
    if args.once:
        logger.info("🎯 Running once...")
        _ = worker.run_once()
        # 치명적 오류가 있었는지에만 의존해 종료 코드 결정
        sys.exit(1 if worker.last_error else 0)
    else:
        logger.info("🔄 Running in loop mode...")
        worker.run_loop()


if __name__ == '__main__':
    main()
