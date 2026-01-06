#!/usr/bin/env python3
"""
Flow 상태 → 뇌파 주파수 매핑 시스템
음악/사운드를 통한 정보 전달 실험
"""
import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime
from workspace_root import get_workspace_root

@dataclass
class BrainwaveFrequency:
    """뇌파 주파수 대역"""
    name: str
    hz_min: float
    hz_max: float
    description: str
    use_case: str

# 과학적 근거가 있는 뇌파 대역
BRAINWAVE_BANDS = {
    "delta": BrainwaveFrequency("Delta", 0.5, 4.0, "깊은 수면, 무의식", "Glymphatic drain, 수면"),
    "theta": BrainwaveFrequency("Theta", 4.0, 8.0, "명상, 창의성", "휴식, 아이디어 떠오름"),
    "alpha": BrainwaveFrequency("Alpha", 8.0, 13.0, "편안한 집중", "Flow 상태, 학습"),
    "beta": BrainwaveFrequency("Beta", 13.0, 30.0, "활성 사고", "문제 해결, 코딩"),
    "gamma": BrainwaveFrequency("Gamma", 30.0, 100.0, "고차원 인지", "통찰, 연결"),
}

# Solfeggio 주파수 (역사적/영적 의미, 과학적 근거는 제한적)
SOLFEGGIO_FREQUENCIES = {
    174: "Pain relief, 안정감",
    285: "Tissue healing",
    396: "Liberation from fear",
    417: "Change, transformation",
    528: "DNA repair, love",  # 가장 유명
    639: "Relationships",
    741: "Awakening intuition",
    852: "Spiritual order",
    963: "Divine connection",
}

class FlowToFrequencyMapper:
    """Flow 상태를 음악 파라미터로 매핑"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.flow_report = workspace_root / "outputs" / "flow_observer_report_latest.json"
    
    def load_current_flow(self) -> Optional[Dict]:
        """최근 Flow 상태 로드"""
        if not self.flow_report.exists():
            return None
        
        with open(self.flow_report, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("current_state", {})
    
    def flow_quality_to_brainwave(self, quality: float) -> Dict:
        """
        Flow quality → 최적 뇌파 주파수
        
        품질 범위:
        - 0.0-0.3: 산만 → Theta (휴식 필요)
        - 0.3-0.6: 중간 → Alpha (안정된 집중)
        - 0.6-0.8: 좋음 → Low Beta (활성 작업)
        - 0.8-1.0: 최고 → Alpha/Gamma 경계 (Flow)
        """
        if quality < 0.3:
            return {
                "band": "theta",
                "target_hz": 6.5,
                "carrier_freq": 396,  # Grounding
                "reason": "산만 상태, 휴식 및 재집중 필요"
            }
        elif quality < 0.6:
            return {
                "band": "alpha",
                "target_hz": 10.0,
                "carrier_freq": 528,  # 치유, 안정
                "reason": "안정된 집중 상태 유지"
            }
        elif quality < 0.8:
            return {
                "band": "beta",
                "target_hz": 18.0,
                "carrier_freq": 432,  # 자연 조화 주파수
                "reason": "활발한 작업 상태"
            }
        else:  # 0.8-1.0
            return {
                "band": "alpha_high",
                "target_hz": 12.5,
                "carrier_freq": 528,  # Flow 최적화
                "reason": "깊은 몰입 상태 (Flow)"
            }
    
    def generate_binaural_params(self, flow_quality: float) -> Dict:
        """
        Binaural beat 파라미터 생성
        좌/우 귀에 약간 다른 주파수 → 뇌가 차이 주파수 인식
        """
        mapping = self.flow_quality_to_brainwave(flow_quality)
        target_hz = mapping["target_hz"]
        carrier = mapping["carrier_freq"]
        
        return {
            "left_ear_hz": carrier,
            "right_ear_hz": carrier + target_hz,
            "perceived_beat_hz": target_hz,
            "brainwave_band": mapping["band"],
            "carrier_frequency": carrier,
            "description": mapping["reason"],
            "duration_minutes": 25,  # Pomodoro
        }
    
    def rhythm_to_audio_signature(self, hours: int = 24) -> Dict:
        """
        리듬 리포트 → 오디오 시그니처
        시간 축의 Flow quality를 주파수 패턴으로 변환
        """
        # 실제 구현 시: outputs/RHYTHM_*.md 파싱
        # 여기서는 데모 데이터
        
        # 예: 24시간 → 24개 데이터 포인트
        signature = {
            "duration_seconds": hours,  # 1시간 = 1초
            "sample_rate": 44100,
            "format": "wav",
            "encoding": "flow_quality_to_pitch",
            "data_points": hours,
            "frequency_range": {
                "min_hz": 200,   # Flow 0.0
                "max_hz": 800,   # Flow 1.0
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return signature
    
    def generate_report(self) -> str:
        """리포트 생성"""
        flow = self.load_current_flow()
        
        if not flow:
            return "⚠️ Flow 데이터 없음 (flow_observer_report_latest.json 없음)"
        
        quality = flow.get("quality", 0.5)
        duration = flow.get("duration_minutes", 0)
        
        mapping = self.flow_quality_to_brainwave(quality)
        binaural = self.generate_binaural_params(quality)
        
        report = f"""
