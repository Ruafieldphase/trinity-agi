#!/usr/bin/env python3
"""
Reaper Music Pattern Analyzer
Extracts musical patterns and information-theoretic properties from audio files

Requirements:
- Reaper with Python ReaScript support
- librosa (audio analysis)
- numpy
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import numpy as np
    import librosa
    # librosa.display는 시각화용이므로 생략
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Install with: pip install librosa numpy soundfile")
    print(f"   Python: {sys.executable}")
    sys.exit(1)


class MusicPatternAnalyzer:
    """Analyze music patterns for AGI rhythm system"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        
    def analyze_file(self, audio_path: str) -> Dict:
        """Complete analysis of an audio file"""
        print(f"\n🎵 Analyzing: {Path(audio_path).name}")
        
        # Load audio
        try:
            y, sr = librosa.load(audio_path, sr=self.sr, mono=True)
        except Exception as e:
            return {"error": str(e), "path": audio_path}
        
        # Basic properties
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Tempo and beat
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        
        # MFCCs (timbre)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Chroma (harmonic content)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Information theory metrics
        entropy = self._calculate_entropy(y)
        complexity = self._calculate_complexity(mfccs)
        
        # Rhythm pattern
        rhythm_pattern = self._extract_rhythm_pattern(beats, duration)
        
        # Key detection (simple)
        key = self._detect_key(chroma)
        
        result = {
            "path": audio_path,
            "filename": Path(audio_path).name,
            "analyzed_at": datetime.now().isoformat(),
            "basic_properties": {
                "duration_seconds": float(duration),
                "sample_rate": sr,
                "total_samples": len(y)
            },
            "tempo_rhythm": {
                "tempo_bpm": float(tempo),
                "beat_count": len(beats),
                "beats_per_second": len(beats) / duration if duration > 0 else 0,
                "rhythm_regularity": self._calculate_regularity(beats)
            },
            "spectral_features": {
                "mean_spectral_centroid": float(np.mean(spectral_centroids)),
                "std_spectral_centroid": float(np.std(spectral_centroids)),
                "mean_spectral_rolloff": float(np.mean(spectral_rolloff)),
                "mean_zero_crossing_rate": float(np.mean(zero_crossing_rate))
            },
            "timbre": {
                "mfcc_means": [float(x) for x in np.mean(mfccs, axis=1)],
                "mfcc_stds": [float(x) for x in np.std(mfccs, axis=1)]
            },
            "harmonic": {
                "detected_key": key,
                "chroma_mean": [float(x) for x in np.mean(chroma, axis=1)]
            },
            "energy": {
                "mean_rms": float(np.mean(rms)),
                "max_rms": float(np.max(rms)),
                "energy_variance": float(np.var(rms))
            },
            "information_theory": {
                "entropy": entropy,
                "complexity": complexity,
                "pattern_density": len(beats) / duration if duration > 0 else 0
            },
            "rhythm_pattern": rhythm_pattern,
            "agi_mapping": self._map_to_agi_rhythm(tempo, entropy, complexity)
        }
        
        return result
    
    def _calculate_entropy(self, y: np.ndarray) -> float:
        """Calculate audio entropy (information theory)"""
        # Normalize to [0, 1]
        y_norm = (y - np.min(y)) / (np.max(y) - np.min(y) + 1e-10)
        
        # Histogram-based entropy
        hist, _ = np.histogram(y_norm, bins=100, density=True)
        hist = hist[hist > 0]  # Remove zeros
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        return float(entropy)
    
    def _calculate_complexity(self, mfccs: np.ndarray) -> float:
        """Calculate spectral complexity"""
        # Variance across time for each MFCC
        temporal_variance = np.var(mfccs, axis=1)
        
        # Average variance (higher = more complex)
        complexity = float(np.mean(temporal_variance))
        
        return complexity
    
    def _calculate_regularity(self, beats: np.ndarray) -> float:
        """How regular is the rhythm? (0-1, 1 = perfectly regular)"""
        if len(beats) < 2:
            return 0.0
        
        # Inter-beat intervals
        intervals = np.diff(beats)
        
        if len(intervals) == 0:
            return 0.0
        
        # Coefficient of variation (lower = more regular)
        cv = np.std(intervals) / (np.mean(intervals) + 1e-10)
        
        # Convert to regularity score (0-1)
        regularity = 1.0 / (1.0 + cv)
        
        return float(regularity)
    
    def _extract_rhythm_pattern(self, beats: np.ndarray, duration: float) -> List[float]:
        """Extract rhythm pattern signature"""
        if len(beats) < 2:
            return []
        
        # Normalize beat positions to 0-1
        normalized = beats / duration
        
        # Return first 16 beats (or all if fewer)
        return [float(x) for x in normalized[:16]]
    
    def _detect_key(self, chroma: np.ndarray) -> str:
        """Simple key detection based on chroma"""
        # Average chroma across time
        chroma_mean = np.mean(chroma, axis=1)
        
        # Find dominant pitch class
        dominant = np.argmax(chroma_mean)
        
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return keys[dominant]
    
    def _map_to_agi_rhythm(self, tempo: float, entropy: float, complexity: float) -> Dict:
        """Map music properties to AGI rhythm states"""
        
        # Heuristic mapping
        if tempo < 80 and entropy < 5.0:
            primary_state = "resting"
            confidence = 0.9
        elif 80 <= tempo < 100 and entropy < 6.0:
            primary_state = "integrating"
            confidence = 0.75
        elif 100 <= tempo < 140 and complexity > 0.5:
            primary_state = "superconducting"
            confidence = 0.8
        elif tempo >= 140 or complexity > 1.0:
            primary_state = "folding"
            confidence = 0.7
        else:
            primary_state = "unknown"
            confidence = 0.5
        
        return {
            "primary_state": primary_state,
            "confidence": confidence,
            "reasoning": f"tempo={tempo:.1f}, entropy={entropy:.2f}, complexity={complexity:.2f}"
        }


