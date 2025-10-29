#!/usr/bin/env python3
"""
Auto-Remediation Actions - Lumen v1.4 패턴

승인된 자동복구 행동을 실행합니다:
- SCALE_DOWN: min_instances 감소
- ROLLBACK: 이전 안정 리비전으로 롤백
- EMERGENCY_STOP: 모든 인스턴스 중지
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
SERVICE_NAME = os.getenv("SERVICE_NAME", "ion-api-canary")
REGION = os.getenv("GCP_REGION", "us-central1")


class ActionResult(Enum):
    """행동 결과"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class RemediationResult:
    """자동복구 결과"""
    action_type: str
    result: str
    message: str
    details: Dict
    executed_at: str


class RemediationActions:
    """
    Auto-Remediation Actions
    
    Lumen v1.4 auto_remediation_service 패턴을 따릅니다.
    """
    
    def __init__(self, project_id: str, service_name: str, region: str):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
            region: GCP 리전
        """
        self.project_id = project_id
        self.service_name = service_name
        self.region = region
    
    def _run_gcloud_command(self, command: str) -> tuple[int, str, str]:
        """
        gcloud 명령 실행
        
        Args:
            command: 실행할 명령
            
        Returns:
            (exit_code, stdout, stderr)
        """
        print(f"🔧 실행: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout (120s)"
        except Exception as e:
            return 1, "", str(e)
    
    def scale_down(self, target_min_instances: int = 1) -> RemediationResult:
        """
        Scale Down 실행
        
        min_instances를 줄여서 비용 절감
        
        Args:
            target_min_instances: 목표 min_instances
            
        Returns:
            RemediationResult
        """
        print("=" * 70)
        print("⚠️  SCALE_DOWN 실행")
        print("=" * 70)
        
        # 현재 설정 조회
        get_cmd = (
            f"gcloud run services describe {self.service_name} "
            f"--project={self.project_id} --region={self.region} "
            f"--format='value(spec.template.metadata.annotations[\"autoscaling.knative.dev/minScale\"])'"
        )
        
        exit_code, current_min, stderr = self._run_gcloud_command(get_cmd)
        
        if exit_code != 0:
            return RemediationResult(
                action_type="SCALE_DOWN",
                result=ActionResult.FAILED.value,
                message="Failed to get current configuration",
                details={"error": stderr},
                executed_at=datetime.utcnow().isoformat(),
            )
        
        current_min = int(current_min.strip() or "0")
        print(f"📊 Current min_instances: {current_min}")
        
        if current_min <= target_min_instances:
            return RemediationResult(
                action_type="SCALE_DOWN",
                result=ActionResult.SKIPPED.value,
                message=f"Already scaled down (current: {current_min}, target: {target_min_instances})",
                details={"current_min_instances": current_min},
                executed_at=datetime.utcnow().isoformat(),
            )
        
        # Scale Down 실행
        update_cmd = (
            f"gcloud run services update {self.service_name} "
            f"--project={self.project_id} --region={self.region} "
            f"--min-instances={target_min_instances} "
            f"--quiet"
        )
        
        exit_code, stdout, stderr = self._run_gcloud_command(update_cmd)
        
        if exit_code == 0:
            print(f"✅ Scale Down 완료: {current_min} → {target_min_instances}")
            return RemediationResult(
                action_type="SCALE_DOWN",
                result=ActionResult.SUCCESS.value,
                message=f"Scaled down from {current_min} to {target_min_instances}",
                details={
                    "previous_min_instances": current_min,
                    "new_min_instances": target_min_instances,
                },
                executed_at=datetime.utcnow().isoformat(),
            )
        else:
            print(f"❌ Scale Down 실패: {stderr}")
            return RemediationResult(
                action_type="SCALE_DOWN",
                result=ActionResult.FAILED.value,
                message="Failed to scale down",
                details={"error": stderr},
                executed_at=datetime.utcnow().isoformat(),
            )
    
    def rollback(self, target_revision: Optional[str] = None) -> RemediationResult:
        """
        Rollback 실행
        
        이전 안정 리비전으로 롤백
        
        Args:
            target_revision: 목표 리비전 (None이면 자동 탐지)
            
        Returns:
            RemediationResult
        """
        print("=" * 70)
        print("🚨 ROLLBACK 실행")
        print("=" * 70)
        
        # 현재 리비전 조회
        current_cmd = (
            f"gcloud run services describe {self.service_name} "
            f"--project={self.project_id} --region={self.region} "
            f"--format='value(status.latestReadyRevisionName)'"
        )
        
        exit_code, current_revision, stderr = self._run_gcloud_command(current_cmd)
        
        if exit_code != 0:
            return RemediationResult(
                action_type="ROLLBACK",
                result=ActionResult.FAILED.value,
                message="Failed to get current revision",
                details={"error": stderr},
                executed_at=datetime.utcnow().isoformat(),
            )
        
        current_revision = current_revision.strip()
        print(f"📊 Current revision: {current_revision}")
        
        # 목표 리비전 결정
        if not target_revision:
            # 최근 리비전 목록 조회
            list_cmd = (
                f"gcloud run revisions list --service={self.service_name} "
                f"--project={self.project_id} --region={self.region} "
                f"--limit=5 --format='value(metadata.name)'"
            )
            
            exit_code, revisions_output, stderr = self._run_gcloud_command(list_cmd)
            
            if exit_code != 0:
                return RemediationResult(
                    action_type="ROLLBACK",
                    result=ActionResult.FAILED.value,
                    message="Failed to list revisions",
                    details={"error": stderr},
                    executed_at=datetime.utcnow().isoformat(),
                )
            
            revisions = [r.strip() for r in revisions_output.split('\n') if r.strip()]
            
            # 현재 리비전 다음 것 선택 (이전 버전)
            if len(revisions) < 2:
                return RemediationResult(
                    action_type="ROLLBACK",
                    result=ActionResult.SKIPPED.value,
                    message="No previous revision available",
                    details={"available_revisions": len(revisions)},
                    executed_at=datetime.utcnow().isoformat(),
                )
            
            target_revision = revisions[1]  # 두 번째 = 이전 리비전
        
        print(f"🎯 Target revision: {target_revision}")
        
        # 롤백 실행
        rollback_cmd = (
            f"gcloud run services update-traffic {self.service_name} "
            f"--project={self.project_id} --region={self.region} "
            f"--to-revisions={target_revision}=100 "
            f"--quiet"
        )
        
        exit_code, stdout, stderr = self._run_gcloud_command(rollback_cmd)
        
        if exit_code == 0:
            print(f"✅ Rollback 완료: {current_revision} → {target_revision}")
            return RemediationResult(
                action_type="ROLLBACK",
                result=ActionResult.SUCCESS.value,
                message=f"Rolled back from {current_revision} to {target_revision}",
                details={
                    "previous_revision": current_revision,
                    "target_revision": target_revision,
                },
                executed_at=datetime.utcnow().isoformat(),
            )
        else:
            print(f"❌ Rollback 실패: {stderr}")
            return RemediationResult(
                action_type="ROLLBACK",
                result=ActionResult.FAILED.value,
                message="Failed to rollback",
                details={"error": stderr},
                executed_at=datetime.utcnow().isoformat(),
            )
    
    def emergency_stop(self) -> RemediationResult:
        """
        Emergency Stop 실행
        
        모든 인스턴스를 0으로 축소 (서비스 일시 중지)
        
        Returns:
            RemediationResult
        """
        print("=" * 70)
        print("❌ EMERGENCY_STOP 실행")
        print("=" * 70)
        
        # min_instances와 max_instances 모두 0으로 설정
        stop_cmd = (
            f"gcloud run services update {self.service_name} "
            f"--project={self.project_id} --region={self.region} "
            f"--min-instances=0 --max-instances=0 "
            f"--quiet"
        )
        
        exit_code, stdout, stderr = self._run_gcloud_command(stop_cmd)
        
        if exit_code == 0:
            print(f"✅ Emergency Stop 완료: 모든 인스턴스 중지")
            return RemediationResult(
                action_type="EMERGENCY_STOP",
                result=ActionResult.SUCCESS.value,
                message="All instances stopped",
                details={"min_instances": 0, "max_instances": 0},
                executed_at=datetime.utcnow().isoformat(),
            )
        else:
            print(f"❌ Emergency Stop 실패: {stderr}")
            return RemediationResult(
                action_type="EMERGENCY_STOP",
                result=ActionResult.FAILED.value,
                message="Failed to stop instances",
                details={"error": stderr},
                executed_at=datetime.utcnow().isoformat(),
            )


def main():
    """테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-Remediation Actions")
    parser.add_argument(
        "--action",
        choices=["scale_down", "rollback", "emergency_stop"],
        required=True,
        help="행동 유형"
    )
    parser.add_argument(
        "--min-instances",
        type=int,
        default=1,
        help="Scale down 목표 min_instances"
    )
    parser.add_argument(
        "--target-revision",
        type=str,
        help="Rollback 목표 리비전"
    )
    
    args = parser.parse_args()
    
    # RemediationActions 초기화
    actions = RemediationActions(PROJECT_ID, SERVICE_NAME, REGION)
    
    # 행동 실행
    if args.action == "scale_down":
        result = actions.scale_down(target_min_instances=args.min_instances)
    elif args.action == "rollback":
        result = actions.rollback(target_revision=args.target_revision)
    else:  # emergency_stop
        result = actions.emergency_stop()
    
    # 결과 출력
    print()
    print("=" * 70)
    print(f"🎯 Action: {result.action_type}")
    print(f"📊 Result: {result.result}")
    print(f"💬 Message: {result.message}")
    print(f"📝 Details: {result.details}")
    print(f"⏰ Executed: {result.executed_at}")
    print("=" * 70)
    
    # Exit code
    exit_code = 0 if result.result == ActionResult.SUCCESS.value else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
