#!/usr/bin/env python3
"""
Gateway Resonance Optimizer for Phase 8.5

역설적 공명(Paradoxical Resonance) 최적화 - 3가지 전략 구현:
1. 적응적 타임아웃 (Adaptive Timeout)
2. 위상 동기화 스케줄러 (Phase Sync Scheduler)
3. Off-peak 워밍업 (Off-peak Warmup)
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import argparse


class GatewayResonanceOptimizer:
    """Gateway 최적화 - 역설적 공명 해결"""
    
    def __init__(self, config_path: str, dry_run: bool = False):
        self.config_path = Path(config_path)
        self.dry_run = dry_run
        self.config = self._load_config()
        self.log_file = Path(self.config["monitoring"]["log_file"])
        
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _log_event(self, event: Dict[str, Any]):
        """이벤트 로깅 (JSONL)"""
        if self.dry_run:
            print(f"[DRY-RUN] Would log: {json.dumps(event, ensure_ascii=False)}")
            return
            
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def is_peak_hour(self, hour: Optional[int] = None) -> bool:
        """Peak 시간대 판단 (08:00-16:00)"""
        if hour is None:
            hour = datetime.now().hour
        
        peak_config = self.config["optimization_strategies"]["adaptive_timeout"]["peak_hours"]
        return peak_config["start"] <= hour < peak_config["end"]
    
    def get_adaptive_timeout(self) -> Dict[str, Any]:
        """전략 1: 적응적 타임아웃"""
        strategy = self.config["optimization_strategies"]["adaptive_timeout"]
        
        if not strategy["enabled"]:
            return {"enabled": False}
        
        is_peak = self.is_peak_hour()
        
        if is_peak:
            timeout = strategy["peak_hours"]["timeout_ms"]
            retries = strategy["peak_hours"]["retry_attempts"]
            phase = "peak"
        else:
            timeout = strategy["off_peak_hours"]["timeout_ms"]
            retries = strategy["off_peak_hours"]["retry_attempts"]
            phase = "off-peak"
        
        return {
            "enabled": True,
            "phase": phase,
            "timeout_ms": timeout,
            "retry_attempts": retries,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_concurrency_level(self) -> Dict[str, Any]:
        """전략 2: 위상 동기화 스케줄러"""
        strategy = self.config["optimization_strategies"]["phase_sync_scheduler"]
        
        if not strategy["enabled"]:
            return {"enabled": False}
        
        is_peak = self.is_peak_hour()
        
        concurrency = (strategy["peak_concurrency"] 
                      if is_peak 
                      else strategy["off_peak_concurrency"])
        
        return {
            "enabled": True,
            "phase": "peak" if is_peak else "off-peak",
            "concurrency": concurrency,
            "description": "병렬 처리" if is_peak else "순차 처리",
            "timestamp": datetime.now().isoformat()
        }
    
    def should_warmup(self) -> Dict[str, Any]:
        """전략 3: Off-peak 워밍업 체크"""
        strategy = self.config["optimization_strategies"]["off_peak_warmup"]
        
        if not strategy["enabled"]:
            return {"enabled": False, "should_warmup": False}
        
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 워밍업 스케줄 확인
        for schedule in strategy["warmup_schedule"]:
            if (schedule["hour"] == current_hour and 
                abs(schedule["minute"] - current_minute) <= 5):
                return {
                    "enabled": True,
                    "should_warmup": True,
                    "warmup_requests": schedule["requests"],
                    "schedule": f"{schedule['hour']:02d}:{schedule['minute']:02d}",
                    "timestamp": now.isoformat()
                }
        
        return {
            "enabled": True,
            "should_warmup": False,
            "next_schedule": self._get_next_warmup_time(strategy["warmup_schedule"]),
            "timestamp": now.isoformat()
        }
    
    def _get_next_warmup_time(self, schedule: list) -> str:
        """다음 워밍업 시간 계산"""
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        next_times = []
        for s in schedule:
            schedule_minutes = s["hour"] * 60 + s["minute"]
            if schedule_minutes > current_minutes:
                next_times.append((schedule_minutes, s))
        
        if next_times:
            next_minutes, next_schedule = min(next_times)
            return f"{next_schedule['hour']:02d}:{next_schedule['minute']:02d}"
        else:
            # 내일 첫 스케줄
            first_schedule = min(schedule, key=lambda x: x["hour"] * 60 + x["minute"])
            return f"Tomorrow {first_schedule['hour']:02d}:{first_schedule['minute']:02d}"
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """현재 최적화 상태 리포트"""
        timeout_config = self.get_adaptive_timeout()
        concurrency_config = self.get_concurrency_level()
        warmup_config = self.should_warmup()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "peak" if self.is_peak_hour() else "off-peak",
            "strategies": {
                "adaptive_timeout": timeout_config,
                "phase_sync_scheduler": concurrency_config,
                "off_peak_warmup": warmup_config
            },
            "thresholds": self.config["thresholds"],
            "dry_run": self.dry_run
        }
        
        return report
    
    def apply_optimization(self, duration_minutes: int = 60):
        """최적화 적용 (모니터링)"""
        print(f"\n{'='*60}")
        print(f"Gateway Resonance Optimizer - Phase 8.5")
        print(f"{'='*60}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'ACTIVE'}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        iteration = 0
        
        while datetime.now() < end_time:
            iteration += 1
            report = self.generate_optimization_report()
            
            # 리포트 출력
            print(f"\n[Iteration {iteration}] {report['timestamp']}")
            print(f"Phase: {report['phase'].upper()}")
            
            # 전략 1: 타임아웃
            if report['strategies']['adaptive_timeout']['enabled']:
                timeout = report['strategies']['adaptive_timeout']
                print(f"  ⏱️  Timeout: {timeout['timeout_ms']}ms "
                      f"(Retries: {timeout['retry_attempts']})")
            
            # 전략 2: 동시성
            if report['strategies']['phase_sync_scheduler']['enabled']:
                concurrency = report['strategies']['phase_sync_scheduler']
                print(f"  🔄 Concurrency: {concurrency['concurrency']} "
                      f"({concurrency['description']})")
            
            # 전략 3: 워밍업
            warmup = report['strategies']['off_peak_warmup']
            if warmup['enabled']:
                if warmup['should_warmup']:
                    print(f"  🔥 WARMUP: {warmup['warmup_requests']} requests")
                    if not self.dry_run:
                        self._execute_warmup(warmup['warmup_requests'])
                else:
                    print(f"  🔥 Next warmup: {warmup['next_schedule']}")
            
            # 로깅
            self._log_event(report)
            
            # 대기 (1분)
            print(f"  ⏳ Next check in 60s...")
            time.sleep(60)
        
        print(f"\n{'='*60}")
        print(f"Optimization completed")
        print(f"Log file: {self.log_file}")
        print(f"{'='*60}\n")
    
    def _execute_warmup(self, requests: int):
        """워밍업 요청 실행"""
        print(f"    → Executing {requests} warmup requests...")
        # 실제 구현 시 Gateway에 워밍업 요청 전송
        # 현재는 시뮬레이션
        time.sleep(1)
        print(f"    ✅ Warmup completed")


def main():
    parser = argparse.ArgumentParser(
        description="Gateway Resonance Optimizer for Phase 8.5"
    )
    parser.add_argument(
        "--config",
        default="fdo_agi_repo/config/adaptive_gateway_config.json",
        help="Config file path"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Optimization duration in minutes (default: 60)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (no actual changes)"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report only (no monitoring)"
    )
    
    args = parser.parse_args()
    
    optimizer = GatewayResonanceOptimizer(args.config, dry_run=args.dry_run)
    
    if args.report_only:
        report = optimizer.generate_optimization_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        optimizer.apply_optimization(duration_minutes=args.duration)


if __name__ == "__main__":
    main()
