"""
24시간 Full-Stack 시스템 모니터링
Phase 9→10 Transition

시스템의 안정성, 성능, 자율 학습 동작을 24시간 연속 모니터링합니다.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'fdo_agi_repo'))

from orchestrator.full_stack_orchestrator import FullStackOrchestrator


def monitor_system_24h(workspace_root: Path, interval_minutes: int = 5):
    """
    24시간 동안 시스템 모니터링
    
    Args:
        workspace_root: 작업 공간 경로
        interval_minutes: 모니터링 간격(분)
    """
    print("=" * 60)
    print("24시간 Full-Stack 시스템 모니터링 시작")
    print("=" * 60)
    print(f"\n시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"종료 예정: {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"모니터링 간격: {interval_minutes}분")
    print(f"예상 샘플 수: {24 * 60 // interval_minutes}개")
    
    # 출력 파일
    outputs_dir = workspace_root / 'outputs'
    outputs_dir.mkdir(exist_ok=True)
    
    log_file = outputs_dir / 'fullstack_24h_monitoring.jsonl'
    summary_file = outputs_dir / 'fullstack_24h_summary.json'
    
    print(f"\n로그 파일: {log_file}")
    print(f"요약 파일: {summary_file}")
    print("\n" + "=" * 60)
    
    # 오케스트레이터 초기화
    orchestrator = FullStackOrchestrator(workspace_root)
    
    start_time = time.time()
    end_time = start_time + (24 * 3600)  # 24시간 후
    interval_seconds = interval_minutes * 60
    
    samples = []
    sample_count = 0
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            while time.time() < end_time:
                sample_count += 1
                
                # 시스템 상태 수집
                status = orchestrator.get_status()
                
                # 타임스탬프 추가
                sample = {
                    'timestamp': datetime.now().isoformat(),
                    'sample_id': sample_count,
                    'elapsed_hours': (time.time() - start_time) / 3600,
                    'status': status
                }
                
                # JSONL 로그 기록
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
                f.flush()
                
                samples.append(sample)
                
                # 진행 상황 출력
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                progress = (elapsed / (24 * 3600)) * 100
                
                print(f"\n[샘플 #{sample_count}] {datetime.now().strftime('%H:%M:%S')}")
                print(f"  진행: {progress:.1f}% ({elapsed/3600:.1f}h / 24h)")
                print(f"  남은 시간: {remaining/3600:.1f}h")
                print(f"  처리된 이벤트: {status['state'].get('events_processed', 0)}")
                print(f"  학습 사이클: {status['state'].get('learning_cycles', 0)}")
                print(f"  컴포넌트 상태: {status['components']}")
                
                # 다음 샘플까지 대기
                time.sleep(interval_seconds)
        
        # 24시간 완료 - 요약 생성
        summary = {
            'monitoring_period': {
                'start': datetime.fromtimestamp(start_time).isoformat(),
                'end': datetime.now().isoformat(),
                'duration_hours': 24
            },
            'total_samples': sample_count,
            'sampling_interval_minutes': interval_minutes,
            'final_status': orchestrator.get_status(),
            'statistics': {
                'total_events': sum(s['status']['state'].get('events_processed', 0) for s in samples),
                'total_learning_cycles': sum(s['status']['state'].get('learning_cycles', 0) for s in samples),
                'component_availability': {
                    comp: sum(1 for s in samples if s['status']['components'].get(comp) == 'active') / len(samples)
                    for comp in ['resonance', 'bqi', 'gateway', 'youtube']
                }
            }
        }
        
        # 요약 저장
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("24시간 모니터링 완료!")
        print("=" * 60)
        print(f"\n총 샘플: {sample_count}개")
        print(f"총 이벤트: {summary['statistics']['total_events']}")
        print(f"총 학습 사이클: {summary['statistics']['total_learning_cycles']}")
        print(f"\n컴포넌트 가용성:")
        for comp, avail in summary['statistics']['component_availability'].items():
            print(f"  {comp}: {avail*100:.1f}%")
        print(f"\n요약 파일: {summary_file}")
        
    except KeyboardInterrupt:
        print("\n\n중단됨 (Ctrl+C)")
        print(f"총 샘플: {sample_count}개")
        print(f"실행 시간: {(time.time() - start_time) / 3600:.1f}시간")
        
    finally:
        orchestrator.shutdown()
        print("\nOrchestrator shutdown complete.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='24h Full-Stack Monitoring')
    parser.add_argument('--interval', type=int, default=5,
                        help='모니터링 간격(분, 기본값: 5)')
    parser.add_argument('--workspace', type=str, default=None,
                        help='작업 공간 경로')
    
    args = parser.parse_args()
    
    if args.workspace:
        workspace_root = Path(args.workspace)
    else:
        workspace_root = Path(__file__).parent.parent.parent
    
    monitor_system_24h(workspace_root, args.interval)
