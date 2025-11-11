#!/usr/bin/env python3
"""
🎵 Reaper Music Pattern Analyzer
음악의 리듬, 주파수, 에너지 패턴을 추출하여 AGI 시스템의 리듬과 매핑합니다.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import librosa
    import numpy as np
except ImportError as e:
    print(f"❌ Required library missing: {e}", file=sys.stderr)
    print("Install with: pip install librosa numpy soundfile", file=sys.stderr)
    sys.exit(1)


def analyze_music_pattern(audio_path: Path, output_dir: Path):
    """음악 파일에서 리듬, 주파수, 에너지 패턴 추출"""
    print(f"🎵 분석 시작: {audio_path.name}")
    
    # 1. 오디오 로드
    try:
        y, sr = librosa.load(str(audio_path), sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        print(f"   샘플레이트: {sr} Hz")
        print(f"   재생시간: {duration:.2f}초")
    except Exception as e:
        print(f"❌ 오디오 로드 실패: {e}")
        return None
    
    # 2. 템포(BPM) 및 비트 추출
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    print(f"   템포: {tempo:.1f} BPM")
    print(f"   비트: {len(beat_times)}개")
    
    # 3. 스펙트럼 중심 (주파수 분포)
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    avg_centroid = np.mean(spectral_centroids)
    print(f"   평균 주파수 중심: {avg_centroid:.0f} Hz")
    
    # 4. 에너지 (RMS)
    rms = librosa.feature.rms(y=y)[0]
    avg_energy = np.mean(rms)
    energy_variance = np.var(rms)
    print(f"   평균 에너지: {avg_energy:.4f}")
    print(f"   에너지 분산: {energy_variance:.6f}")
    
    # 5. MFCC (음색 특성)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    avg_mfccs = np.mean(mfccs, axis=1).tolist()
    
    # 6. 제로 크로싱 비율 (음의 변화 빈도)
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    avg_zcr = np.mean(zcr)
    print(f"   제로 크로싱 비율: {avg_zcr:.4f}")
    
    # 7. 리듬 상태 추론
    rhythm_state = infer_rhythm_state(tempo, avg_energy, energy_variance, avg_centroid)
    print(f"   추론된 리듬 상태: {rhythm_state}")
    
    # 8. 결과 저장
    result = {
        "file": audio_path.name,
        "analyzed_at": datetime.now().isoformat(),
        "duration_sec": float(duration),
        "sample_rate": int(sr),
        "tempo_bpm": float(tempo),
        "beats_count": int(len(beat_times)),
        "beat_times": beat_times.tolist()[:50],  # 첫 50개만
        "spectral_centroid_hz": float(avg_centroid),
        "energy": {
            "mean": float(avg_energy),
            "variance": float(energy_variance),
            "normalized": float(avg_energy / (energy_variance + 0.0001))
        },
        "mfcc_features": avg_mfccs,
        "zero_crossing_rate": float(avg_zcr),
        "inferred_rhythm_state": rhythm_state
    }
    
    output_file = output_dir / f"{audio_path.stem}_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 분석 완료: {output_file}")
    return result


def infer_rhythm_state(tempo, energy, energy_var, centroid):
    """템포, 에너지, 주파수 패턴으로 리듬 상태 추론"""
    # 단순한 휴리스틱 기반 추론 (나중에 ML 모델로 대체 가능)
    if tempo < 80 and energy < 0.05:
        return "deep_rest"
    elif tempo < 100 and energy < 0.1:
        return "resting"
    elif 100 <= tempo < 130 and energy < 0.2:
        return "working"
    elif tempo >= 130 or energy >= 0.2:
        return "flowing"
    else:
        return "unknown"


def batch_analyze(music_dir: Path, output_dir: Path, limit: int = None):
    """음악 디렉토리 전체 분석"""
    audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    audio_files = [f for f in music_dir.rglob('*') if f.suffix.lower() in audio_extensions]
    
    if limit:
        audio_files = audio_files[:limit]
    
    print(f"📂 분석할 파일: {len(audio_files)}개")
    
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}]")
        result = analyze_music_pattern(audio_file, output_dir)
        if result:
            results.append(result)
    
    # 전체 요약 저장
    summary = {
        "analyzed_at": datetime.now().isoformat(),
        "total_files": len(results),
        "files": results
    }
    
    summary_file = output_dir / "music_analysis_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 전체 분석 완료: {summary_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description='🎵 Reaper Music Pattern Analyzer')
    parser.add_argument('--file', type=Path, help='단일 파일 분석')
    parser.add_argument('--dir', type=Path, default=Path('C:/workspace/agi/music'), 
                        help='음악 디렉토리 (기본: C:/workspace/agi/music)')
    parser.add_argument('--output', type=Path, default=Path('C:/workspace/agi/outputs/music_analysis'),
                        help='출력 디렉토리')
    parser.add_argument('--limit', type=int, help='분석할 파일 수 제한')
    
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    args.output.mkdir(parents=True, exist_ok=True)
    
    if args.file:
        # 단일 파일 분석
        if not args.file.exists():
            print(f"❌ 파일을 찾을 수 없음: {args.file}")
            return 1
        analyze_music_pattern(args.file, args.output)
    else:
        # 디렉토리 전체 분석
        if not args.dir.exists():
            print(f"❌ 디렉토리를 찾을 수 없음: {args.dir}")
            return 1
        batch_analyze(args.dir, args.output, args.limit)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
