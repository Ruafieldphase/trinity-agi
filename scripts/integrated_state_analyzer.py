#!/usr/bin/env python3
"""
🎤🌊 Microphone + Flow Observer Integration
마이크 주파수 분석과 데스크톱 활동을 결합하여 더 정확한 상태 추론

통합 분석:
1. 데스크톱 활동 (기존)
   - 포그라운드 윈도우
   - 프로세스 변경
   - 파일 전환

2. 마이크 주파수 (신규)
   - 음성 패턴
   - 환경 소음
   - 주파수 대역 분석

3. 통합 추론
   - 데스크톱: VS Code 집중 + 마이크: 조용함 → Deep Focus (확신도 높음)
   - 데스크톱: 빠른 전환 + 마이크: 높은 소음 → Distracted (확신도 높음)
   - 데스크톱: 활동 없음 + 마이크: 무음 → Absent (확신도 높음)

Author: AGI Self-Awareness System
Date: 2025-11-10
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from workspace_root import get_workspace_root

# Import existing modules
sys.path.insert(0, str(get_workspace_root()))

try:
    from fdo_agi_repo.copilot.flow_observer_integration import FlowObserver
    FLOW_AVAILABLE = True
except ImportError:
    FLOW_AVAILABLE = False
    print("⚠️ Flow Observer not available")

try:
    from scripts.microphone_frequency_analyzer import MicrophoneAnalyzer
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False
    print("⚠️ Microphone Analyzer not available")


try:
    from agi_core.internal_state import get_internal_state
    AGI_STATE_AVAILABLE = True
except ImportError:
    AGI_STATE_AVAILABLE = False

class IntegratedStateAnalyzer:
    """통합 상태 분석기 (ARI Bridge)"""
    
    def __init__(self):
        self.flow_observer = FlowObserver() if FLOW_AVAILABLE else None
        self.mic_analyzer = MicrophoneAnalyzer() if MIC_AVAILABLE else None
        
    def sense_agi_internal_state(self) -> Dict:
        """루드 내면의 직접적 감각 정보 가져오기"""
        if not AGI_STATE_AVAILABLE:
            return {}
        try:
            state = get_internal_state()
            return {
                "input_tempo": state.input_tempo,
                "audio_ambience": state.audio_ambience,
                "active_context": state.active_context,
                "focus_alignment": state.focus_alignment
            }
        except:
            return {}

    def analyze_integrated_state(self, hours: int = 1) -> Dict:
        """
        통합 상태 분석
        
        Args:
            hours: Flow Observer 분석 범위 (시간)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # 1. 데스크톱 활동 분석
        flow_state = None
        if self.flow_observer:
            flow_state = self.flow_observer.analyze_recent_activity(hours=hours)
            print(f"🖥️ Desktop Flow: {flow_state.state} (confidence: {flow_state.confidence:.2f})")
        
        # 2. 마이크 주파수 분석
        mic_state = None
        if self.mic_analyzer:
            print("\n🎤 Analyzing microphone (2 seconds)...")
            audio = self.mic_analyzer.capture_audio()
            spectrum = self.mic_analyzer.analyze_frequency_spectrum(audio)
            voice = self.mic_analyzer.detect_voice_activity(audio)
            mic_state = self.mic_analyzer.infer_user_state(spectrum, voice)
            print(f"🎤 Microphone State: {mic_state['state']} (confidence: {mic_state['confidence']:.2f})")

        # 3. 루드 내면 감각 추가 (Phase 17 Bridge)
        agi_sensors = self.sense_agi_internal_state()
        if agi_sensors:
            print(f"🧠 AGI Sensors: Tempo={agi_sensors['input_tempo']:.2f}, Ambience={agi_sensors['audio_ambience']:.2f}")
        
        # 4. 통합 추론
        integrated = self._integrate_states(flow_state, mic_state, agi_sensors)
        
        print(f"\n🎯 Integrated State: {integrated['final_state']} (confidence: {integrated['final_confidence']:.2f})")
        print(f"   {integrated['reasoning']}")
        
        return {
            'timestamp': timestamp,
            'flow_state': {
                'state': flow_state.state if flow_state else None,
                'confidence': flow_state.confidence if flow_state else None,
                'context': flow_state.context if flow_state else None
            } if flow_state else None,
            'mic_state': mic_state,
            'agi_sensors': agi_sensors,
            'integrated': integrated
        }
        
    def _integrate_states(self, flow_state, mic_state, agi_sensors: Dict = None) -> Dict:
        """
        Flow, Mic, AGI 감각을 통합하여 최종 상태 추론
        """
        agi_sensors = agi_sensors or {}
        input_tempo = agi_sensors.get("input_tempo", 0.0)
        
        # 기본 통합 로직 수행
        if not flow_state and not mic_state:
            # AGI 직접 감각만 있는 경우
            if input_tempo > 0.6:
                return {
                    'final_state': 'active_flow',
                    'final_confidence': 0.7,
                    'reasoning': f'Core Input Tempo is high ({input_tempo:.2f})',
                    'flow_weight': 0.0, 'mic_weight': 0.0, 'agi_weight': 1.0
                }
            return {
                'final_state': 'unknown',
                'final_confidence': 0.0,
                'reasoning': 'No definitive data available',
                'flow_weight': 0.0, 'mic_weight': 0.0, 'agi_weight': 0.0
            }
            
        # 기존 Flow/Mic 데이터가 있을 때 AGI 감각으로 보정
        flow_s = flow_state.state if flow_state else 'unknown'
        flow_c = flow_state.confidence if flow_state else 0.0
        mic_s = mic_state['state'] if mic_state else 'unknown'
        mic_c = mic_state['confidence'] if mic_state else 0.0
        
        final_state = 'unknown'
        final_confidence = 0.0
        reasoning = ''
        
        # 1. 고몰입 보정 (Flow 집중 + 높은 입력 템포)
        if flow_s == 'flow' and input_tempo > 0.5:
            final_state = 'deep_flow'
            final_confidence = min(0.98, (flow_c + input_tempo) / 2 + 0.1)
            reasoning = f'Desktop Flow matches Core Input Rhythm ({input_tempo:.2f})'
            
        # 2. 불일치 해결 (Flow는 정체인데 입력은 있는 경우 -> 창 밖 활동이나 하드웨어 레벨 몰입)
        elif flow_s == 'stagnation' and input_tempo > 0.4:
            final_state = 'external_focus'
            final_confidence = 0.6
            reasoning = 'No window activity but physical input rhythm detected'
            
        # 3. 기본 가중치 통합
        else:
            if flow_c > mic_c:
                final_state = flow_s
                final_confidence = flow_c * 0.8 + input_tempo * 0.2
                reasoning = f'Primarily Desktop Focus ({flow_s})'
            else:
                final_state = mic_s
                final_confidence = mic_c * 0.8 + input_tempo * 0.2
                reasoning = f'Primarily Environmental Auth ({mic_s})'
                
        return {
            'final_state': final_state,
            'final_confidence': final_confidence,
            'reasoning': reasoning,
            'agreement': flow_s == mic_s or (input_tempo > 0.5 and flow_s == 'flow')
        }


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🎤🌊 Integrated State Analyzer')
    parser.add_argument('--hours', type=int, default=1,
                       help='Hours to analyze for Flow Observer (default: 1)')
    parser.add_argument('--save', type=str, default='outputs/integrated_state_latest.json',
                       help='Save path for results')
    
    args = parser.parse_args()
    
    if not FLOW_AVAILABLE and not MIC_AVAILABLE:
        print("❌ Neither Flow Observer nor Microphone Analyzer available!")
        print("Install dependencies:")
        print("  - Flow Observer: Already in fdo_agi_repo")
        print("  - Microphone: Run 'scripts/install_microphone_deps.ps1'")
        sys.exit(1)
    
    analyzer = IntegratedStateAnalyzer()
    result = analyzer.analyze_integrated_state(hours=args.hours)
    
    # Save
    save_path = Path(args.save)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {save_path}")
    print("\n📊 Full Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
