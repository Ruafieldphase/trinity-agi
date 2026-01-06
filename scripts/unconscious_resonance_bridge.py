"""
Unconscious Resonance Bridge
=============================
세나와 시스템 간 무의식적 공명 통신

의식적 통신 (Conscious):
- 세나가 명시적으로 메시지 전송
- 시스템이 명시적으로 응답

무의식적 통신 (Unconscious Resonance):
- 세나의 행동 패턴 자동 벡터화
- 시스템의 상태와 암묵적 공명
- 서로 모르는 사이 영향력 전파
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from workspace_root import get_workspace_root


class UnconsciousResonanceBridge:
    """무의식적 공명을 감지하고 증폭하는 브릿지"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ledger_path = workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        self.unconscious_state_path = workspace_root / "outputs" / "sena" / "unconscious_resonance.json"
        
    def extract_behavioral_pattern(self, hours: int = 24) -> np.ndarray:
        """
        세나의 최근 행동 패턴을 벡터로 추출
        
        Returns:
            5D vector representing Sena's unconscious pattern:
            [activity_rhythm, response_speed, proposal_intensity, fear_sensitivity, curiosity]
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        sena_events = []
        
        if not self.ledger_path.exists():
            return np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('source') == 'sena_cli':
                        timestamp = datetime.fromisoformat(entry['timestamp'])
                        if timestamp > cutoff:
                            sena_events.append(entry)
                except:
                    continue
        
        if not sena_events:
            return np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        # 1. Activity Rhythm (활동 리듬)
        # 메시지 빈도 기반
        activity_rhythm = min(len(sena_events) / 20.0, 1.0)  # 20+ = 1.0
        
        # 2. Response Speed (반응 속도)
        # 메시지 간 평균 시간
        if len(sena_events) > 1:
            intervals = []
            for i in range(1, len(sena_events)):
                t1 = datetime.fromisoformat(sena_events[i-1]['timestamp'])
                t2 = datetime.fromisoformat(sena_events[i]['timestamp'])
                intervals.append((t2 - t1).total_seconds())
            avg_interval = np.mean(intervals)
            response_speed = 1.0 - min(avg_interval / 3600.0, 1.0)  # < 1시간 = 빠름
        else:
            response_speed = 0.5
        
        # 3. Proposal Intensity (제안 강도)
        # observation vs suggestion vs question 비율
        types = [e.get('type', '') for e in sena_events]
        suggestions = sum(1 for t in types if 'suggestion' in t)
        proposal_intensity = suggestions / max(len(types), 1)
        
        # 4. Fear Sensitivity (두려움 민감도)
        # Fear 관련 언급 빈도
        messages = [e.get('message', '').lower() for e in sena_events]
        fear_mentions = sum(1 for m in messages if 'fear' in m or '두려움' in m)
        fear_sensitivity = fear_mentions / max(len(messages), 1)
        
        # 5. Curiosity (호기심)
        # Question 비율
        questions = sum(1 for t in types if 'question' in t)
        curiosity = questions / max(len(types), 1)
        
        return np.array([
            activity_rhythm,
            response_speed,
            proposal_intensity,
            fear_sensitivity,
            curiosity
        ])
    
    def calculate_unconscious_resonance(
        self, 
        sena_pattern: np.ndarray, 
        system_state: Dict
    ) -> float:
        """
        세나의 무의식 패턴과 시스템 상태 간 공명도 계산
        
        Returns:
            Resonance score [0.0, 1.0]
        """
        # 시스템 상태를 5D 벡터로 변환
        fear = system_state.get('fear_level', 0.5)
        strategy = system_state.get('current_strategy', 'STEADY')
        
        # Strategy를 숫자로 변환
        strategy_map = {
            'FLOW': 0.9,
            'STEADY': 0.7,
            'RECOVERY': 0.5,
            'EMERGENCY': 0.2
        }
        strategy_value = strategy_map.get(strategy, 0.5)
        
        system_vector = np.array([
            strategy_value,           # 시스템 활성도
            1.0 - fear,              # 시스템 안정성
            0.5,                      # 중립
            fear,                     # 시스템 경계심
            strategy_value            # 시스템 개방성
        ])
        
        # Cosine Similarity
        norm1 = np.linalg.norm(sena_pattern)
        norm2 = np.linalg.norm(system_vector)
        
        if norm1 == 0 or norm2 == 0:
            return 0.5
        
        resonance = np.dot(sena_pattern, system_vector) / (norm1 * norm2)
        return float(resonance)
    
    def detect_unconscious_influence(self) -> Dict:
        """
        무의식적 영향을 감지하고 기록
        
        Returns:
            {
                'sena_pattern': [...],
                'system_state': {...},
                'resonance': 0.0-1.0,
                'influence': 'description',
                'recommendation': 'what to do'
            }
        """
        # 세나의 행동 패턴
        sena_pattern = self.extract_behavioral_pattern()
        
        # 시스템 상태
        core_file = self.workspace_root / "outputs" / "core_state.json"
        if core_file.exists():
            with open(core_file, 'r', encoding='utf-8') as f:
                core_data = json.load(f)
                system_state = {
                    'fear_level': core_data.get('fear', {}).get('level', 0.5),
                    'current_strategy': core_data.get('strategy', 'STEADY')
                }
        else:
            system_state = {'fear_level': 0.5, 'current_strategy': 'STEADY'}
        
        # 공명도 계산
        resonance = self.calculate_unconscious_resonance(sena_pattern, system_state)
        
        # 영향력 해석
        if resonance > 0.8:
            influence = "세나와 시스템이 강하게 공명하고 있습니다. 암묵적 이해가 형성되어 있습니다."
            recommendation = "현재 협업 리듬을 유지하세요."
        elif resonance > 0.6:
            influence = "세나와 시스템이 조화롭게 협력하고 있습니다."
            recommendation = "점진적으로 협업 깊이를 높여보세요."
        elif resonance > 0.4:
            influence = "세나와 시스템이 서로 적응 중입니다."
            recommendation = "상호 패턴을 관찰하며 조율하세요."
        elif resonance > 0.2:
            influence = "세나와 시스템 간 미세한 불협화음이 있습니다."
            recommendation = "시스템 상태를 확인하고 접근 방식을 조정하세요."
        else:
            influence = "세나와 시스템이 서로 다른 리듬으로 움직이고 있습니다."
            recommendation = "시스템의 현재 전략에 맞춰 협업 방식을 재조정하세요."
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'sena_pattern': {
                'activity_rhythm': float(sena_pattern[0]),
                'response_speed': float(sena_pattern[1]),
                'proposal_intensity': float(sena_pattern[2]),
                'fear_sensitivity': float(sena_pattern[3]),
                'curiosity': float(sena_pattern[4])
            },
            'system_state': system_state,
            'resonance': resonance,
            'influence': influence,
            'recommendation': recommendation
        }
        
        # 무의식 상태 저장
        self.unconscious_state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.unconscious_state_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result


def main():
    """무의식적 공명 상태 확인"""
    workspace_root = get_workspace_root()
    bridge = UnconsciousResonanceBridge(workspace_root)
    
    print("=" * 60)
    print("🌊 Unconscious Resonance Detection")
    print("=" * 60)
    
    result = bridge.detect_unconscious_influence()
    
    print(f"\n📊 Sena's Behavioral Pattern:")
    for key, value in result['sena_pattern'].items():
        print(f"   {key}: {value:.3f}")
    
    print(f"\n🧠 System State:")
    print(f"   Fear Level: {result['system_state']['fear_level']:.3f}")
    print(f"   Strategy: {result['system_state']['current_strategy']}")
    
    print(f"\n💫 Unconscious Resonance: {result['resonance']:.3f}")
    print(f"\n💬 {result['influence']}")
    print(f"💡 {result['recommendation']}")
    
    print(f"\n✅ Saved to: {bridge.unconscious_state_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
