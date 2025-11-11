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

# Import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

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


class IntegratedStateAnalyzer:
    """통합 상태 분석기"""
    
    def __init__(self):
        self.flow_observer = FlowObserver() if FLOW_AVAILABLE else None
        self.mic_analyzer = MicrophoneAnalyzer() if MIC_AVAILABLE else None
        
    def analyze_integrated_state(self, hours: int = 1) -> Dict:
        """
        통합 상태 분석
        
        Args:
            hours: Flow Observer 분석 범위 (시간)
            
        Returns:
            통합 분석 결과
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
        
        # 3. 통합 추론
        integrated = self._integrate_states(flow_state, mic_state)
        
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
            'integrated': integrated
        }
        
    def _integrate_states(self, flow_state, mic_state) -> Dict:
        """
        두 상태를 통합하여 최종 상태 추론
        
        Args:
            flow_state: Flow Observer 결과
            mic_state: Microphone Analyzer 결과
            
        Returns:
            통합 상태
        """
        # 둘 다 없으면 unknown
        if not flow_state and not mic_state:
            return {
                'final_state': 'unknown',
                'final_confidence': 0.0,
                'reasoning': 'No data available',
                'flow_weight': 0.0,
                'mic_weight': 0.0
            }
            
        # Flow만 있으면 Flow 사용
        if flow_state and not mic_state:
            return {
                'final_state': flow_state.state,
                'final_confidence': flow_state.confidence,
                'reasoning': 'Based on desktop activity only',
                'flow_weight': 1.0,
                'mic_weight': 0.0
            }
            
        # Mic만 있으면 Mic 사용
        if mic_state and not flow_state:
            return {
                'final_state': mic_state['state'],
                'final_confidence': mic_state['confidence'],
                'reasoning': 'Based on microphone analysis only',
                'flow_weight': 0.0,
                'mic_weight': 1.0
            }
            
        # 둘 다 있으면 통합 추론
        flow_s = flow_state.state
        flow_c = flow_state.confidence
        mic_s = mic_state['state']
        mic_c = mic_state['confidence']
        
        # 통합 로직
        final_state = 'unknown'
        final_confidence = 0.0
        reasoning = ''
        flow_weight = 0.5
        mic_weight = 0.5
        
        # Case 1: Flow 집중 + 조용함 → Deep Focus (강화)
        if flow_s == 'flow' and mic_s in ['deep_focus', 'active_work']:
            final_state = 'deep_flow'
            final_confidence = min(0.95, (flow_c + mic_c) / 2 + 0.2)  # 보너스
            reasoning = 'Desktop focus + Quiet environment = Deep Flow (강화됨)'
            flow_weight = 0.6
            mic_weight = 0.4
            
        # Case 2: Flow 집중 but 소음 → Shallow Flow (약화)
        elif flow_s == 'flow' and mic_s == 'noisy_environment':
            final_state = 'shallow_flow'
            final_confidence = min(flow_c, mic_c)  # 낮은 쪽 선택
            reasoning = 'Desktop focus but noisy = Shallow Flow (약화됨)'
            flow_weight = 0.7
            mic_weight = 0.3
            
        # Case 3: Flow 전환 + 대화 → Normal (일치)
        elif flow_s == 'transition' and mic_s == 'speaking':
            final_state = 'conversing'
            final_confidence = (flow_c + mic_c) / 2
            reasoning = 'Desktop switching + Speaking = Conversation'
            flow_weight = 0.5
            mic_weight = 0.5
            
        # Case 4: Flow 정체 + 무음 → Absent (일치)
        elif flow_s == 'stagnation' and mic_s in ['absent', 'deep_focus']:
            if mic_s == 'absent':
                final_state = 'away'
                final_confidence = (flow_c + mic_c) / 2 + 0.1
                reasoning = 'No desktop activity + Silence = Away (확실)'
            else:
                final_state = 'resting'
                final_confidence = (flow_c + mic_c) / 2
                reasoning = 'No desktop activity + Quiet = Resting/Thinking'
            flow_weight = 0.5
            mic_weight = 0.5
            
        # Case 5: 불일치 → 가중 평균
        else:
            # 더 확신도 높은 쪽에 가중치
            if flow_c > mic_c:
                final_state = flow_s
                final_confidence = flow_c * 0.7 + mic_c * 0.3
                reasoning = f'Desktop ({flow_s}) more confident than Mic ({mic_s})'
                flow_weight = 0.7
                mic_weight = 0.3
            else:
                final_state = mic_s
                final_confidence = mic_c * 0.7 + flow_c * 0.3
                reasoning = f'Mic ({mic_s}) more confident than Desktop ({flow_s})'
                flow_weight = 0.3
                mic_weight = 0.7
                
        return {
            'final_state': final_state,
            'final_confidence': final_confidence,
            'reasoning': reasoning,
            'flow_weight': flow_weight,
            'mic_weight': mic_weight,
            'agreement': flow_s == mic_s  # 두 시스템이 일치하는지
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
