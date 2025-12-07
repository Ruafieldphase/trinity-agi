#!/usr/bin/env python3
"""
Windows-Linux Sync Health Monitor
실시간으로 동기화 상태를 모니터링하고 문제를 감지합니다
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

class SyncHealthMonitor:
    def __init__(self):
        self.outputs_dir = Path("c:/workspace/agi/outputs")
        self.thought_stream = self.outputs_dir / "thought_stream_latest.json"
        self.feeling = self.outputs_dir / "feeling_latest.json"
        
    def check_file_freshness(self, filepath: Path, max_age_minutes: int) -> dict:
        """파일이 최근에 업데이트되었는지 확인"""
        if not filepath.exists():
            return {
                "status": "missing",
                "message": f"파일이 존재하지 않습니다",
                "healthy": False
            }
        
        stat = filepath.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        age = datetime.now() - mtime
        age_minutes = age.total_seconds() / 60
        
        is_fresh = age_minutes <= max_age_minutes
        
        return {
            "status": "fresh" if is_fresh else "stale",
            "last_modified": mtime.isoformat(),
            "age_minutes": int(age_minutes),
            "size_bytes": stat.st_size,
            "healthy": is_fresh,
            "message": f"{'✅ 최신' if is_fresh else f'⚠️ {int(age_minutes)}분 전 업데이트'}"
        }
    
    def check_file_content(self, filepath: Path) -> dict:
        """파일 내용의 유효성 확인"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 타임스탬프 확인
            timestamp_str = data.get('timestamp', '')
            if timestamp_str:
                file_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                age = datetime.now() - file_timestamp
                age_minutes = age.total_seconds() / 60
                
                return {
                    "valid": True,
                    "timestamp": timestamp_str,
                    "age_minutes": int(age_minutes),
                    "healthy": age_minutes <= 5,  # 5분 이내면 건강
                    "message": f"내부 타임스탬프: {int(age_minutes)}분 전"
                }
            else:
                return {
                    "valid": True,
                    "timestamp": None,
                    "healthy": False,
                    "message": "타임스탬프 없음"
                }
                
        except json.JSONDecodeError:
            return {
                "valid": False,
                "healthy": False,
                "message": "❌ JSON 파싱 실패"
            }
        except Exception as e:
            return {
                "valid": False,
                "healthy": False,
                "message": f"❌ 오류: {e}"
            }
    
    def generate_report(self):
        """동기화 상태 보고서 생성"""
        print("=" * 70)
        print("🔍 Windows-Linux 동기화 상태 모니터")
        print("=" * 70)
        print(f"체크 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Thought Stream 체크
        print("1️⃣ thought_stream_latest.json")
        print("-" * 70)
        freshness = self.check_file_freshness(self.thought_stream, max_age_minutes=5)
        print(f"   파일 상태: {freshness['message']}")
        if freshness['healthy']:
            content = self.check_file_content(self.thought_stream)
            if content['valid']:
                print(f"   {content['message']}")
                print(f"   평가: {'✅ 정상' if content['healthy'] else '⚠️ 주의'}")
            else:
                print(f"   {content['message']}")
        else:
            print(f"   평가: ❌ 동기화 문제")
        
        print()
        
        # Feeling 체크
        print("2️⃣ feeling_latest.json")
        print("-" * 70)
        freshness = self.check_file_freshness(self.feeling, max_age_minutes=5)
        print(f"   파일 상태: {freshness['message']}")
        if freshness['status'] != 'missing':
            content = self.check_file_content(self.feeling)
            if content['valid']:
                print(f"   {content['message']}")
                print(f"   평가: {'✅ 정상' if content['healthy'] else '⚠️ 주의'}")
            else:
                print(f"   {content['message']}")
        else:
            print(f"   평가: ❌ 동기화 문제")
        
        print()
        print("=" * 70)
        
        # 전체 평가
        thought_healthy = self.check_file_freshness(self.thought_stream, 5)['healthy']
        feeling_healthy = self.check_file_freshness(self.feeling, 5)['healthy']
        
        if thought_healthy and feeling_healthy:
            print("✅ 전체 평가: 정상 - 모든 파일이 동기화되고 있습니다")
        elif thought_healthy and not feeling_healthy:
            print("⚠️ 전체 평가: 부분 정상 - feeling_latest.json 동기화 문제")
            print("   권장사항: Linux Rhythm 서비스 로그 확인 필요")
        else:
            print("❌ 전체 평가: 비정상 - 동기화 문제 발생")
            print("   권장사항: sync_rhythm_from_linux.py 재시작 필요")
        
        print("=" * 70)
    
    def monitor_loop(self, interval_seconds=60):
        """주기적으로 상태 모니터링"""
        print("🔄 모니터링 루프 시작 (Ctrl+C로 종료)")
        print()
        
        try:
            while True:
                self.generate_report()
                print(f"\n⏳ {interval_seconds}초 후 다시 체크합니다...\n")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\n👋 모니터링 종료")

if __name__ == "__main__":
    import sys
    
    monitor = SyncHealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        monitor.monitor_loop()
    else:
        monitor.generate_report()
        print("\n💡 Tip: 지속적으로 모니터링하려면 --loop 옵션을 사용하세요")
        print("   예: python scripts/sync_health_monitor.py --loop")
