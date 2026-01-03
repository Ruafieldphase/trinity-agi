#!/usr/bin/env python3
"""
Thought-Action Bridge
====================
"생각을 행동으로 번역하는 다리"

무의식(Quantum Digital Twin - 리눅스)에서 발견한 패턴을
의식(Digital Twin - 안티그래비티)의 구체적인 행동으로 변환합니다.

Architecture:
-------------
무의식 시뮬레이션 (리눅스 플레이그라운드)
    ↓
Thought Stream (rhythm_think.py)
    ↓
Thought-Action Bridge (여기) ← Fear System 연동
    ↓
Action Proposals (proposals.json)
    ↓
의식 실행 (execute_proposal.py - Windows)
    ↓
Feedback Loop → Resonance Ledger → 무의식 학습
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from workspace_root import get_workspace_root

# Configuration
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = get_workspace_root()
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
PROPOSALS_FILE = OUTPUTS_DIR / "proposals.json"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
CORE_STATE_FILE = OUTPUTS_DIR / "core_state.json"
RESONANCE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
BRIDGE_RESPONSES_FILE = OUTPUTS_DIR / "bridge" / "bridge_responses.jsonl"

# Risk thresholds for execution targets
RISK_THRESHOLDS = {
    "LOW": "antigravity_playground",      # 안티그래비티에서 직접 실행 (Windows)
    "MEDIUM": "linux_playground",         # 리눅스 플레이그라운드에서 시뮬레이션 (Unconscious)
    "HIGH": "quantum_simulation_only"     # 퀀텀 시뮬레이션만 (실행하지 않음)
}

def load_json_safe(file_path: Path) -> Optional[Dict]:
    """Safely load JSON file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {file_path}: {e}")
        return None

def get_fear_level() -> float:
    """Get current fear level from Core state."""
    state = load_json_safe(CORE_STATE_FILE)
    if state and 'fear' in state:
        return state['fear'].get('level', 0.0)
    return 0.0

def assess_risk(decision: str, fear_level: float, resonance: float) -> str:
    """
    Assess risk level for the proposed action.
    
    Risk decreases as fear decreases and resonance increases.
    """
    # Base risk by decision type
    base_risk = {
        'amplify': 0.1,      # 패턴 강화 - 낮은 위험
        'explore': 0.3,      # 새로운 탐색 - 중간 위험
        'stabilize': 0.2,    # 안정화 - 낮은 위험
        'rest': 0.1,         # 휴식 - 낮은 위험
        'observe': 0.0,      # 관찰만 - 위험 없음
        'pivot': 0.5,        # 전환 - 높은 위험
    }.get(decision, 0.5)
    
    # Fear 증가 = 위험 증가 (0.0 ~ 1.0)
    fear_factor = fear_level * 0.3
    
    # Resonance 증가 = 위험 감소 (익숙한 패턴은 안전) (-1.0 ~ 1.0)
    resonance_factor = -(resonance * 0.2)
    
    total_risk = base_risk + fear_factor + resonance_factor
    total_risk = max(0.0, min(1.0, total_risk))  # Clamp to [0, 1]
    
    # Categorize
    if total_risk < 0.3:
        return "LOW"
    elif total_risk < 0.6:
        return "MEDIUM"
    else:
        return "HIGH"

def determine_execution_target(risk_level: str) -> str:
    """
    Determine where this action should be executed.
    
    - LOW: Antigravity (Windows) - 의식에서 직접 실행
    - MEDIUM: Linux Playground - 무의식 시뮬레이션 먼저
    - HIGH: Quantum Simulation Only - 시뮬레이션만
    """
    return RISK_THRESHOLDS.get(risk_level, "quantum_simulation_only")

