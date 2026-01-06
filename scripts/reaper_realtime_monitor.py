#!/usr/bin/env python3
"""
🎵 Reaper Realtime Music Monitor
Reaper에서 재생 중인 음악을 실시간으로 분석하고 리듬 페이즈와 매칭합니다.
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("❌ requests 모듈 필요: pip install requests", file=sys.stderr)
    sys.exit(1)


class ReaperMonitor:
    """Reaper 실시간 모니터"""
    
    def __init__(self, reaper_url: str = "http://localhost:8080", 
                 rhythm_file: Path = None, interval: int = 30):
        self.reaper_url = reaper_url.rstrip('/')
        self.interval = interval
        self.rhythm_file = rhythm_file or Path("outputs/RHYTHM_REST_PHASE_latest.md")
        self.output_dir = Path("outputs/music_monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """현재 재생 중인 트랙 정보 가져오기 (Reaper Web Interface)"""
        try:
            # Reaper Web Interface API 호출
            response = requests.get(f"{self.reaper_url}/api/transport", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('playing'):
                    return {
                        'title': data.get('title', 'Unknown'),
                        'artist': data.get('artist', 'Unknown'),
                        'tempo': data.get('tempo', 120),
                        'position': data.get('position', 0),
                        'duration': data.get('duration', 0),
                        'playing': True
                    }
            return None
        except Exception as e:
            # Reaper가 꺼져있거나 연결 실패
            return None
    
    def get_current_rhythm_phase(self) -> str:
        """현재 리듬 페이즈 확인"""
        try:
            if self.rhythm_file.exists():
                content = self.rhythm_file.read_text(encoding='utf-8')
                if "DEEP_REST" in content or "deep_rest" in content:
                    return "deep_rest"
                elif "RESTING" in content or "resting" in content:
                    return "resting"
                elif "FLOWING" in content or "flowing" in content:
                    return "flowing"
                elif "WORKING" in content or "working" in content:
                    return "working"
            return "unknown"
        except Exception:
            return "unknown"
    
    def match_tempo_to_phase(self, tempo: float) -> str:
        """템포를 리듬 페이즈로 매핑"""
        if tempo < 80:
            return "deep_rest"
        elif tempo < 100:
            return "resting"
        elif tempo < 130:
            return "working"
        else:
            return "flowing"
    
    def check_compatibility(self, track: Dict[str, Any], current_phase: str) -> Dict[str, Any]:
        """현재 음악과 리듬 페이즈의 호환성 확인"""
        tempo = track.get('tempo', 120)
        inferred_phase = self.match_tempo_to_phase(tempo)
        
        compatible = (inferred_phase == current_phase)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "track": track,
            "current_rhythm_phase": current_phase,
            "inferred_phase": inferred_phase,
            "tempo_bpm": tempo,
            "compatible": compatible,
            "recommendation": None
        }
        
        if not compatible:
            result["recommendation"] = f"현재 페이즈({current_phase})에 맞지 않습니다. {inferred_phase} 음악이 재생 중입니다."
            
            # 추천 템포 범위
            if current_phase == "deep_rest":
                result["suggested_tempo_range"] = "60-80 BPM"
            elif current_phase == "resting":
                result["suggested_tempo_range"] = "80-100 BPM"
            elif current_phase == "working":
                result["suggested_tempo_range"] = "100-130 BPM"
            elif current_phase == "flowing":
                result["suggested_tempo_range"] = "130+ BPM"
        
        return result
    
    def save_result(self, result: Dict[str, Any]):
        """결과 저장"""
        # 최신 결과 (덮어쓰기)
        latest_file = self.output_dir / "music_rhythm_match_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 히스토리 (추가)
        history_file = self.output_dir / "music_rhythm_match_history.jsonl"
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    def print_status(self, result: Dict[str, Any]):
        """상태 출력"""
        track = result['track']
        print(f"\n🎵 현재 재생 중: {track['title']} - {track['artist']}")
        print(f"   템포: {result['tempo_bpm']:.1f} BPM")
        print(f"   현재 리듬 페이즈: {result['current_rhythm_phase']}")
        print(f"   추론된 페이즈: {result['inferred_phase']}")
        
        if result['compatible']:
            print(f"   ✅ 호환성: 매칭됨")
        else:
            print(f"   ⚠️ 호환성: 불일치")
            if result.get('recommendation'):
                print(f"   💡 추천: {result['recommendation']}")
                print(f"   💡 권장 템포: {result.get('suggested_tempo_range', 'N/A')}")
    
    def run_once(self) -> bool:
        """1회 체크"""
        print(f"🔍 Reaper 상태 확인 중... ({self.reaper_url})")
        
        track = self.get_current_track()
        if not track:
            print("   ⏸️ 재생 중인 음악 없음 (또는 Reaper 오프라인)")
            return False
        
        current_phase = self.get_current_rhythm_phase()
        result = self.check_compatibility(track, current_phase)
        
        self.save_result(result)
        self.print_status(result)
        
        return result['compatible']
    
    def run_loop(self):
        """무한 루프 모니터링"""
        print(f"🔄 실시간 모니터링 시작 (간격: {self.interval}초)")
        print(f"   Reaper URL: {self.reaper_url}")
        print(f"   리듬 파일: {self.rhythm_file}")
        print(f"   Ctrl+C로 중지\n")
        
        try:
            while True:
                self.run_once()
                print(f"\n⏳ {self.interval}초 대기...")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n\n🛑 모니터링 중지됨")


def main():
    parser = argparse.ArgumentParser(description='🎵 Reaper Realtime Music Monitor')
    parser.add_argument('--url', default='http://localhost:8080',
                        help='Reaper Web Interface URL (기본: http://localhost:8080)')
    parser.add_argument('--rhythm-file', type=Path,
                        help='리듬 페이즈 파일 경로')
    parser.add_argument('--interval', type=int, default=30,
                        help='체크 간격(초) (기본: 30)')
    parser.add_argument('--once', action='store_true',
                        help='1회만 실행')
    
    args = parser.parse_args()
    
    monitor = ReaperMonitor(
        reaper_url=args.url,
        rhythm_file=args.rhythm_file,
        interval=args.interval
    )
    
    if args.once:
        compatible = monitor.run_once()
        return 0 if compatible else 1
    else:
        monitor.run_loop()
        return 0


if __name__ == '__main__':
    sys.exit(main())