def analyze_music_library(music_dir: str, output_json: str):
    """Analyze entire music library"""
    print("\n🎛️ Reaper Music Pattern Analyzer")
    print("=" * 70)
    
    analyzer = MusicPatternAnalyzer()
    
    # Find all WAV files
    music_path = Path(music_dir)
    wav_files = list(music_path.glob("*.wav"))
    
    if not wav_files:
        print(f"❌ No WAV files found in {music_dir}")
        return
    
    print(f"\n📁 Found {len(wav_files)} music files")
    
    results = {
        "analyzed_at": datetime.now().isoformat(),
        "music_dir": music_dir,
        "total_files": len(wav_files),
        "analyses": []
    }
    
    for i, wav_file in enumerate(wav_files, 1):
        print(f"\n[{i}/{len(wav_files)}] Processing: {wav_file.name}")
        
        try:
            analysis = analyzer.analyze_file(str(wav_file))
            results["analyses"].append(analysis)
            
            # Print key info
            if "error" not in analysis:
                tempo = analysis["tempo_rhythm"]["tempo_bpm"]
                entropy = analysis["information_theory"]["entropy"]
                state = analysis["agi_mapping"]["primary_state"]
                
                print(f"   ✅ Tempo: {tempo:.1f} BPM")
                print(f"   ✅ Entropy: {entropy:.2f}")
                print(f"   ✅ AGI State: {state}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["analyses"].append({
                "path": str(wav_file),
                "error": str(e)
            })
    
    # Save results
    print(f"\n💾 Saving results to: {output_json}")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✨ Analysis complete!")
    print("=" * 70)
    
    # Summary
    successful = len([a for a in results["analyses"] if "error" not in a])
    print(f"\n📊 Summary:")
    print(f"   Total: {len(wav_files)} files")
    print(f"   Successful: {successful}")
    print(f"   Failed: {len(wav_files) - successful}")


if __name__ == "__main__":
    # Default paths for AGI system
    MUSIC_DIR = r"C:\workspace\agi\music"
    OUTPUT_JSON = r"C:\workspace\agi\outputs\music_pattern_analysis.json"
    
    if len(sys.argv) > 1:
        MUSIC_DIR = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_JSON = sys.argv[2]
    
    analyze_music_library(MUSIC_DIR, OUTPUT_JSON)
