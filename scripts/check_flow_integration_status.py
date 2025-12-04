#!/usr/bin/env python3
"""
통합 상태 확인: Flow Observer + Desktop Observer
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

def check_observer_status():
    """Desktop Observer 실행 상태 확인"""
    pid_file = Path('outputs/telemetry/observer_telemetry.pid')
    
    if not pid_file.exists():
        return {
            'status': 'stopped',
            'message': 'Desktop Observer가 실행 중이지 않습니다.'
        }
    
    try:
        pid = int(pid_file.read_text().strip())
        # Windows에서 프로세스 존재 확인
        import subprocess
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}'],
            capture_output=True, text=True
        )
        
        if 'powershell' in result.stdout.lower() or 'pwsh' in result.stdout.lower():
            return {
                'status': 'running',
                'pid': pid,
                'message': f'Desktop Observer 실행 중 (PID: {pid})'
            }
        else:
            return {
                'status': 'stopped',
                'message': 'Desktop Observer PID 파일은 있지만 프로세스가 없습니다.'
            }
    except Exception as e:
        return {
            'status': 'unknown',
            'message': f'상태 확인 실패: {str(e)}'
        }

def check_telemetry_data():
    """텔레메트리 데이터 수집 상태 확인"""
    tele_dir = Path('outputs/telemetry')
    if not tele_dir.exists():
        return {
            'status': 'no_data',
            'message': '텔레메트리 디렉토리가 없습니다.'
        }
    
    today_file = tele_dir / f"stream_observer_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    
    if not today_file.exists():
        return {
            'status': 'no_data',
            'message': '오늘 데이터가 아직 없습니다.'
        }
    
    try:
        lines = today_file.read_text(encoding='utf-8', errors='ignore').strip().split('\n')
        record_count = len([l for l in lines if l.strip()])
        
        # 마지막 레코드 시간
        if record_count > 0:
            last_record = json.loads(lines[-1])
            last_ts = datetime.fromisoformat(last_record['ts_utc'].replace('Z', '+00:00'))
            minutes_ago = (datetime.now(timezone.utc) - last_ts).total_seconds() / 60
            
            return {
                'status': 'collecting',
                'record_count': record_count,
                'last_activity': last_ts.isoformat(),
                'minutes_ago': round(minutes_ago, 1),
                'message': f'{record_count}개 레코드 수집됨 (마지막: {minutes_ago:.1f}분 전)'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'데이터 파싱 실패: {str(e)}'
        }
    
    return {
        'status': 'unknown',
        'message': '상태 확인 실패'
    }

def check_scheduled_validation():
    """스케줄된 검증 작업 확인"""
    import subprocess
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Job | ConvertTo-Json'],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            jobs = json.loads(result.stdout)
            if not isinstance(jobs, list):
                jobs = [jobs]
            
            validation_jobs = [j for j in jobs if j.get('State') == 'Running']
            
            if validation_jobs:
                return {
                    'status': 'scheduled',
                    'job_count': len(validation_jobs),
                    'message': f'{len(validation_jobs)}개 검증 작업 예약됨'
                }
        
        return {
            'status': 'none',
            'message': '예약된 검증 작업 없음'
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'message': f'작업 확인 실패: {str(e)}'
        }

def main():
    print("🌊 Flow Observer Integration Status Check\n")
    print("=" * 60)
    
    # 1. Desktop Observer 상태
    print("\n📡 Desktop Observer:")
    observer = check_observer_status()
    status_icon = "✅" if observer['status'] == 'running' else "❌"
    print(f"   {status_icon} {observer['message']}")
    
    # 2. 텔레메트리 데이터
    print("\n📊 Telemetry Data:")
    data = check_telemetry_data()
    status_icon = "✅" if data['status'] == 'collecting' else "⚠️"
    print(f"   {status_icon} {data['message']}")
    
    if data['status'] == 'collecting':
        print(f"      Last activity: {data['minutes_ago']:.1f} minutes ago")
        
        # 데이터 충분성 평가
        if data['record_count'] >= 12:  # 1분 데이터 (5초 * 12)
            print("      ✅ 분석 가능한 데이터 수집됨")
        else:
            needed = 12 - data['record_count']
            print(f"      ⏳ {needed}개 더 필요 (약 {needed * 5}초)")
    
    # 3. 스케줄 상태
    print("\n⏰ Scheduled Validation:")
    schedule = check_scheduled_validation()
    status_icon = "✅" if schedule['status'] == 'scheduled' else "ℹ️"
    print(f"   {status_icon} {schedule['message']}")
    
    # 4. 종합 평가
    print("\n" + "=" * 60)
    print("\n🎯 Overall Status:")
    
    all_good = (
        observer['status'] == 'running' and
        data['status'] == 'collecting' and
        data.get('record_count', 0) >= 12
    )
    
    if all_good:
        print("   ✅ 시스템이 정상적으로 작동 중입니다!")
        print("   💡 계속 자연스럽게 작업하시면 됩니다.")
        
        if schedule['status'] == 'scheduled':
            print("   ⏰ 예약된 검증이 자동으로 실행됩니다.")
        else:
            print("   💡 수동 검증: python fdo_agi_repo/copilot/flow_observer_integration.py")
    
    elif observer['status'] != 'running':
        print("   ⚠️ Desktop Observer를 시작하세요!")
        print("   💡 Task: 'Observer: Start Telemetry (Background)'")
    
    elif data['status'] != 'collecting':
        print("   ⏳ 데이터 수집 대기 중...")
        print("   💡 몇 분 후 다시 확인하세요.")
    
    else:
        print("   🔄 시스템 준비 중...")
    
    print()

if __name__ == '__main__':
    main()
