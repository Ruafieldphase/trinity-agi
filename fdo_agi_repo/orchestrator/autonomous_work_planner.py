#!/usr/bin/env python3
"""
Autonomous Work Planner

작업 완료 후 자동으로 다음 작업을 계획하고 실행하는 시스템
Phase 6+ 핵심 컴포넌트
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WorkItem:
    """작업 항목"""
    id: str
    title: str
    description: str
    priority: int  # 1-10, 10이 최고
    category: str  # 'monitoring', 'learning', 'optimization', 'maintenance'
    estimated_duration_minutes: int
    dependencies: List[str]  # 의존성 작업 ID 목록
    auto_execute: bool  # 자동 실행 여부
    created_at: str
    last_updated: str
    status: str  # 'pending', 'in_progress', 'completed', 'skipped'
    result: Optional[str] = None


class AutonomousWorkPlanner:
    """자율 작업 계획 시스템"""
    
    def __init__(self, work_queue_path: Path):
        self.work_queue_path = work_queue_path
        self.work_queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.work_queue: List[WorkItem] = []
        # 주기적(반복) 실행 정책: 일정 시간 경과 후 자동으로 pending으로 복귀
        self.recurring_policies: Dict[str, timedelta] = {
            'system_health_check': timedelta(hours=1),
            'monitor_24h': timedelta(hours=24),
            'autopoietic_report': timedelta(hours=24),
            'performance_dashboard': timedelta(hours=6),
            # SiAN 추론 점검은 12시간마다 재실행
            'sian_thinking': timedelta(hours=12),
        }
        self._load_work_queue()
        # 기존 큐가 있는 경우에도 신규 기본 작업을 보강
        self._ensure_backfill_items()
    
    def _load_work_queue(self):
        """작업 대기열 로드"""
        if self.work_queue_path.exists():
            try:
                with open(self.work_queue_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.work_queue = [WorkItem(**item) for item in data.get('items', [])]
                logger.info(f"Loaded {len(self.work_queue)} work items")
            except Exception as e:
                logger.error(f"Failed to load work queue: {e}")
                self.work_queue = []
        else:
            logger.info("No existing work queue found, initializing...")
            self._initialize_default_queue()
    
    def _save_work_queue(self):
        """작업 대기열 저장"""
        try:
            data = {
                'last_updated': datetime.utcnow().isoformat(),
                'items': [asdict(item) for item in self.work_queue]
            }
            with open(self.work_queue_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.work_queue)} work items")
        except Exception as e:
            logger.error(f"Failed to save work queue: {e}")

    def _ensure_backfill_items(self):
        """기존 큐에 누락된 신규 기본 작업을 보강한다 (역호환)."""
        try:
            existing_ids = {item.id for item in self.work_queue}
            now = datetime.utcnow().isoformat()

            backfilled = False
            # SiAN 추론 점검 작업이 없다면 추가
            if 'sian_thinking' not in existing_ids:
                self.work_queue.append(
                    WorkItem(
                        id="sian_thinking",
                        title="SiAN Meta Layer Quick Thinking Probe",
                        description="Gemini 추론 모델로 메타층 상태 점검용 간단 질의 실행",
                        priority=8,
                        category="learning",
                        estimated_duration_minutes=1,
                        dependencies=[],
                        auto_execute=True,
                        created_at=now,
                        last_updated=now,
                        status="pending"
                    )
                )
                backfilled = True

            if backfilled:
                self._save_work_queue()
                logger.info("Backfilled missing default items into work queue")
        except Exception as e:
            logger.warning(f"Backfill ensure failed: {e}")
    
    def _initialize_default_queue(self):
        """기본 작업 대기열 초기화"""
        now = datetime.utcnow().isoformat()
        
        default_items = [
            WorkItem(
                id="monitor_24h",
                title="24h 통합 모니터링 리포트 생성",
                description="지난 24시간 시스템 성능 및 이벤트 분석",
                priority=8,
                category="monitoring",
                estimated_duration_minutes=5,
                dependencies=[],
                auto_execute=True,
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="sian_thinking",
                title="SiAN Meta Layer Quick Thinking Probe",
                description="Gemini 추론 모델로 메타층 상태 점검용 간단 질의 실행",
                priority=8,
                category="learning",
                estimated_duration_minutes=1,
                dependencies=[],
                auto_execute=True,
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="autopoietic_report",
                title="Autopoietic Loop 분석",
                description="자기생성 루프 성능 및 개선점 분석",
                priority=7,
                category="monitoring",
                estimated_duration_minutes=3,
                dependencies=["monitor_24h"],
                auto_execute=True,
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="phase6_optimization",
                title="Phase 6 성능 최적화",
                description="Ensemble 가중치 미세 조정 및 정확도 향상",
                priority=6,
                category="optimization",
                estimated_duration_minutes=10,
                dependencies=["autopoietic_report"],
                auto_execute=False,  # 사용자 승인 필요
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="layer23_activation",
                title="Layer 2 & 3 Monitoring 활성화",
                description="관리자 권한으로 Task Watchdog와 Meta Observer 등록",
                priority=5,
                category="maintenance",
                estimated_duration_minutes=2,
                dependencies=[],
                auto_execute=False,  # 관리자 권한 필요
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="performance_dashboard",
                title="성능 대시보드 업데이트",
                description="최신 메트릭으로 대시보드 HTML 생성",
                priority=6,
                category="monitoring",
                estimated_duration_minutes=3,
                dependencies=["monitor_24h"],
                auto_execute=True,
                created_at=now,
                last_updated=now,
                status="pending"
            ),
            WorkItem(
                id="system_health_check",
                title="전체 시스템 헬스 체크",
                description="모든 서비스 및 Scheduled Tasks 상태 확인",
                priority=9,
                category="monitoring",
                estimated_duration_minutes=2,
                dependencies=[],
                auto_execute=True,
                created_at=now,
                last_updated=now,
                status="pending"
            ),
        ]
        
        self.work_queue = default_items
        self._save_work_queue()
        logger.info("Initialized default work queue")
    
    def get_next_work_item(self) -> Optional[WorkItem]:
        """다음 실행할 작업 가져오기"""
        # 주기 작업 갱신
        self._refresh_recurring_items()
        # Pending 상태이고 의존성이 모두 완료된 작업 필터링
        eligible_items = []
        
        for item in self.work_queue:
            if item.status != 'pending':
                continue
            
            # 의존성 체크
            dependencies_met = all(
                any(w.id == dep and w.status == 'completed' for w in self.work_queue)
                for dep in item.dependencies
            ) if item.dependencies else True
            
            if dependencies_met:
                eligible_items.append(item)
        
        # 우선순위로 정렬 (높은 것부터)
        eligible_items.sort(key=lambda x: x.priority, reverse=True)
        
        # auto_execute=True인 것 우선
        auto_items = [item for item in eligible_items if item.auto_execute]
        if auto_items:
            return auto_items[0]
        
        # 수동 실행 항목 중 가장 우선순위 높은 것
        if eligible_items:
            return eligible_items[0]
        
        return None

    def _refresh_recurring_items(self):
        """완료된 주기 작업을 정책에 따라 pending으로 복귀"""
        changed = False
        now = datetime.utcnow()
        for item in self.work_queue:
            if item.status == 'completed' and item.id in self.recurring_policies:
                try:
                    last = datetime.fromisoformat(item.last_updated)
                except Exception:
                    # 파싱 실패 시 즉시 갱신 기준으로 본다
                    last = now - self.recurring_policies[item.id] - timedelta(seconds=1)
                cooldown = self.recurring_policies[item.id]
                if now - last >= cooldown:
                    item.status = 'pending'
                    item.result = None
                    item.last_updated = now.isoformat()
                    changed = True
                    logger.info(f"Re-queued recurring item '{item.id}' after cooldown {cooldown}")
        if changed:
            self._save_work_queue()
    
    def mark_completed(self, work_id: str, result: str = "success"):
        """작업 완료 표시"""
        for item in self.work_queue:
            if item.id == work_id:
                item.status = 'completed'
                item.result = result
                item.last_updated = datetime.utcnow().isoformat()
                self._save_work_queue()
                logger.info(f"Marked work item '{work_id}' as completed")
                break
    
    def mark_in_progress(self, work_id: str):
        """작업 진행 중 표시"""
        for item in self.work_queue:
            if item.id == work_id:
                item.status = 'in_progress'
                item.last_updated = datetime.utcnow().isoformat()
                self._save_work_queue()
                logger.info(f"Marked work item '{work_id}' as in_progress")
                break
    
    def skip_work_item(self, work_id: str, reason: str = "user_skipped"):
        """작업 건너뛰기"""
        for item in self.work_queue:
            if item.id == work_id:
                item.status = 'skipped'
                item.result = reason
                item.last_updated = datetime.utcnow().isoformat()
                self._save_work_queue()
                logger.info(f"Skipped work item '{work_id}': {reason}")
                break
    
    def get_work_summary(self) -> Dict:
        """작업 대기열 요약"""
        summary = {
            'total': len(self.work_queue),
            'pending': sum(1 for item in self.work_queue if item.status == 'pending'),
            'in_progress': sum(1 for item in self.work_queue if item.status == 'in_progress'),
            'completed': sum(1 for item in self.work_queue if item.status == 'completed'),
            'skipped': sum(1 for item in self.work_queue if item.status == 'skipped'),
            'auto_executable': sum(1 for item in self.work_queue 
                                   if item.status == 'pending' and item.auto_execute),
        }
        return summary
    
    def generate_plan_report(self) -> str:
        """작업 계획 리포트 생성"""
        lines = [
            "# 🤖 Autonomous Work Plan",
            "",
            f"**Generated**: {datetime.utcnow().isoformat()}",
            "",
            "## 📊 Summary",
            ""
        ]
        
        summary = self.get_work_summary()
        lines.extend([
            f"- Total Items: {summary['total']}",
            f"- Pending: {summary['pending']}",
            f"- In Progress: {summary['in_progress']}",
            f"- Completed: {summary['completed']}",
            f"- Skipped: {summary['skipped']}",
            f"- Auto-Executable: {summary['auto_executable']}",
            "",
            "## 📋 Work Queue (by priority)",
            ""
        ])
        
        # 우선순위 순으로 정렬
        sorted_items = sorted(self.work_queue, key=lambda x: x.priority, reverse=True)
        
        for item in sorted_items:
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'skipped': '⏭️'
            }.get(item.status, '❓')
            
            auto_badge = "🤖 AUTO" if item.auto_execute else "👤 MANUAL"
            
            lines.extend([
                f"### {status_emoji} {item.title}",
                f"**ID**: `{item.id}` | **Priority**: {item.priority}/10 | **Status**: {item.status} | {auto_badge}",
                f"**Category**: {item.category} | **Duration**: ~{item.estimated_duration_minutes}m",
                "",
                item.description,
                ""
            ])
            
            if item.dependencies:
                lines.append(f"**Dependencies**: {', '.join(item.dependencies)}")
                lines.append("")
            
            if item.result:
                lines.append(f"**Result**: {item.result}")
                lines.append("")
        
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    workspace = Path(__file__).parent.parent
    queue_path = workspace / "outputs" / "autonomous_work_queue.json"
    
    planner = AutonomousWorkPlanner(queue_path)
    
    if len(sys.argv) > 1 and sys.argv[1] == "next":
        # 다음 작업 가져오기
        next_item = planner.get_next_work_item()
        if next_item:
            print(f"\n🎯 Next Work Item:")
            print(f"   ID: {next_item.id}")
            print(f"   Title: {next_item.title}")
            print(f"   Priority: {next_item.priority}/10")
            print(f"   Auto-Execute: {next_item.auto_execute}")
            print(f"   Estimated: {next_item.estimated_duration_minutes}m\n")
        else:
            print("\n✅ No pending work items!\n")
    elif len(sys.argv) > 2 and sys.argv[1] == "complete":
        # 작업 완료 표시
        work_id = sys.argv[2]
        planner.mark_completed(work_id)
        print(f"\n✅ Marked '{work_id}' as completed\n")
    else:
        # 리포트 생성
        report_path = workspace / "outputs" / "autonomous_work_plan.md"
        report = planner.generate_plan_report()
        report_path.write_text(report, encoding='utf-8')
        print(f"\n📄 Work plan saved: {report_path}\n")
        print(report)