# 🎵 Flow → Frequency Mapping Report

**생성 시각**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 현재 Flow 상태
- **품질**: {quality:.2f} / 1.00
- **지속 시간**: {duration}분
- **상태**: {self._quality_label(quality)}

## 🧠 추천 뇌파 주파수
- **대역**: {mapping['band'].upper()} ({BRAINWAVE_BANDS[mapping['band']].hz_min}-{BRAINWAVE_BANDS[mapping['band']].hz_max} Hz)
- **타겟**: {mapping['target_hz']} Hz
- **캐리어**: {mapping['carrier_freq']} Hz ({SOLFEGGIO_FREQUENCIES.get(mapping['carrier_freq'], 'N/A')})
- **이유**: {mapping['reason']}

## 🎧 Binaural Beat 파라미터
```json
{json.dumps(binaural, indent=2, ensure_ascii=False)}
```

## 💡 실용 적용

### A. 즉시 실행 (수동)
1. **YouTube 검색**: "{mapping['target_hz']}hz binaural beats"
2. **재생 시간**: 25분 (Pomodoro)
3. **볼륨**: 낮게 (배경음)

### B. 자동화 (다음 단계)
```powershell
# Task 추가 예정
Task: 🎵 Music: Auto Flow Frequency Sync
→ Flow quality 감지 → 자동 음악 재생
```

### C. Spotify 통합 (Phase 2)
- Flow < 0.3 → "Deep Focus" 플레이리스트
- Flow 0.3-0.6 → "Chill Study" 
- Flow > 0.8 → "Flow State" (high tempo)

## 🔬 과학적 근거
- **뇌파 entrainment**: 외부 자극에 뇌파가 동기화되는 현상 (검증됨)
- **Binaural beats**: 1839년 Heinrich Wilhelm Dove 발견
- **효과 연구**: Mixed results, but anecdotal evidence strong
- **안전성**: 일반적으로 안전 (간질 병력 있으면 주의)

## 📈 다음 단계
1. ✅ Flow → Frequency 매핑 (완료)
2. ⏳ 자동 음악 재생 (scripts/auto_music_player.py)
3. ⏳ 24시간 리듬 → 오디오 파일 변환
4. ⏳ Spotify API 통합
5. ⏳ "Sonic Memory" 실험 (경험 → 음악 인코딩)

---
**생성**: `flow_to_frequency_mapper.py`
**시간**: {datetime.now().strftime("%H:%M:%S")}
"""
        return report
    
    def _quality_label(self, quality: float) -> str:
        """품질 레이블"""
        if quality < 0.3:
            return "❌ 산만"
        elif quality < 0.6:
            return "⚠️ 중간"
        elif quality < 0.8:
            return "✅ 좋음"
        else:
            return "🔥 최고 (Flow)"

def main():
    """메인 실행"""
    import sys
    workspace = get_workspace_root()
    
    mapper = FlowToFrequencyMapper(workspace)
    report = mapper.generate_report()
    
    # 리포트 저장
    output_path = workspace / "outputs" / "flow_frequency_mapping_latest.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(report)
    print(f"\n✅ 리포트 저장: {output_path}")
    
    # JSON도 저장
    flow = mapper.load_current_flow()
    if flow:
        quality = flow.get("quality", 0.5)
        binaural = mapper.generate_binaural_params(quality)
        
        json_path = workspace / "outputs" / "flow_frequency_mapping_latest.json"
        json_path.write_text(json.dumps(binaural, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ JSON 저장: {json_path}")

if __name__ == "__main__":
    main()
