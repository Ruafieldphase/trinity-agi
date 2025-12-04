#!/usr/bin/env python3
"""
🎵 Music Pattern Analyzer - Reaper Integration
음악 파일에서 리듬 패턴을 추출하여 AGI 시스템의 Rhythm State와 연결
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# librosa는 실제 분석에만 사용 (import는 실행 시점에)
# import librosa

WORKSPACE = Path(__file__).parent.parent
MUSIC_DIR = WORKSPACE / "music"
OUTPUT_DIR = WORKSPACE / "outputs"


def analyze_audio_file(file_path: Path) -> Dict[str, Any]:
    """
    오디오 파일 분석 (librosa 사용)
    
    Returns:
        tempo: BPM
        rhythm_pattern: 리듬 패턴 (strong/weak beats)
        energy: 에너지 레벨 (0-1)
        spectral_centroid: 음색 특성
    """
    try:
        import librosa
    except ImportError:
        print("⚠️ librosa not installed. Install with: pip install librosa")
        return None
    
    try:
        # Load audio file
        y, sr = librosa.load(str(file_path), duration=60)  # 첫 60초만 분석
        
        # 1. Tempo (BPM) 추출
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # 2. Energy (RMS)
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))
        
        # 3. Spectral Centroid (음색)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        brightness = float(np.mean(spectral_centroid))
        
        # 4. Rhythm Pattern (onset strength)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        rhythm_pattern = "strong" if np.std(onset_env) > np.mean(onset_env) else "steady"
        
        return {
            "tempo_bpm": float(tempo),
            "energy": energy,
            "brightness": brightness,
            "rhythm_pattern": rhythm_pattern,
            "beats_detected": len(beats),
            "analysis_duration": 60
        }
    
    except Exception as e:
        print(f"❌ Error analyzing {file_path.name}: {e}")
        return None


def map_to_rhythm_state(analysis: Dict[str, Any]) -> str:
    """
    음악 분석 결과를 AGI Rhythm State에 매핑
    
    Rhythm States:
    - deep_flow: 몰입 (빠른 템포, 높은 에너지)
    - active: 활동적 (중간 템포, 중간 에너지)
    - resting: 휴식 (느린 템포, 낮은 에너지)
    - transition: 전환 (불규칙한 패턴)
    """
    tempo = analysis.get("tempo_bpm", 120)
    energy = analysis.get("energy", 0.5)
    pattern = analysis.get("rhythm_pattern", "steady")
    
    if tempo > 140 and energy > 0.6:
        return "deep_flow"
    elif tempo > 100 and energy > 0.4:
        return "active"
    elif tempo < 80 or energy < 0.3:
        return "resting"
    else:
        return "transition"


def analyze_music_library():
    """
    전체 음악 라이브러리 분석 및 Rhythm State 매핑
    """
    print("🎼 Music Pattern Analysis Starting...\n")
    
    # Load existing music index
    music_index_path = OUTPUT_DIR / "music_index.json"
    if not music_index_path.exists():
        print("❌ music_index.json not found. Run build_music_index.ps1 first.")
        return
    
    with open(music_index_path, "r", encoding="utf-8") as f:
        music_index = json.load(f)
    
    results = []
    total = len(music_index.get("files", []))
    
    for idx, file_info in enumerate(music_index.get("files", []), 1):
        file_path = Path(file_info["path"])
        
        print(f"[{idx}/{total}] Analyzing: {file_path.name}")
        
        if not file_path.exists():
            print(f"  ⚠️ File not found: {file_path}")
            continue
        
        # Analyze audio
        analysis = analyze_audio_file(file_path)
        
        if analysis:
            # Map to rhythm state
            rhythm_state = map_to_rhythm_state(analysis)
            
            result = {
                "file": file_path.name,
                "path": str(file_path),
                "analysis": analysis,
                "rhythm_state": rhythm_state,
                "metadata": file_info.get("metadata", {})
            }
            
            results.append(result)
            
            print(f"  ✅ Tempo: {analysis['tempo_bpm']:.1f} BPM")
            print(f"  ✅ Energy: {analysis['energy']:.3f}")
            print(f"  ✅ Rhythm State: {rhythm_state}")
            print()
    
    # Save results
    output_path = OUTPUT_DIR / "music_pattern_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "analyzed_at": "2025-11-07T14:00:00+09:00",
            "total_files": len(results),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✨ Analysis complete! Saved to: {output_path}")
    
    # Generate summary report
    generate_summary_report(results)


def generate_summary_report(results: List[Dict[str, Any]]):
    """
    분석 결과 요약 리포트 생성
    """
    output_path = OUTPUT_DIR / "music_pattern_summary.md"
    
    # Rhythm state distribution
    rhythm_counts = {}
    for r in results:
        state = r.get("rhythm_state", "unknown")
        rhythm_counts[state] = rhythm_counts.get(state, 0) + 1
    
    # Tempo statistics
    tempos = [r["analysis"]["tempo_bpm"] for r in results if "analysis" in r]
    avg_tempo = np.mean(tempos) if tempos else 0
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 🎵 Music Pattern Analysis Summary\n\n")
        f.write(f"**Analyzed:** {len(results)} files\n\n")
        
        f.write("## Rhythm State Distribution\n\n")
        for state, count in sorted(rhythm_counts.items(), key=lambda x: -x[1]):
            f.write(f"- **{state}**: {count} files\n")
        
        f.write(f"\n## Tempo Statistics\n\n")
        f.write(f"- **Average BPM**: {avg_tempo:.1f}\n")
        f.write(f"- **Range**: {min(tempos):.1f} - {max(tempos):.1f}\n")
        
        f.write("\n## Top 5 High Energy Tracks\n\n")
        top_energy = sorted(results, key=lambda x: x["analysis"].get("energy", 0), reverse=True)[:5]
        for r in top_energy:
            f.write(f"- **{r['file']}** (Energy: {r['analysis']['energy']:.3f})\n")
        
        f.write("\n---\n")
        f.write("*Generated by Music Pattern Analyzer*\n")
    
    print(f"📄 Summary report saved to: {output_path}")


if __name__ == "__main__":
    try:
        analyze_music_library()
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
