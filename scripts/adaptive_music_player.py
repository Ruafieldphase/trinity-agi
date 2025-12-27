#!/usr/bin/env python3
"""
🎵 Adaptive Music Player

리듬 상태, 작업 컨텍스트, 시간대에 맞춰 자동으로 음악 재생
"""
import json
<<<<<<< HEAD
import os
=======
>>>>>>> origin/main
import random
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(r"C:\workspace\agi")
OUTPUTS = WORKSPACE / "outputs"
MUSIC_DB = WORKSPACE / "config" / "music_library.json"


# 음악 라이브러리 (YouTube 링크 기반)
MUSIC_LIBRARY = {
    "wake_up": {
        "name": "각성 (Wake Up)",
        "description": "높은 에너지, 빠른 템포 - 각성 및 활동 시작",
        "urls": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 예시 (교체 필요)
            "https://www.youtube.com/watch?v=ZbZSe6N_BXs",  # Happy
            "https://www.youtube.com/watch?v=y6Sxv-sUYtM",  # Thunderstruck
        ]
    },
    "focus": {
        "name": "집중 (Deep Focus)",
        "description": "Lo-fi, 클래식 - 깊은 집중 작업",
        "urls": [
            "https://www.youtube.com/watch?v=5qap5aO4i9A",  # Lofi Girl
            "https://www.youtube.com/watch?v=jfKfPfyJRdk",  # Lofi Hip Hop
            "https://www.youtube.com/watch?v=lTRiuFIWV54",  # Chill Beats
        ]
    },
    "coding": {
        "name": "코딩 (Coding Flow)",
        "description": "전자음악, Synthwave - 코딩 흐름",
        "urls": [
            "https://www.youtube.com/watch?v=MVPTGNGiI-4",  # Synthwave
            "https://www.youtube.com/watch?v=4xDzrJKXOOY",  # Cyberpunk
            "https://www.youtube.com/watch?v=MV_3Dpw-BRY",  # Chillstep
        ]
    },
    "rest": {
        "name": "휴식 (Rest & Recovery)",
        "description": "주변음, 자연음 - Glymphatic 배수 지원",
        "urls": [
            "https://www.youtube.com/watch?v=eKFTSSKCzWA",  # Rain
            "https://www.youtube.com/watch?v=wzjWIxXBs_s",  # Ocean
            "https://www.youtube.com/watch?v=nDq6TstdEi8",  # Nature
        ]
    },
    "transition": {
        "name": "전환 (Smooth Transition)",
        "description": "부드러운 음악 - 페이즈 전환",
        "urls": [
            "https://www.youtube.com/watch?v=nKxvDYHkfSY",  # Ambient
            "https://www.youtube.com/watch?v=UfcAVejslrU",  # Peaceful
            "https://www.youtube.com/watch?v=2OEL4P1Rz04",  # Meditation
        ]
    }
}


def detect_rhythm_phase() -> str:
    """현재 리듬 페이즈 감지"""
    rest_marker = OUTPUTS / "RHYTHM_REST_PHASE_20251107.md"
    if rest_marker.exists():
        from datetime import timedelta
        age = datetime.now() - datetime.fromtimestamp(rest_marker.stat().st_mtime)
        if age < timedelta(hours=2):
            return "REST"
    return "ACTIVE"


def detect_context() -> str:
    """작업 컨텍스트 감지 (간단한 휴리스틱)"""
    hour = datetime.now().hour
    
    # 시간대 기반 추론
    if 6 <= hour < 9:
        return "wake_up"
    elif 9 <= hour < 12 or 14 <= hour < 18:
        return "coding"  # 주요 작업 시간
    elif 12 <= hour < 14:
        return "focus"  # 점심 후 집중
    elif 18 <= hour < 22:
        return "transition"
    else:
        return "rest"


def select_music(phase: str = None, context: str = None) -> dict:
    """
    상황에 맞는 음악 선택
    
    우선순위:
    1. 명시적 context
    2. 리듬 페이즈
    3. 시간대 기반 추론
    """
    if context and context in MUSIC_LIBRARY:
        category = context
    else:
        rhythm = detect_rhythm_phase()
        if rhythm == "REST":
            category = "rest"
        else:
            category = detect_context()
    
    music_cat = MUSIC_LIBRARY.get(category, MUSIC_LIBRARY["focus"])
    selected_url = random.choice(music_cat["urls"])
    
    return {
        "category": category,
        "name": music_cat["name"],
        "description": music_cat["description"],
        "url": selected_url,
        "timestamp": datetime.now().isoformat()
    }


def play_music(url: str, browser: str = "comet"):
    """음악 재생 (브라우저에서 열기)"""
<<<<<<< HEAD
    # 기본은 "자동 팝업 금지": 음악은 제안(리포트)만 하고, 필요 시에만 명시적으로 연다.
    # - AGI_MUSIC_OPEN_BROWSER=1 일 때만 브라우저를 연다.
    open_browser = str(os.getenv("AGI_MUSIC_OPEN_BROWSER", "")).strip().lower() in ("1", "true", "yes", "on")
    if not open_browser:
        print("🎵 Music suggestion generated (browser not opened).")
        print(f"   URL: {url}")
        return

=======
>>>>>>> origin/main
    print(f"🎵 Opening music in {browser}...")
    
    if browser.lower() == "comet":
        # 코멧 브라우저 실행 (경로는 환경에 맞게 조정)
        # 기본적으로 webbrowser 모듈 사용
        webbrowser.open(url)
    else:
        webbrowser.open(url)
    
    print(f"✅ Music started: {url}")


def save_music_history(selection: dict):
    """음악 재생 기록 저장 (BQI 학습용)"""
    history_file = OUTPUTS / "music_playback_history.jsonl"
    
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(selection, ensure_ascii=False) + "\n")
    
    print(f"📝 History saved: {history_file}")


def main(category: str = None, url: str = None):
    print("🎵 Adaptive Music Player")
    print("=" * 50)
    
    if url:
        # 직접 URL 지정
        selection = {
            "category": "manual",
            "name": "Manual Selection",
            "description": "User-specified URL",
            "url": url,
            "timestamp": datetime.now().isoformat()
        }
    else:
        # 자동 선택
        rhythm = detect_rhythm_phase()
        context = detect_context()
        
        print(f"🌊 Rhythm Phase: {rhythm}")
        print(f"🎯 Context: {context}")
        print("")
        
        selection = select_music(phase=rhythm, context=category)
        
        print(f"📂 Selected Category: {selection['name']}")
        print(f"📝 Description: {selection['description']}")
        print(f"🔗 URL: {selection['url']}")
    
    # 음악 재생
    play_music(selection["url"])
    
    # 기록 저장
    save_music_history(selection)
    
    print("\n✅ Music playback initiated!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Adaptive Music Player")
    parser.add_argument("--category", choices=list(MUSIC_LIBRARY.keys()),
                        help="Music category to play")
    parser.add_argument("--url", help="Direct YouTube URL to play")
    
    args = parser.parse_args()
    main(category=args.category, url=args.url)
