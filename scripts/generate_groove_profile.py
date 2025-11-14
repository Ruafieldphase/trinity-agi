#!/usr/bin/env python3
"""
🎼 Groove Profile Generator

Flow Observer / Microphone / Rhythm 이벤트 텔레메트리로부터 현재 작업 리듬에 적합한
groove (microtiming, spectral tilt, swing) 파라미터를 추론하여
`outputs/groove_profile_latest.json` 에 저장한다.

과거에는 `fdo_agi_repo.utils.groove_engine.GrooveProfile` 에 의존했으나
현재 워크스페이스에는 모듈이 없으므로 이 스크립트가 경량 dataclass 대체 구현을 제공한다.
"""

from __future__ import annotations

import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Any

# -------------------- Setup --------------------
CURRENT_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = CURRENT_FILE.parent.parent  # scripts/ 상위 = workspace 루트
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

logger = logging.getLogger("groove_profile")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# -------------------- Data Model --------------------
@dataclass
class GrooveProfile:
    swing_ratio: float               # 0.0 = straight, 0.5 = heavy swing (8th feel)
    push_pull_ms: float              # 음표 전체 평균 타이밍 오프셋 (음수가 뒤로, 양수가 앞으로)
    microtiming_variance: float      # 박자 별 분산 (humanization 정도)
    bass_boost_db: float             # 저역대 EQ 부스트 (가상 값)
    treble_boost_db: float           # 고역대 EQ 부스트 (가상 값)
    warmth_factor: float             # 전체 사운드 따뜻함 (0-1 스케일)
    name: str                        # 생성된 프로파일 이름
    generated_at: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


