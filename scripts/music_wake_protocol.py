#!/usr/bin/env python3
"""
🎵 Music-Triggered Wake Protocol

음악 재생 감지 → Glymphatic 배수 대기 → 자연스러운 각성 트리거
"""
import json
import time
import subprocess
from pathlib import Path
from workspace_root import get_workspace_root
from datetime import datetime, timedelta

WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"
RHYTHM_DIR = OUTPUTS

MUSIC_DETECT_SCRIPT = WORKSPACE / "scripts" / "detect_audio_playback.ps1"
GLYMPHATIC_GRACE_SECONDS = 15  # 음악 시작 후 배수 완료 대기 시간


def detect_music_playing() -> dict:
    """음악 재생 상태 감지"""
    if not MUSIC_DETECT_SCRIPT.exists():
        return {"IsPlaying": False, "SessionCount": 0}
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(MUSIC_DETECT_SCRIPT), "-Json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return {"IsPlaying": False, "SessionCount": 0}
    except Exception as e:
        print(f"⚠️ Music detection failed: {e}")
        return {"IsPlaying": False, "SessionCount": 0}


def check_rhythm_phase() -> str:
    """현재 리듬 페이즈 확인"""
    rest_marker = RHYTHM_DIR / "RHYTHM_REST_PHASE_20251107.md"
    if rest_marker.exists():
        age = datetime.now() - datetime.fromtimestamp(rest_marker.stat().st_mtime)
        if age < timedelta(hours=2):
            return "REST"
    return "ACTIVE"


def play_wake_music():
    """각성용 음악 자동 재생"""
    music_player = WORKSPACE / "scripts" / "adaptive_music_player.py"
    if not music_player.exists():
        print("   ⚠️ Adaptive music player not found")
        return False
    
    try:
        print("   🎵 Playing wake-up music...")
        subprocess.run(
            ["python", str(music_player), "--category", "wake_up"],
            timeout=10
        )
        return True
    except Exception as e:
        print(f"   ⚠️ Music playback failed: {e}")
        return False


def trigger_wake_sequence(auto_play_music: bool = True):
    """각성 시퀀스 트리거"""
    print("🌅 Wake sequence triggered...")
    
    # 0. 음악 자동 재생 (선택적)
    if auto_play_music:
        play_wake_music()
    
    # 1. Glymphatic cleanup signal
    cleanup_signal = OUTPUTS / "glymphatic_cleanup_complete.json"
    cleanup_signal.write_text(json.dumps({
        "triggered_by": "music",
        "timestamp": datetime.now().isoformat(),
        "grace_period_seconds": GLYMPHATIC_GRACE_SECONDS,
        "auto_music_played": auto_play_music
    }, indent=2))
    
    # 2. 리듬 상태 업데이트 (ACTIVE로 전환 준비)
    rhythm_signal = OUTPUTS / "rhythm_wake_signal.json"
    rhythm_signal.write_text(json.dumps({
        "signal": "WAKE_BY_MUSIC",
        "timestamp": datetime.now().isoformat(),
        "ready_for_active_phase": True
    }, indent=2))
    
    print("✅ Wake signals sent")
    print(f"   - Glymphatic grace: {GLYMPHATIC_GRACE_SECONDS}s")
    print(f"   - Rhythm transition: REST → ACTIVE")


def main():
    print("🎵 Music-Triggered Wake Protocol")
    print("=" * 50)
    
    music_state = detect_music_playing()
    rhythm_phase = check_rhythm_phase()
    
    print(f"🎶 Music Playing: {music_state.get('IsPlaying', False)}")
    print(f"🌊 Current Phase: {rhythm_phase}")
    
    if music_state.get("IsPlaying") and rhythm_phase == "REST":
        print("\n🚀 Conditions met for wake protocol")
        print(f"   - Waiting {GLYMPHATIC_GRACE_SECONDS}s for glymphatic drainage...")
        time.sleep(GLYMPHATIC_GRACE_SECONDS)
        trigger_wake_sequence()
        
        # 자율 목표 실행 추천
        print("\n💡 Recommended next action:")
        print("   → Run autonomous goal executor")
        print("   → VS Code Task: '🎯 Goal: Execute + Open Tracker'")
    else:
        print("\n⏸️ No wake trigger needed")
        if not music_state.get("IsPlaying"):
            print("   Reason: No music detected")
        if rhythm_phase != "REST":
            print(f"   Reason: Already in {rhythm_phase} phase")
    
    # 상태 저장
    state_file = OUTPUTS / "music_wake_protocol_state.json"
    state_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "music_playing": music_state.get("IsPlaying", False),
        "rhythm_phase": rhythm_phase,
        "wake_triggered": music_state.get("IsPlaying") and rhythm_phase == "REST"
    }, indent=2))
    
    print(f"\n📁 State saved: {state_file}")


if __name__ == "__main__":
    main()
