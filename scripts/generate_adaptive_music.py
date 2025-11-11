#!/usr/bin/env python3
"""
Reaper 음악 자동 생성 시스템
리듬 페이즈에 최적화된 음악을 Reaper로 생성하고 렌더링
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 경로 설정
WORKSPACE = Path(__file__).parent.parent
REAPER_PROJECTS = WORKSPACE / "reaper_projects"
REAPER_RENDERS = WORKSPACE / "outputs" / "generated_music"
REAPER_TEMPLATES = REAPER_PROJECTS / "templates"

REAPER_PROJECTS.mkdir(exist_ok=True)
REAPER_RENDERS.mkdir(exist_ok=True)
REAPER_TEMPLATES.mkdir(exist_ok=True)

# 페이즈별 음악 파라미터
PHASE_MUSIC_PARAMS = {
    "wake_up": {
        "bpm": 135,
        "energy": "HIGH",
        "duration_minutes": 3,
        "instruments": ["synth_lead", "bass", "drums", "pad"],
        "frequency_range": "120-8000Hz",  # RAS 자극에 효과적
        "rhythm_pattern": "4/4_energetic",
        "key": "C_major",
        "description": "각성 촉진용 - 높은 에너지, 빠른 템포"
    },
    "coding": {
        "bpm": 120,
        "energy": "MEDIUM",
        "duration_minutes": 15,
        "instruments": ["synth_arp", "bass", "light_drums", "ambient"],
        "frequency_range": "80-6000Hz",
        "rhythm_pattern": "4/4_steady",
        "key": "A_minor",
        "description": "코딩 흐름 - 안정적 리듬, 중간 에너지"
    },
    "focus": {
        "bpm": 75,
        "energy": "LOW",
        "duration_minutes": 20,
        "instruments": ["piano", "strings", "ambient", "soft_pad"],
        "frequency_range": "60-4000Hz",
        "rhythm_pattern": "3/4_gentle",
        "key": "D_minor",
        "description": "깊은 집중 - 부드러운 리듬, 낮은 에너지"
    },
    "rest": {
        "bpm": 50,
        "energy": "VERY_LOW",
        "duration_minutes": 10,
        "instruments": ["pad", "ambient", "nature_sounds"],
        "frequency_range": "40-2000Hz",
        "rhythm_pattern": "free_flowing",
        "key": "G_major",
        "description": "휴식/회복 - Glymphatic 배수 촉진"
    },
    "transition": {
        "bpm": 90,
        "energy": "LOW",
        "duration_minutes": 5,
        "instruments": ["piano", "pad", "light_perc"],
        "frequency_range": "60-5000Hz",
        "rhythm_pattern": "4/4_relaxed",
        "key": "F_major",
        "description": "페이즈 전환 - 부드러운 이동"
    }
}


def generate_reaper_project(category: str, output_path: Path) -> Dict:
    """Reaper 프로젝트 파일 (.rpp) 생성"""
    params = PHASE_MUSIC_PARAMS.get(category)
    if not params:
        raise ValueError(f"Unknown category: {category}")
    
    # Reaper RPP 파일 형식 (간소화 버전)
    # 실제로는 GUI에서 템플릿 만들고 여기서 파라미터만 수정
    rpp_content = f"""<REAPER_PROJECT 0.1 "7.0" 1699999999
  RIPPLE 0
  GROUPOVERRIDE 0 0 0
  AUTOXFADE 1
  ENVATTACH 1
  POOLEDENVATTACH 0
  MIXERUIFLAGS 11 48
  PEAKGAIN 1
  FEEDBACK 0
  PANLAW 1
  PROJOFFS 0 0 0
  MAXPROJLEN 0 600
  GRID 3199 8 1 8 1 0 0 0
  TIMEMODE 1 5 -1 30 0 0 -1
  VIDEO_CONFIG 0 0 256
  PANMODE 3
  CURSOR 0
  ZOOM 100 0 0
  VZOOMEX 6 0
  USE_REC_CFG 0
  RECMODE 1
  SMPTESYNC 0 30 100 40 1000 300 0 0 1 0 0
  LOOP 0
  LOOPGRAN 0 4
  RECORD_PATH "" ""
  <RECORD_CFG
    ZXZhdxgAAQ==
  >
  <APPLYFX_CFG
  >
  RENDER_FILE ""
  RENDER_PATTERN ""
  RENDER_FMT 0 2 0
  RENDER_1X 0
  RENDER_RANGE 1 0 0 18 1000
  RENDER_RESAMPLE 3 0 1
  RENDER_ADDTOPROJ 0
  RENDER_STEMS 0
  RENDER_DITHER 0
  TIMELOCKMODE 1
  TEMPOENVLOCKMODE 1
  ITEMMIX 0
  DEFPITCHMODE 589824 0
  TAKELANE 1
  SAMPLERATE 44100 0 0
  <RENDER_CFG
    ZXZhdxgAAQ==
  >
  LOCK 1
  <METRONOME 6 2
    VOL 0.25 0.125
    FREQ 800 1600 1
    BEATLEN 4
    SAMPLES "" ""
    PATTERN 2863311530 2863311529
    MULT 1
  >
  GLOBAL_AUTO -1
  TEMPO {params['bpm']} 4 4
  PLAYRATE 1 0 0.25 4
  SELECTION 0 0
  SELECTION2 0 0
  MASTERAUTOMODE 0
  MASTERTRACKHEIGHT 0 0
  MASTERPEAKCOL 16576
  MASTERMUTESOLO 0
  MASTERTRACKVIEW 0 0.6667 0.5 0.5 -1 -1 -1 0 0 0 -1 -1 0
  MASTER_VOLUME 1 0 -1 -1 1
  MASTER_PANMODE 3
  MASTER_FX 1
  MASTER_SEL 0
  <MASTERPLAYSPEEDENV
    EGUID {{generated-guid}}
    ACT 0 -1
    VIS 0 1 1
    LANEHEIGHT 0 0
    ARM 0
    DEFSHAPE 0 -1 -1
  >
  <TEMPOENVEX
    EGUID {{generated-tempo-guid}}
    ACT 1 -1
    VIS 1 0 1
    LANEHEIGHT 0 0
    ARM 0
    DEFSHAPE 1 -1 -1
  >
  <PROJBAY
  >