# -------------------- Generator --------------------
class GrooveProfileGenerator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    # 텔레메트리 로드
    def load_recent_telemetry(self, hours: int) -> Dict[str, Any]:
        telemetry = {
            "flow_reports": [],
            "microphone_analyses": [],
            "rhythm_events": []
        }

        # Flow Observer 리포트
        flow_report_path = self.workspace_root / "outputs" / "flow_observer_report_latest.json"
        if flow_report_path.exists():
            try:
                with open(flow_report_path, 'r', encoding='utf-8') as f:
                    telemetry["flow_reports"].append(json.load(f))
                logger.info(f"✅ Loaded flow report: {flow_report_path}")
            except Exception as e:
                logger.warning(f"Failed to load flow report: {e}")

        # 마이크 분석
        mic_analysis_path = self.workspace_root / "outputs" / "microphone" / "microphone_analysis_latest.json"
        if mic_analysis_path.exists():
            try:
                with open(mic_analysis_path, 'r', encoding='utf-8') as f:
                    telemetry["microphone_analyses"].append(json.load(f))
                logger.info(f"✅ Loaded microphone analysis: {mic_analysis_path}")
            except Exception as e:
                logger.warning(f"Failed to load microphone analysis: {e}")

        # Event Bus 리듬 이벤트 (최근 window)
        event_bus_path = self.workspace_root / "outputs" / "event_bus.jsonl"
        if event_bus_path.exists():
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                with open(event_bus_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        event = json.loads(line.strip())
                        ts = event.get("timestamp")
                        try:
                            event_time = datetime.fromisoformat(ts) if ts else None
                        except Exception:
                            event_time = None
                        if event_time and event_time >= cutoff_time and event.get("topic") == "rhythm_pulse":
                            telemetry["rhythm_events"].append(event)
                logger.info(f"✅ Loaded {len(telemetry['rhythm_events'])} rhythm events")
            except Exception as e:
                logger.warning(f"Failed to load rhythm events: {e}")

        return telemetry

    # 템포 선호도 (현재는 BPM 평균을 산출만 하고 리턴 값은 swing/push에 간접 영향)
    def analyze_tempo_preference(self, telemetry: Dict[str, Any]) -> float:
        base_tempo = 120.0
        if telemetry["flow_reports"]:
            flow_score = telemetry["flow_reports"][0].get("flow_metrics", {}).get("flow_score", 0.5)
            base_tempo = 100 + (flow_score * 40)  # 100~140 BPM 범위
        if telemetry["microphone_analyses"]:
            dominant_freq = telemetry["microphone_analyses"][0].get("dominant_frequency", 0)
            if dominant_freq > 0:
                estimated_bpm = (dominant_freq / 2) * 60  # 매우 단순 모델
                if 60 <= estimated_bpm <= 180:
                    base_tempo = (base_tempo + estimated_bpm) / 2
        return round(base_tempo, 1)

    # 마이크로타이밍 스타일 분석 (Flow 기반)
    def analyze_microtiming_style(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        push_ms = -5.0
        swing = 0.10
        if telemetry["flow_reports"]:
            flow_score = telemetry["flow_reports"][0].get("flow_metrics", {}).get("flow_score", 0.5)
            if flow_score < 0.3:
                push_ms = -10.0
                swing = 0.15
            elif flow_score > 0.7:
                push_ms = -2.0
                swing = 0.05
        return {"push_ms": push_ms, "swing_factor": swing}

    # 스펙트럴 밸런스 (마이크 기반 아주 단순 모델)
    def analyze_spectral_balance(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        balance = {"low": 0.4, "mid": 0.4, "high": 0.2}
        if telemetry["microphone_analyses"]:
            analysis = telemetry["microphone_analyses"][0]
            dominant_freq = analysis.get("dominant_frequency", 0)
            if dominant_freq < 250:
                balance = {"low": 0.5, "mid": 0.3, "high": 0.2}
            elif dominant_freq > 2000:
                balance = {"low": 0.3, "mid": 0.3, "high": 0.4}
        return balance

    # 프로파일 생성
    def generate_profile(self, hours: int = 24) -> GrooveProfile:
        logger.info(f"🎼 Generating groove profile from last {hours}h telemetry ...")
        telemetry = self.load_recent_telemetry(hours)
        tempo = self.analyze_tempo_preference(telemetry)  # 현재는 로깅용
        microtiming = self.analyze_microtiming_style(telemetry)
        spectral = self.analyze_spectral_balance(telemetry)

        logger.info(f"📊 Tempo preference: {tempo} BPM")
        logger.info(f"📊 Microtiming: push={microtiming['push_ms']:.1f}ms swing={microtiming['swing_factor']:.2f}")
        logger.info(f"📊 Spectral balance: low={spectral['low']:.2f} mid={spectral['mid']:.2f} high={spectral['high']:.2f}")

        # spectral → EQ boost 변환 (baseline 0.33을 기준으로 -12~+12 dB 범위 스케일링)
        bass_boost = (spectral['low'] - 0.33) * 12.0
        treble_boost = (spectral['high'] - 0.33) * 12.0

        profile = GrooveProfile(
            swing_ratio=microtiming["swing_factor"],
            push_pull_ms=microtiming["push_ms"],
            microtiming_variance=0.30,
            bass_boost_db=bass_boost,
            treble_boost_db=treble_boost,
            warmth_factor=0.50,
            name=f"auto_generated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        return profile

    def save_profile(self, profile: GrooveProfile, output_path: Path) -> None:
        profile.save(output_path)
        logger.info(f"✅ Saved groove profile → {output_path}")


# -------------------- CLI --------------------
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="🎼 Groove Profile Generator")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window (hours)")
    parser.add_argument("--output", type=str, help="Output JSON path")
    args = parser.parse_args()

    workspace_root = WORKSPACE_ROOT
    generator = GrooveProfileGenerator(workspace_root)
    profile = generator.generate_profile(args.hours)

    output_path = Path(args.output) if args.output else workspace_root / "outputs" / "groove_profile_latest.json"
    generator.save_profile(profile, output_path)

    print(f"\n✅ Groove profile generated: {output_path}")
    print(f"📊 Swing Ratio   : {profile.swing_ratio:.2f}")
    print(f"📊 Push/Pull ms  : {profile.push_pull_ms:.1f}")
    print(f"📊 Bass Boost dB : {profile.bass_boost_db:.1f}")
    print(f"📊 Treble Boost dB: {profile.treble_boost_db:.1f}")
    print(f"📊 Warmth Factor : {profile.warmth_factor:.2f}")


if __name__ == "__main__":  # pragma: no cover
    main()