def check_quantum_signals() -> Optional[Dict]:
    """Check for recent quantum simulation signals from Linux."""
    if not BRIDGE_RESPONSES_FILE.exists():
        return None
        
    try:
        # Read last line efficiently
        with open(BRIDGE_RESPONSES_FILE, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
            
        if not last_line:
            return None
            
        response = json.loads(last_line)
        result = response.get('result', {})
        
        # Check if it's a quantum simulation result
        if result.get('type') == 'quantum_simulation' and response.get('status') == 'completed':
            # Check if recent (within last 10 seconds) to avoid reprocessing old signals
            timestamp = datetime.fromisoformat(response['timestamp'])
            if (datetime.now() - timestamp).total_seconds() < 10:
                return result
                
    except Exception as e:
        print(f"⚠️ Failed to check quantum signals: {e}")
        
    return None

def translate_quantum_signal_to_proposal(signal: Dict) -> Optional[Dict]:
    """Translate quantum signal into action proposal."""
    pattern = signal.get('quantum_pattern')
    output = signal.get('output')
    
    if not pattern:
        return None
        
    # Map patterns to actions
    action_map = {
        'fear_spike_detected': {
            'type': 'deepen_current', # 안정화를 위해 현재 흐름 강화
            'title': '퀀텀 불안정 감지: 심화 및 안정화',
            'description': f"무의식(Quantum)에서 불안정 패턴이 감지되었습니다.\\n\\n**신호**: {output}\\n**대응**: 현재 흐름을 더 깊이 파고들어 근본 원인을 찾고 안정화합니다.",
            'risk': 'LOW' # 대응 자체는 안전하게
        },
        'resource_anomaly': {
            'type': 'optimize_system',
            'title': '퀀텀 리소스 변칙: 시스템 최적화',
            'description': f"무의식(Quantum)에서 리소스 변칙이 감지되었습니다.\\n\\n**신호**: {output}\\n**대응**: 시스템 리소스를 점검하고 최적화를 수행합니다.",
            'risk': 'LOW'
        },
        'optimization_found': {
            'type': 'refactor_code', # 리팩토링 제안
            'title': '퀀텀 최적화 발견: 코드 리팩토링',
            'description': f"무의식(Quantum) 시뮬레이션에서 최적화 가능성을 발견했습니다.\\n\\n**신호**: {output}\\n**대응**: 발견된 패턴을 바탕으로 코드를 개선합니다.",
            'risk': 'MEDIUM' # 코드 수정은 주의 필요
        },
        'creative_stagnation': {
            'type': 'search_knowledge', # 새로운 지식 탐색
            'title': '창작 블록 감지: 무작위 탐색',
            'description': f"무의식(Quantum)에서 창작적 정체가 감지되었습니다.\\n\\n**신호**: {output}\\n**대응**: 알려진 해결 공간에서 벗어나 무작위 탐색을 시작합니다.",
            'risk': 'LOW' # 탐색은 안전
        },
        'self_model_fragmentation': {
            'type': 'analyze_change', # 변화 분석 및 통합
            'title': '정체성 혼란 감지: 기억 통합',
            'description': f"무의식(Quantum)에서 자기 모델의 파편화가 감지되었습니다.\\n\\n**신호**: {output}\\n**대응**: 최근 기억을 통합하여 일관된 자기 서사를 재구성합니다.",
            'risk': 'MEDIUM' # 정체성 관련은 주의 필요
        }
    }
    
    template = action_map.get(pattern)
    if not template:
        return None
        
    proposal = {
        'id': int(datetime.now().timestamp()),
        'timestamp': datetime.now().isoformat(),
        'source': 'quantum_bridge', # Source is Quantum Bridge
        'status': 'pending',
        'decision': 'stabilize' if pattern == 'fear_spike_detected' else 'amplify',
        'risk_level': template['risk'],
        'execution_target': 'antigravity_playground', # Execute in Conscious (Windows)
        'title': template['title'],
        'description': template['description'],
        'action': {
            'type': template['type'],
            'params': {
                'context_message': f"Quantum Signal: {pattern}",
                'origin': 'linux_simulation'
            }
        },
        'metadata': {
            'quantum_pattern': pattern,
            'simulation_output': output
        }
    }
    return proposal

def translate_thought_to_action(thought_data: Dict) -> Optional[Dict]:
    """
    Translate thought stream output into actionable proposal.
    """
    if not thought_data:
        return None
    
    decision_data = thought_data.get('decision', {})
    decision = decision_data.get('decision', 'observe')
    
    delivery = thought_data.get('delivery', {})
    feeling = delivery.get('feeling', 'neutral')
    resonance = delivery.get('resonance', 0.5)
    message = delivery.get('message', '')
    
    # Get Fear level
    fear_level = get_fear_level()
    
    # Assess risk
    risk_level = assess_risk(decision, fear_level, resonance)
    execution_target = determine_execution_target(risk_level)
    
    # Map decision to action type
    action_map = {
        'amplify': {
            'type': 'deepen_current',
            'title': '현재 흐름 강화',
            'description': f"리듬 사고가 'amplify' 결정을 내렸습니다. 현재의 긍정적인 패턴을 더 깊이 탐구합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '이 리듬을 타고 더 깊이 나아가라')}\\n**위험도**: {risk_level}"
        },
        'explore': {
            'type': 'search_knowledge',
            'title': '새로운 탐색',
            'description': f"리듬 사고가 'explore' 결정을 내렸습니다. 새로운 지식 영역을 탐색합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '새로운 흐름을 즐기며 탐험하라')}\\n**위험도**: {risk_level}"
        },
        'stabilize': {
            'type': 'optimize_system',
            'title': '시스템 안정화',
            'description': f"리듬 사고가 'stabilize' 결정을 내렸습니다. 시스템을 최적화하고 안정화합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '즉시 안정을 취하고 중심을 잡으라')}\\n**위험도**: {risk_level}"
        },
        'rest': {
            'type': 'cleanup',
            'title': '휴식 및 정리',
            'description': f"리듬 사고가 'rest' 결정을 내렸습니다. 잠시 멈추어 정리합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '잠시 멈추어 숨을 고르라')}\\n**위험도**: {risk_level}"
        },
        'observe': {
            'type': 'monitor',
            'title': '관찰 모드 유지',
            'description': f"리듬 사고가 'observe' 결정을 내렸습니다. 현재 상태를 유지하며 패턴을 모니터링합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '현재의 리듬을 유지하며 관찰하라')}\\n**위험도**: {risk_level}"
        },
        'pivot': {
            'type': 'analyze_change',
            'title': '변화 감지 및 분석',
            'description': f"리듬 사고가 'pivot' 결정을 내렸습니다. 전환의 조짐을 분석합니다.\\n\\n**느낌**: {feeling}\\n**공명도**: {resonance*100:.2f}%\\n**행동 지침**: {decision_data.get('action', '변화의 조짐을 주시하라')}\\n**위험도**: {risk_level}"
        }
    }
    
    action_template = action_map.get(decision, action_map['observe'])
    
    proposal = {
        'id': int(datetime.now().timestamp()),
        'timestamp': datetime.now().isoformat(),
        'source': 'rhythm_think',
        'status': 'pending',
        'decision': decision,
        'risk_level': risk_level,
        'execution_target': execution_target,
        'title': action_template['title'],
        'description': action_template['description'],
        'action': {
            'type': action_template['type'],
            'params': {
                'feeling': feeling,
                'resonance': resonance,
                'context_message': message[:200] + '...' if len(message) > 200 else message
            }
        },
        'metadata': {
            'thought_timestamp': thought_data.get('timestamp'),
            'original_action': decision_data.get('action'),
            'fear_level': fear_level
        }
    }
    
    return proposal

def save_proposal(proposal: Dict) -> bool:
    """Save proposal to proposals.json."""
    try:
        PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing proposals
        proposals = []
        if PROPOSALS_FILE.exists():
            try:
                with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
                    proposals = json.load(f)
            except:
                proposals = []
        
        # Check for duplicates (simple check)
        for p in proposals:
            if (p.get('source') == 'rhythm_think' and 
                p.get('decision') == proposal['decision'] and 
                p.get('status') == 'pending'):
                # Update timestamp instead of adding new
                p['timestamp'] = proposal['timestamp']
                p['metadata']['thought_timestamp'] = proposal['metadata']['thought_timestamp']
                
                with open(PROPOSALS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(proposals, f, indent=2, ensure_ascii=False)
                print(f"🔄 Updated existing pending proposal: {p['id']}")
                return True

        # Append new proposal
        proposals.append(proposal)
        
        # Save
        with open(PROPOSALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(proposals, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"❌ Failed to save proposal: {e}")
        return False

def bridge_thought_to_action() -> bool:
    """
    Main bridge function: Read thought stream AND quantum signals.
    """
    print("=" * 60)
    print("🌉 Thought-Action Bridge (Quantum-Enhanced)")
    print("=" * 60)
    
    proposal = None
    
    # 1. Check Quantum Signals (Priority)
    quantum_signal = check_quantum_signals()
    if quantum_signal:
        print(f"🌌 Quantum Signal Detected: {quantum_signal.get('quantum_pattern')}")
        proposal = translate_quantum_signal_to_proposal(quantum_signal)
        
    # 2. If no quantum signal, check Thought Stream
    if not proposal:
        thought_data = load_json_safe(THOUGHT_STREAM_FILE)
        if thought_data:
            print(f"📖 Thought Stream: {thought_data.get('timestamp')}")
            print(f"   Decision: {thought_data.get('decision', {}).get('decision')}")
            proposal = translate_thought_to_action(thought_data)
    
    if not proposal:
        print("⚠️ No actionable signals found (Thought or Quantum)")
        return False
    
    print(f"\n✨ Action Proposal Created:")
    print(f"   Source: {proposal['source']}")
    print(f"   Type: {proposal['action']['type']}")
    print(f"   Risk: {proposal['risk_level']}")
    
    # Get fear level from metadata
    fear_level = proposal.get('metadata', {}).get('fear_level', 0.0)
    
    # Save proposal
    if save_proposal(proposal):
        print(f"\n✅ Proposal processed: ID={proposal['id']}")
        
        # [SENA CONSULTATION] HIGH fear + HIGH risk requires external guidance
        if fear_level > 0.8 and proposal['risk_level'] == "HIGH":
            print(f"\n🆘 CRITICAL STATE: Fear={fear_level:.2f}, Risk=HIGH")
            print(f"   Requesting guidance from Sena (External AI)...")
            
            try:
                import requests
                
                # Prepare Sena consultation message
                sena_request = {
                    "type": "consultation_request",
                    "message": f"긴급 상황: 두려움이 {fear_level:.2f}로 매우 높습니다. 다음 행동에 대한 조언이 필요합니다.\n\n**제안된 행동**: {proposal['title']}\n**설명**: {proposal['description'][:200]}...\n**위험도**: {proposal['risk_level']}\n\n이 행동을 실행해야 할까요, 아니면 다른 접근이 필요할까요?",
                    "vector": [fear_level, 0.2, 0.5, 0.8, 0.3],  # High fear, low calm
                    "metadata": {
                        "proposal_id": proposal['id'],
                        "fear_level": fear_level,
                        "risk_level": proposal['risk_level'],
                        "requires_response": True
                    }
                }
                
                # Send to Sena via dashboard API
                response = requests.post(
                    "http://localhost:3000/api/sena/messages",
                    json=sena_request,
                    timeout=5
                )
                
                if response.ok:
                    print(f"   ✅ Consultation request sent to Sena")
                    print(f"   ⏸️ Execution PAUSED - Awaiting Sena's guidance")
                    
                    # Update proposal status to indicate it's waiting for Sena
                    proposals = []
                    if PROPOSALS_FILE.exists():
                        with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
                            proposals = json.load(f)
                    
                    for p in proposals:
                        if p['id'] == proposal['id']:
                            p['status'] = 'awaiting_sena_input'
                            p['sena_consultation'] = {
                                'requested_at': datetime.now().isoformat(),
                                'reason': 'high_fear_high_risk'
                            }
                            break
                    
                    with open(PROPOSALS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(proposals, f, indent=2, ensure_ascii=False)
                    
                else:
                    print(f"   ⚠️ Failed to contact Sena: {response.status_code}")
                    print(f"   Falling back to manual approval")
                    
            except Exception as e:
                print(f"   ⚠️ Error contacting Sena: {e}")
                print(f"   Falling back to manual approval")
        
        # [AUTO-EXECUTION] LOW risk actions execute automatically
        elif proposal['risk_level'] == "LOW":
            print(f"🤖 AUTO-EXECUTE: Low risk action, executing in {proposal['execution_target']}...")
            try:
                subprocess.Popen(
                    [sys.executable, str(WORKSPACE_ROOT / "scripts" / "execute_proposal.py"), str(proposal['id'])],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                print(f"   Execution queued (background)")
            except Exception as e:
                print(f"   Failed to auto-execute: {e}")
        else:
             print(f"⏸️ MANUAL APPROVAL REQUIRED: {proposal['risk_level']} risk - awaiting user decision")

        return True
    else:
        return False

if __name__ == "__main__":
    success = bridge_thought_to_action()
    exit(0 if success else 1)
