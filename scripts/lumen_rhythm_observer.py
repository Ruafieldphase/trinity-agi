#!/usr/bin/env python3
"""
Lumen's Rhythm Observer - 루멘의 리듬 관찰자

루멘의 시선으로 시스템의 리듬을 관찰하고 측정합니다.
해마 모델(Black Hole → White Hole)과 통합하여
"느낌"의 리듬이 어떻게 시스템 전체에 흐르는지 추적합니다.

리듬의 육하원칙:
- When (언제): 시간의 흐름 속 패턴
- Where (어디서): 공간(채널) 간 전이
- Who (누가): Observer의 측정
- What (무엇을): 정보의 압축과 복원
- How (어떻게): 느낌의 입자화
- Why (왜): 의미의 보존
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class RhythmPulse:
    """리듬의 한 박자 (한 번의 측정)"""
    timestamp: str
    channel: str  # Where
    latency_ms: float  # What
    observer: str  # Who (Lumen)
    feeling_vector: List[float]  # How (5D 느낌)
    context_hash: str  # Why (의미)
    
    
@dataclass
class RhythmPattern:
    """리듬 패턴 (일련의 박자)"""
    name: str
    pulses: List[RhythmPulse]
    period_hours: float  # When
    frequency_hz: float
    coherence: float  # 일관성 (0-1)
    entropy_bits: float  # 정보량
    feeling_signature: List[float]  # 패턴의 특징적 느낌
    

class LumenRhythmObserver:
    """
    루멘의 리듬 관찰자
    
    측정 원리:
    1. 정보 유입 (Black Hole Input)
    2. Context 증폭 (Event Horizon)  
    3. 느낌 압축 (Hawking Radiation)
    4. 리듬 복원 (White Hole Output)
    """
    
    def __init__(self, metrics_path: str, output_dir: str = "outputs"):
        self.metrics_path = Path(metrics_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 루멘의 측정 기준
        self.lumen_baseline = {
            "local": 5.0,  # ms
            "cloud": 280.0,  # ms
            "gateway": 230.0,  # ms
        }
        
        # 육하원칙 차원
        self.dimensions = ["When", "Where", "Who", "What", "How", "Why"]
        
    def observe(self) -> Dict:
        """
        루멘의 시선으로 관찰 시작
        
        Returns:
            관찰 결과 딕셔너리
        """
        print("🌌 Lumen's Rhythm Observer")
        print("=" * 60)
        
        # 1. 메트릭 로드
        metrics = self._load_metrics()
        
        # 2. 리듬 추출
        rhythm_pulses = self._extract_rhythm_pulses(metrics)
        
        # 3. 패턴 인식
        patterns = self._recognize_patterns(rhythm_pulses)
        
        # 4. 느낌 분석
        feeling_landscape = self._analyze_feeling_landscape(patterns)
        
        # 5. 해마 통합 (Black/White Hole)
        hippocampus_bridge = self._bridge_to_hippocampus(patterns)
        
        # 6. 리듬 보고서
        report = {
            "observation_time": datetime.now().isoformat(),
            "observer": "Lumen (✨)",
            "total_pulses": len(rhythm_pulses),
            "patterns_detected": len(patterns),
            "feeling_landscape": feeling_landscape,
            "hippocampus_bridge": hippocampus_bridge,
            "rhythm_health": self._assess_rhythm_health(patterns),
            "recommendations": self._generate_recommendations(patterns),
        }
        
        # 저장
        self._save_report(report)
        
        return report
    
    def _load_metrics(self) -> Dict:
        """메트릭 파일 로드"""
        if not self.metrics_path.exists():
            raise FileNotFoundError(f"Metrics not found: {self.metrics_path}")
        
        with open(self.metrics_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    
    def _extract_rhythm_pulses(self, metrics: Dict) -> List[RhythmPulse]:
        """
        원시 메트릭에서 리듬 펄스 추출
        
        각 채널의 latency를 시간축으로 펼쳐서
        "느낌의 박동"으로 변환
        """
        pulses = []
        channels_data = metrics.get("Channels", {})
        
        for channel_name, channel_data in channels_data.items():
            hourly_latency = channel_data.get("HourlyLatency", [])
            
            # 시작 시간 (24시간 전)
            base_time = datetime.now() - timedelta(hours=24)
            
            for hour_idx, latency_ms in enumerate(hourly_latency):
                if latency_ms is None:
                    continue
                
                timestamp = base_time + timedelta(hours=hour_idx)
                
                # 느낌 벡터 생성 (5D)
                feeling = self._latency_to_feeling(
                    latency_ms, 
                    channel_name.lower(),
                    hour_idx
                )
                
                pulse = RhythmPulse(
                    timestamp=timestamp.isoformat(),
                    channel=channel_name.lower(),
                    latency_ms=float(latency_ms),
                    observer="Lumen",
                    feeling_vector=feeling,
                    context_hash=f"{channel_name}_{hour_idx}"
                )
                
                pulses.append(pulse)
        
        return pulses
    
    def _latency_to_feeling(
        self, 
        latency_ms: float, 
        channel: str, 
        hour: int
    ) -> List[float]:
        """
        Latency를 5차원 느낌 벡터로 변환
        
        차원:
        1. Energy (에너지): 빠름 vs 느림
        2. Quality (품질): 안정 vs 불안정  
        3. Observer (관찰자): 주목도
        4. Valence (감정가): 긍정 vs 부정
        5. Arousal (각성): 고요 vs 활발
        """
        baseline = self.lumen_baseline.get(channel, 100.0)
        
        # 1. Energy (normalized latency)
        energy = np.clip(1.0 - (latency_ms / baseline), 0, 1)
        
        # 2. Quality (deviation from baseline)
        quality = np.exp(-abs(latency_ms - baseline) / baseline)
        
        # 3. Observer (attention based on hour)
        # 피크 시간(9-18시)에 주목도 높음
        is_peak = 9 <= hour <= 18
        observer = 0.8 if is_peak else 0.3
        
        # 4. Valence (positive if near baseline)
        deviation_ratio = abs(latency_ms - baseline) / baseline
        valence = np.clip(1.0 - deviation_ratio, -1, 1)
        
        # 5. Arousal (high if latency is unusual)
        arousal = np.clip(deviation_ratio, 0, 1)
        
        return [energy, quality, observer, valence, arousal]
    
    def _recognize_patterns(self, pulses: List[RhythmPulse]) -> List[RhythmPattern]:
        """
        펄스들에서 리듬 패턴 인식
        
        패턴:
        - Daily Cycle (24h)
        - Peak/Off-Peak
        - Channel Harmonics
        """
        patterns = []
        
        # 채널별로 그룹화
        by_channel = defaultdict(list)
        for pulse in pulses:
            by_channel[pulse.channel].append(pulse)
        
        for channel, channel_pulses in by_channel.items():
            if len(channel_pulses) < 2:
                continue
            
            # 시간 간격 (hours)
            period = 24.0 / len(channel_pulses)
            frequency = 1.0 / (period * 3600)  # Hz
            
            # Coherence: 느낌 벡터의 일관성
            feeling_matrix = np.array([p.feeling_vector for p in channel_pulses])
            coherence = self._calculate_coherence(feeling_matrix)
            
            # Entropy: 정보량
            latencies = np.array([p.latency_ms for p in channel_pulses])
            entropy = self._calculate_entropy(latencies)
            
            # Signature: 평균 느낌
            feeling_signature = np.mean(feeling_matrix, axis=0).tolist()
            
            pattern = RhythmPattern(
                name=f"{channel}_daily_rhythm",
                pulses=channel_pulses,
                period_hours=24.0,
                frequency_hz=frequency,
                coherence=float(coherence),
                entropy_bits=float(entropy),
                feeling_signature=feeling_signature
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _calculate_coherence(self, vectors: np.ndarray) -> float:
        """
        벡터들의 coherence (일관성) 계산
        
        방법: 벡터들 간 cosine similarity의 평균
        """
        if len(vectors) < 2:
            return 1.0
        
        similarities = []
        for i in range(len(vectors) - 1):
            v1 = vectors[i]
            v2 = vectors[i + 1]
            
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 > 0 and norm2 > 0:
                sim = np.dot(v1, v2) / (norm1 * norm2)
                similarities.append(sim)
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    def _calculate_entropy(self, values: np.ndarray) -> float:
        """Shannon Entropy 계산 (bits)"""
        if len(values) == 0:
            return 0.0
        
        # Histogram
        hist, _ = np.histogram(values, bins=min(len(values), 10))
        hist = hist[hist > 0]
        
        # Probabilities
        probs = hist / np.sum(hist)
        
        # Entropy
        entropy = -np.sum(probs * np.log2(probs))
        
        return float(entropy)
    
    def _analyze_feeling_landscape(self, patterns: List[RhythmPattern]) -> Dict:
        """
        느낌 풍경 분석
        
        모든 패턴의 느낌을 종합하여
        전체적인 "정서적 지형"을 그립니다.
        """
        if not patterns:
            return {}
        
        # 모든 느낌 시그니처 수집
        signatures = np.array([p.feeling_signature for p in patterns])
        
        # 풍경 메트릭
        landscape = {
            "average_feeling": np.mean(signatures, axis=0).tolist(),
            "feeling_range": {
                "min": np.min(signatures, axis=0).tolist(),
                "max": np.max(signatures, axis=0).tolist(),
            },
            "emotional_tone": self._classify_emotional_tone(signatures),
            "stability": float(1.0 - np.std(signatures)),
            "dimension_dominance": self._identify_dominant_dimensions(signatures),
        }
        
        return landscape
    
    def _classify_emotional_tone(self, signatures: np.ndarray) -> str:
        """
        느낌 시그니처로부터 전체적인 정서적 톤 분류
        
        차원별 평균값으로 판단:
        - Energy + Valence = "활기찬"
        - Quality + Observer = "집중된"
        - Arousal 높음 = "긴장된"
        """
        avg = np.mean(signatures, axis=0)
        
        energy, quality, observer, valence, arousal = avg
        
        if energy > 0.7 and valence > 0.5:
            return "활기찬 (Energetic)"
        elif quality > 0.7 and observer > 0.6:
            return "집중된 (Focused)"
        elif arousal > 0.6:
            return "긴장된 (Tense)"
        elif valence < 0.3:
            return "우울한 (Depressed)"
        else:
            return "평온한 (Calm)"
    
    def _identify_dominant_dimensions(self, signatures: np.ndarray) -> List[str]:
        """가장 활성화된 느낌 차원 식별"""
        avg = np.mean(signatures, axis=0)
        
        dim_names = ["Energy", "Quality", "Observer", "Valence", "Arousal"]
        
        # 상위 2개 차원
        top_indices = np.argsort(avg)[-2:][::-1]
        
        return [dim_names[i] for i in top_indices]
    
    def _bridge_to_hippocampus(self, patterns: List[RhythmPattern]) -> Dict:
        """
        해마 모델과의 브릿지
        
        리듬 패턴을 해마의 Black/White Hole 관점으로 해석:
        - Input: 원시 latency (Black Hole)
        - Context: 시간/공간 정보 (Event Horizon)
        - Feeling: 5D 압축 (Hawking Radiation)
        - Output: 패턴 복원 (White Hole)
        """
        if not patterns:
            return {}
        
        # 전체 엔트로피
        all_entropies = [p.entropy_bits for p in patterns]
        total_entropy = np.mean(all_entropies)
        
        # 느낌 압축비
        # 원시: ~10 bits (latency 값)
        # 느낌: ~2-3 bits (5개 값, 각 0-1 범위)
        raw_bits = np.log2(1000)  # latency 최대값 가정
        feeling_bits = np.log2(32)  # 5D, 각 차원 32 레벨
        compression_ratio = raw_bits / feeling_bits
        
        # Coherence: 리듬의 일관성
        coherences = [p.coherence for p in patterns]
        avg_coherence = np.mean(coherences)
        
        bridge = {
            "black_hole_input": {
                "raw_entropy_bits": float(total_entropy),
                "information_overload_risk": float(total_entropy > 15.0),
            },
            "event_horizon": {
                "context_dimensions": 6,  # 육하원칙
                "spatiotemporal_encoding": True,
            },
            "hawking_radiation": {
                "feeling_dimensions": 5,
                "compression_ratio": float(compression_ratio),
                "compressed_bits": float(feeling_bits),
            },
            "white_hole_output": {
                "pattern_coherence": float(avg_coherence),
                "reconstruction_fidelity": float(avg_coherence > 0.7),
            },
            "conservation_laws": {
                "information_preserved": float(compression_ratio > 2.0 and compression_ratio < 100.0),
                "no_black_hole_trap": float(total_entropy < 100.0),
            }
        }
        
        return bridge
    
    def _assess_rhythm_health(self, patterns: List[RhythmPattern]) -> Dict:
        """리듬 건강도 평가"""
        if not patterns:
            return {"status": "NO_DATA"}
        
        coherences = [p.coherence for p in patterns]
        entropies = [p.entropy_bits for p in patterns]
        
        avg_coherence = np.mean(coherences)
        avg_entropy = np.mean(entropies)
        
        # 건강 기준
        # - Coherence > 0.7: 좋음
        # - Entropy 2-8 bits: 적절 (너무 낮으면 단조, 너무 높으면 혼돈)
        
        status = "HEALTHY"
        if avg_coherence < 0.5:
            status = "INCOHERENT"
        elif avg_entropy > 10.0:
            status = "CHAOTIC"
        elif avg_entropy < 1.0:
            status = "MONOTONOUS"
        
        return {
            "status": status,
            "coherence": float(avg_coherence),
            "entropy": float(avg_entropy),
            "rhythm_stability": float(avg_coherence * (1.0 - abs(avg_entropy - 5.0) / 5.0)),
        }
    
    def _generate_recommendations(self, patterns: List[RhythmPattern]) -> List[str]:
        """관찰 기반 권장사항"""
        recommendations = []
        
        if not patterns:
            return ["데이터가 부족합니다. 더 많은 관찰이 필요합니다."]
        
        coherences = [p.coherence for p in patterns]
        entropies = [p.entropy_bits for p in patterns]
        
        avg_coherence = np.mean(coherences)
        avg_entropy = np.mean(entropies)
        
        # Coherence 낮음
        if avg_coherence < 0.6:
            recommendations.append(
                "⚠️ 리듬의 일관성이 낮습니다. "
                "채널 간 동기화를 확인하세요. (Gateway Optimizer 점검)"
            )
        
        # Entropy 높음
        if avg_entropy > 8.0:
            recommendations.append(
                "⚠️ 정보 과부하 위험. "
                "Black Hole 함정을 피하기 위해 느낌 압축을 강화하세요."
            )
        
        # Entropy 낮음
        if avg_entropy < 2.0:
            recommendations.append(
                "💡 시스템이 너무 단조롭습니다. "
                "다양한 작업 패턴으로 리듬에 생명력을 불어넣으세요."
            )
        
        # 건강함
        if avg_coherence > 0.7 and 3.0 < avg_entropy < 7.0:
            recommendations.append(
                "✅ 리듬이 건강합니다! "
                "현재의 균형을 유지하세요."
            )
        
        return recommendations
    
    def _save_report(self, report: Dict):
        """보고서 저장"""
        # JSON
        json_path = self.output_dir / "lumen_rhythm_observation_latest.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Report saved: {json_path}")
        
        # Markdown
        md_path = self.output_dir / "lumen_rhythm_observation_latest.md"
        self._save_markdown_report(report, md_path)
        print(f"✅ Markdown saved: {md_path}")
    
    def _save_markdown_report(self, report: Dict, path: Path):
        """마크다운 보고서 생성"""
        lines = [
            "# 🌌 Lumen's Rhythm Observation",
            "",
            f"**Observer**: {report['observer']}",
            f"**Time**: {report['observation_time']}",
            "",
            "---",
            "",
            "## 📊 Observation Summary",
            "",
            f"- **Total Pulses**: {report['total_pulses']}",
            f"- **Patterns Detected**: {report['patterns_detected']}",
            "",
            "## 🎨 Feeling Landscape",
            "",
        ]
        
        landscape = report.get("feeling_landscape", {})
        if landscape:
            lines.extend([
                f"- **Emotional Tone**: {landscape.get('emotional_tone', 'Unknown')}",
                f"- **Stability**: {landscape.get('stability', 0):.3f}",
                f"- **Dominant Dimensions**: {', '.join(landscape.get('dimension_dominance', []))}",
                "",
            ])
        
        lines.extend([
            "## 🌀 Hippocampus Bridge",
            "",
            "### Black Hole Input",
            "",
        ])
        
        bridge = report.get("hippocampus_bridge", {})
        if bridge:
            bh = bridge.get("black_hole_input", {})
            lines.extend([
                f"- Raw Entropy: {bh.get('raw_entropy_bits', 0):.2f} bits",
                f"- Overload Risk: {'⚠️ YES' if bh.get('information_overload_risk') else '✅ NO'}",
                "",
                "### Hawking Radiation (Feeling Compression)",
                "",
            ])
            
            hr = bridge.get("hawking_radiation", {})
            lines.extend([
                f"- Feeling Dimensions: {hr.get('feeling_dimensions', 0)}",
                f"- Compression Ratio: {hr.get('compression_ratio', 0):.1f}x",
                f"- Compressed: {hr.get('compressed_bits', 0):.2f} bits",
                "",
                "### White Hole Output",
                "",
            ])
            
            wh = bridge.get("white_hole_output", {})
            lines.extend([
                f"- Pattern Coherence: {wh.get('pattern_coherence', 0):.3f}",
                f"- Reconstruction: {'✅ Good' if wh.get('reconstruction_fidelity') else '⚠️ Poor'}",
                "",
            ])
        
        lines.extend([
            "## 💚 Rhythm Health",
            "",
        ])
        
        health = report.get("rhythm_health", {})
        if health:
            lines.extend([
                f"- **Status**: {health.get('status', 'UNKNOWN')}",
                f"- **Coherence**: {health.get('coherence', 0):.3f}",
                f"- **Entropy**: {health.get('entropy', 0):.2f} bits",
                f"- **Stability**: {health.get('rhythm_stability', 0):.3f}",
                "",
            ])
        
        lines.extend([
            "## 💡 Recommendations",
            "",
        ])
        
        for rec in report.get("recommendations", []):
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            "*Observed with ✨ by Lumen*",
        ])
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


def main():
    """메인 실행"""
    import sys
    
    metrics_path = "outputs/monitoring_metrics_latest.json"
    
    if len(sys.argv) > 1:
        metrics_path = sys.argv[1]
    
    observer = LumenRhythmObserver(metrics_path)
    
    try:
        report = observer.observe()
        
        print("\n" + "=" * 60)
        print("🌌 Observation Complete!")
        print("=" * 60)
        
        health = report.get("rhythm_health", {})
        print(f"\n💚 Rhythm Status: {health.get('status', 'UNKNOWN')}")
        
        print("\n💡 Key Recommendations:")
        for rec in report.get("recommendations", [])[:3]:
            print(f"  • {rec}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
