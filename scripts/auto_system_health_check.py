#!/usr/bin/env python3
"""
자동 시스템 건강 체크 및 복구

정기적으로 실행되어 전체 시스템 상태를 점검하고 필요시 자동 복구를 수행합니다.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"

def check_and_log(name: str, check_func, fix_func=None):
    """시스템 체크 및 자동 수정"""
    try:
        status = check_func()
        if not status and fix_func:
            print(f"❌ {name} - 문제 감지, 자동 수정 시도...")
            fix_func()
            status = check_func()
            if status:
                print(f"✅ {name} - 자동 수정 완료")
                return True
            else:
                print(f"⚠️ {name} - 자동 수정 실패")
                return False
        elif status:
            print(f"✅ {name} - 정상")
            return True
        else:
            print(f"❌ {name} - 문제 있음")
            return False
    except Exception as e:
        print(f"❌ {name} - 체크 실패: {e}")
        return False

def check_meta_supervisor():
    """Meta Supervisor 상태 체크"""
    # 최근 30분 내에 실행되었는지 확인
    report = OUTPUTS_DIR / "meta_supervision_report.md"
    if not report.exists():
        return False
    
    import time
    age_minutes = (time.time() - report.stat().st_mtime) / 60
    return age_minutes < 35  # 30분 + 5분 여유

def fix_meta_supervisor():
    """Meta Supervisor 실행"""
    subprocess.run([sys.executable, "scripts/meta_supervisor.py"], 
                   cwd=WORKSPACE_ROOT, 
                   capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)

def check_motor_reflex():
    """Motor Reflex Loop 실행 여부"""
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and 'motor_reflex_loop.py' in ' '.join(cmdline):
                return True
        except:
            pass
    return False

def fix_motor_reflex():
    """Motor Reflex Loop 시작"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen([sys.executable, "scripts/motor_reflex_loop.py"],
                     cwd=WORKSPACE_ROOT,
                     startupinfo=startupinfo,
                     creationflags=subprocess.CREATE_NO_WINDOW)

def check_active_learning():
    """Active Learning 활성화 여부"""
    diagnostic = OUTPUTS_DIR / "system_integration_diagnostic_latest.json"
    if not diagnostic.exists():
        return False
    
    with open(diagnostic, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('modules', {}).get('reward_system', {}).get('active_learning', False)

def check_consciousness_bridge():
    """Consciousness Bridge 최신성 체크"""
    bridge = OUTPUTS_DIR / "consciousness_bridge_report.json"
    if not bridge.exists():
        return False
    
    import time
    age_hours = (time.time() - bridge.stat().st_mtime) / 3600
    return age_hours < 2  # 2시간 이내

def fix_consciousness_bridge():
    """Consciousness Bridge 업데이트"""
    subprocess.run([sys.executable, "scripts/consciousness_bridge.py"],
                   cwd=WORKSPACE_ROOT,
                   capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)

def check_trinity_stats():
    """Trinity 통계 최신성 체크"""
    stats = OUTPUTS_DIR / "trinity/trinity_statistics.json"
    if not stats.exists():
        return False
    
    import time
    age_hours = (time.time() - stats.stat().st_mtime) / 3600
    return age_hours < 24  # 24시간 이내

def fix_trinity_stats():
    """Trinity 통계 업데이트"""
    subprocess.run([sys.executable, "scripts/trinity_stats.py"],
                   cwd=WORKSPACE_ROOT,
                   capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)

def main():
    """자동 시스템 건강 체크 메인"""
    print("="*60)
    print("🏥 자동 시스템 건강 체크")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # 핵심 시스템 체크
    results['meta_supervisor'] = check_and_log(
        "Meta Supervisor (30분마다)",
        check_meta_supervisor,
        fix_meta_supervisor
    )
    
    results['motor_reflex'] = check_and_log(
        "Motor Reflex Loop (면역시스템)",
        check_motor_reflex,
        fix_motor_reflex
    )
    
    results['active_learning'] = check_and_log(
        "Active Learning",
        check_active_learning
    )
    
    results['consciousness_bridge'] = check_and_log(
        "Consciousness Bridge (의식)",
        check_consciousness_bridge,
        fix_consciousness_bridge
    )
    
    results['trinity_stats'] = check_and_log(
        "Trinity Statistics",
        check_trinity_stats,
        fix_trinity_stats
    )
    
    # 결과 저장
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": results,
        "overall_health": sum(results.values()) / len(results) * 100
    }
    
    with open(OUTPUTS_DIR / "auto_health_check_latest.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print(f"📊 전체 건강도: {report['overall_health']:.1f}%")
    print(f"✅ 정상: {sum(results.values())}/{len(results)}")
    print("="*60)
    
    return 0 if report['overall_health'] >= 60 else 1

if __name__ == "__main__":
    sys.exit(main())