>
"""
    
    # 프로젝트 파일 저장
    output_path.write_text(rpp_content)
    
    metadata = {
        "category": category,
        "params": params,
        "project_file": str(output_path),
        "generated_at": datetime.now().isoformat()
    }
    
    return metadata


def create_render_config(category: str, project_path: Path, output_audio: Path) -> Dict:
    """Reaper 렌더링 설정 생성"""
    params = PHASE_MUSIC_PARAMS[category]
    
    render_config = {
        "project": str(project_path),
        "output": str(output_audio),
        "format": "WAV",  # 또는 MP3
        "sample_rate": 44100,
        "bit_depth": 24,
        "duration_seconds": params["duration_minutes"] * 60,
        "bpm": params["bpm"],
        "category": category
    }
    
    return render_config


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate adaptive music with Reaper")
    parser.add_argument("--category", choices=list(PHASE_MUSIC_PARAMS.keys()),
                        default="coding", help="Music category to generate")
    parser.add_argument("--list", action="store_true", help="List all categories")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n🎼 Available Music Categories:")
        print("=" * 60)
        for cat, params in PHASE_MUSIC_PARAMS.items():
            print(f"\n{cat.upper()}")
            print(f"  BPM: {params['bpm']}")
            print(f"  Energy: {params['energy']}")
            print(f"  Duration: {params['duration_minutes']} min")
            print(f"  Instruments: {', '.join(params['instruments'])}")
            print(f"  Description: {params['description']}")
        return
    
    print(f"\n🎵 Generating {args.category.upper()} music...")
    print("=" * 60)
    
    # 프로젝트 파일 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"{args.category}_{timestamp}"
    project_path = REAPER_PROJECTS / f"{project_name}.rpp"
    
    metadata = generate_reaper_project(args.category, project_path)
    
    print(f"✅ Project created: {project_path}")
    print(f"   BPM: {metadata['params']['bpm']}")
    print(f"   Energy: {metadata['params']['energy']}")
    print(f"   Duration: {metadata['params']['duration_minutes']} min")
    
    # 렌더링 설정
    output_audio = REAPER_RENDERS / f"{project_name}.wav"
    render_config = create_render_config(args.category, project_path, output_audio)
    
    render_config_path = REAPER_PROJECTS / f"{project_name}_render.json"
    render_config_path.write_text(json.dumps(render_config, indent=2))
    
    print(f"\n📝 Render config saved: {render_config_path}")
    print(f"🎧 Output audio: {output_audio}")
    
    print("\n⚠️ Next steps:")
    print("  1. Open the project in Reaper")
    print(f"     > reaper '{project_path}'")
    print("  2. Add instruments and compose")
    print("  3. Render to WAV")
    print("  4. Use in adaptive_music_player.py")
    
    # 메타데이터 저장
    metadata_path = REAPER_PROJECTS / f"{project_name}_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    
    print(f"\n✅ Generation complete!")
    print(f"   Project: {project_path}")
    print(f"   Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
