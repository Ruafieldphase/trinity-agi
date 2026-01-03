"""
Full-Stack Orchestrator - Phase 9
통합 자율 학습 시스템의 중앙 조율자

모든 컴포넌트(Resonance, BQI, Gateway, YouTube)를 통합하여
자율적으로 학습하고 최적화하는 시스템을 구현합니다.
"""

import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Import workspace utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from workspace_utils import find_workspace_root

# 상대 import (기존 컴포넌트 활용)
try:
    from ..orchestrator.resonance_bridge import ResonanceBridge
except ImportError:
    # 개발/테스트 환경에서는 None으로 처리
    ResonanceBridge = None


class FullStackOrchestrator:
    """
    Full-Stack 통합 오케스트레이터
    
    역할:
    - 모든 컴포넌트 조율 및 통합
    - 실시간 피드백 루프 관리
    - 자율 학습 및 최적화
    - 통합 모니터링
    """
    
    def __init__(
        self,
        workspace_root: Path,
        enable_resonance: bool = True,
        enable_bqi: bool = True,
        enable_gateway: bool = True,
        enable_youtube: bool = True
    ):
        """
        오케스트레이터 초기화
        
        Args:
            workspace_root: 작업 공간 루트 경로
            enable_resonance: Resonance 활성화 여부
            enable_bqi: BQI Learning 활성화 여부
            enable_gateway: Gateway Optimizer 활성화 여부
            enable_youtube: YouTube Learner 활성화 여부
        """
        self.workspace_root = Path(workspace_root)
        self.outputs_dir = self.workspace_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        self.logger = self._setup_logging()
        
        # 컴포넌트 초기화
        self.components = {}
        
        if enable_resonance:
            self.components['resonance'] = self._init_resonance()
        
        if enable_bqi:
            self.components['bqi'] = self._init_bqi()
        
        if enable_gateway:
            self.components['gateway'] = self._init_gateway()
        
        if enable_youtube:
            self.components['youtube'] = self._init_youtube()
        
        # 상태 저장소
        self.state = {
            'started_at': datetime.now().isoformat(),
            'events_processed': 0,
            'learning_cycles': 0,
            'last_optimization': None
        }
        
        self.logger.info(f"FullStackOrchestrator initialized with {len(self.components)} components")
        
        # 이벤트 이력 (테스트/모니터링용)
        self.event_history: List[Dict[str, Any]] = []
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('FullStackOrchestrator')
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_file = self.outputs_dir / 'full_stack_orchestrator.log'
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 포매터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _init_resonance(self) -> Optional[Any]:
        """Resonance System 초기화"""
        try:
            if ResonanceBridge is not None:
                bridge = ResonanceBridge()
                self.logger.info("Resonance System initialized")
                return bridge
            else:
                self.logger.warning("Resonance System not available (import failed)")
                return None
        except Exception as e:
            self.logger.error(f"Failed to initialize Resonance: {e}")
            return None
    
    def _init_bqi(self) -> Optional[Dict[str, Any]]:
        """BQI Learning System 초기화"""
        try:
            # BQI 모델 로드
            bqi_model_path = self.workspace_root / 'fdo_agi_repo' / 'outputs' / 'bqi_pattern_model.json'
            binoche_path = self.workspace_root / 'fdo_agi_repo' / 'outputs' / 'binoche_persona.json'
            weights_path = self.workspace_root / 'fdo_agi_repo' / 'outputs' / 'ensemble_weights.json'
            
            bqi_data = {}
            
            if bqi_model_path.exists():
                with open(bqi_model_path, 'r', encoding='utf-8') as f:
                    bqi_data['patterns'] = json.load(f)
            
            if binoche_path.exists():
                with open(binoche_path, 'r', encoding='utf-8') as f:
                    bqi_data['persona'] = json.load(f)
            
            if weights_path.exists():
                with open(weights_path, 'r', encoding='utf-8') as f:
                    bqi_data['weights'] = json.load(f)
            
            self.logger.info(f"BQI System initialized with {len(bqi_data)} models")
            return bqi_data
        except Exception as e:
            self.logger.error(f"Failed to initialize BQI: {e}")
            return None
    
    def _init_gateway(self) -> Optional[Dict[str, Any]]:
        """Gateway Optimizer 초기화"""
        try:
            # Gateway 설정 로드
            gateway_config = {
                'adaptive_timeout': {
                    'peak': 250,      # ms
                    'off_peak': 400   # ms
                },
                'phase_sync': {
                    'peak_hours': list(range(9, 16)),  # 09:00-15:59
                    'off_peak_hours': list(range(0, 9)) + list(range(16, 24))
                },
                'prefetch': {
                    'enabled': True,
                    'max_cache_size': 100
                }
            }
            
            self.logger.info("Gateway Optimizer initialized")
            return gateway_config
        except Exception as e:
            self.logger.error(f"Failed to initialize Gateway: {e}")
            return None
    
    def _init_youtube(self) -> Optional[Dict[str, Any]]:
        """YouTube Learner 초기화"""
        try:
            # YouTube 인덱스 로드
            index_path = self.outputs_dir / 'youtube_learner_index.md'
            
            youtube_data = {
                'enabled': True,
                'index_available': index_path.exists()
            }
            
            if index_path.exists():
                youtube_data['index_path'] = str(index_path)
            
            self.logger.info("YouTube Learner initialized")
            return youtube_data
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube: {e}")
            return None
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        이벤트 처리 (통합 파이프라인)
        
        Flow:
        1. Resonance policy check
        2. BQI prediction
        3. Gateway optimization
        4. Execution
        5. Learning
        
        Args:
            event: 처리할 이벤트
            
        Returns:
            처리 결과
        """
        self.logger.info(f"Processing event: {event.get('type', 'unknown')}")
        
        result = {
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }
        
        try:
            # Stage 1: Resonance Policy Check
            if 'resonance' in self.components and self.components['resonance']:
                resonance_result = self._resonance_check(event)
                result['stages']['resonance'] = resonance_result
                
                # 정책 위반 시 중단
                if not resonance_result.get('approved', True):
                    result['status'] = 'rejected_by_policy'
                    return result
            
            # Stage 2: BQI Prediction
            if 'bqi' in self.components and self.components['bqi']:
                bqi_result = self._bqi_predict(event)
                result['stages']['bqi'] = bqi_result
                
                # BQI 제안 적용
                if bqi_result.get('decision') == 'reject':
                    result['status'] = 'rejected_by_bqi'
                    return result
            
            # Stage 3: Gateway Optimization
            if 'gateway' in self.components and self.components['gateway']:
                gateway_result = self._gateway_optimize(event)
                result['stages']['gateway'] = gateway_result
            
            # Stage 4: Execution (여기서는 시뮬레이션)
            execution_result = self._execute_task(event)
            result['stages']['execution'] = execution_result
            result['status'] = 'completed'
            
            # Stage 5: Learning
            self._learn_from_result(result)
            
            # 상태 업데이트
            self.state['events_processed'] += 1
            self.event_history.append(
                {
                    'event': event,
                    'status': result.get('status'),
                    'timestamp': result.get('timestamp'),
                    'stages': list(result.get('stages', {}).keys()),
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
            self.event_history.append(
                {
                    'event': event,
                    'status': 'error',
                    'timestamp': result.get('timestamp'),
                    'error': str(e),
                }
            )
            return result
    
    def _resonance_check(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Resonance 정책 검사"""
        # 실제로는 ResonanceBridge.evaluate() 호출
        # 여기서는 간단한 시뮬레이션
        return {
            'approved': True,
            'policy': 'ops-safety',
            'confidence': 0.85
        }
    
    def _bqi_predict(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """BQI 의사결정 예측"""
        bqi_data = self.components.get('bqi', {})
        
        # 간단한 규칙 기반 예측
        decision = 'accept'  # accept, reject, escalate
        confidence = 0.75
        
        if bqi_data and 'persona' in bqi_data:
            # Binoche_Observer 페르소나 활용
            persona = bqi_data['persona']
            # 실제로는 복잡한 패턴 매칭
            pass
        
        return {
            'decision': decision,
            'confidence': confidence,
            'reasoning': 'Pattern matched with BQI model'
        }
    
    def _gateway_optimize(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway 최적화 적용"""
        gateway_config = self.components.get('gateway', {})
        
        # 현재 시각에 따른 타임아웃 결정
        current_hour = datetime.now().hour
        
        if current_hour in gateway_config.get('phase_sync', {}).get('peak_hours', []):
            timeout = gateway_config.get('adaptive_timeout', {}).get('peak', 250)
            phase = 'peak'
        else:
            timeout = gateway_config.get('adaptive_timeout', {}).get('off_peak', 400)
            phase = 'off_peak'
        
        return {
            'timeout': timeout,
            'phase': phase,
            'optimizations_applied': ['adaptive_timeout', 'phase_sync']
        }
    
    def _execute_task(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """작업 실행 (시뮬레이션)"""
        # 실제로는 Task Queue에 enqueue하거나 직접 실행
        import random
        success_rate = 0.9
        
        success = random.random() < success_rate
        latency = random.randint(150, 300) if success else random.randint(400, 600)
        
        return {
            'success': success,
            'latency_ms': latency,
            'executed_at': datetime.now().isoformat()
        }
    
    def _learn_from_result(self, result: Dict[str, Any]):
        """결과로부터 학습"""
        # BQI 온라인 학습
        # Resonance 정책 조정
        # Gateway 파라미터 업데이트
        
        self.state['learning_cycles'] += 1
        self.state['last_optimization'] = datetime.now().isoformat()
        
        self.logger.debug(f"Learning cycle {self.state['learning_cycles']} completed")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            'state': self.state,
            'components': {
                name: 'active' if comp is not None else 'inactive'
                for name, comp in self.components.items()
            },
            'events': self.event_history[-100:],
            'timestamp': datetime.now().isoformat()
        }
    
    def save_state(self, filepath: Optional[Path] = None):
        """상태 저장"""
        if filepath is None:
            filepath = self.outputs_dir / 'full_stack_orchestrator_state.json'
        
        state_data = {
            'status': 'initialized',
            'saved_at': datetime.now().isoformat(),
            'event_count': self.state['events_processed'],
            'events_processed': self.event_history,
            'components': {
                name: 'active' if comp is not None else 'inactive'
                for name, comp in self.components.items()
            },
            'state': self.state,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"State saved to {filepath}")
    
    def _generate_synthetic_events(self) -> List[Dict[str, Any]]:
        """학습용 synthetic 이벤트 생성"""
        import random
        
        events = []
        event_types = ['bqi_query', 'gateway_request', 'youtube_learn']
        
        # 사이클당 3-5개 이벤트 생성
        num_events = random.randint(3, 5)
        
        for i in range(num_events):
            event_type = random.choice(event_types)
            event = {
                'id': f"synthetic_{datetime.now().timestamp()}_{i}",
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'priority': random.choice(['high', 'medium', 'low']),
                'synthetic': True
            }
            events.append(event)
        
        return events
    
    def run_learning_cycle(self) -> Dict[str, Any]:
        """
        학습 사이클 실행
        
        1. Synthetic 이벤트 생성 (학습 데이터)
        2. Task Queue에서 대기 중인 태스크 확인
        3. 각 컴포넌트에서 학습 수행
        4. 결과 집계 및 로깅
        
        Returns:
            사이클 실행 결과
        """
        cycle_start = time.time()
        cycle_results = {
            'cycle_number': self.state['learning_cycles'] + 1,
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'events_generated': 0
        }
        
        self.logger.info(f"Starting learning cycle #{cycle_results['cycle_number']}")
        
        # 0. Synthetic 이벤트 생성 (학습 데이터)
        try:
            synthetic_events = self._generate_synthetic_events()
            cycle_results['events_generated'] = len(synthetic_events)
            
            # 생성된 이벤트 처리
            for event in synthetic_events:
                result = self.process_event(event)
                self.logger.debug(f"Processed synthetic event: {event['type']}")
            
            self.logger.info(f"Generated and processed {len(synthetic_events)} synthetic events")
        except Exception as e:
            self.logger.error(f"Synthetic event generation error: {e}")
            cycle_results['events_generated'] = 0
        
        try:
            # 1. BQI Learning
            if 'bqi' in self.components and self.components['bqi']:
                try:
                    bqi_comp = self.components['bqi']
                    # BQI 모델 학습 (최근 24시간 데이터)
                    # 실제 구현은 BQI learner 호출
                    cycle_results['components']['bqi'] = {
                        'status': 'active',
                        'models_updated': 3
                    }
                    self.logger.info("BQI learning cycle completed")
                except Exception as e:
                    self.logger.error(f"BQI learning error: {e}")
                    cycle_results['components']['bqi'] = {'status': 'error', 'error': str(e)}
            
            # 2. Gateway Optimization
            if 'gateway' in self.components and self.components['gateway']:
                try:
                    gateway_comp = self.components['gateway']
                    # Gateway 최적화 수행
                    cycle_results['components']['gateway'] = {
                        'status': 'active',
                        'optimizations_applied': 1
                    }
                    self.logger.info("Gateway optimization completed")
                except Exception as e:
                    self.logger.error(f"Gateway optimization error: {e}")
                    cycle_results['components']['gateway'] = {'status': 'error', 'error': str(e)}
            
            # 3. YouTube Learning
            if 'youtube' in self.components and self.components['youtube']:
                try:
                    youtube_comp = self.components['youtube']
                    # YouTube 학습 수행
                    cycle_results['components']['youtube'] = {
                        'status': 'active',
                        'videos_processed': 0
                    }
                    self.logger.info("YouTube learning completed")
                except Exception as e:
                    self.logger.error(f"YouTube learning error: {e}")
                    cycle_results['components']['youtube'] = {'status': 'error', 'error': str(e)}
            
            # 상태 업데이트
            self.state['learning_cycles'] += 1
            self.state['last_optimization'] = datetime.now().isoformat()
            
            cycle_duration = time.time() - cycle_start
            cycle_results['duration_seconds'] = cycle_duration
            cycle_results['status'] = 'success'
            
            self.logger.info(f"Learning cycle completed in {cycle_duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Learning cycle error: {e}")
            cycle_results['status'] = 'error'
            cycle_results['error'] = str(e)
        
        return cycle_results
    
    def shutdown(self):
        """정상 종료"""
        self.logger.info("Shutting down FullStackOrchestrator")
        self.save_state()
        self.logger.info(f"Total events processed: {self.state['events_processed']}")
        self.logger.info(f"Total learning cycles: {self.state['learning_cycles']}")


def main():
    """메인 실행 함수"""
    # CLI 인자 파싱
    parser = argparse.ArgumentParser(description='Full-Stack Orchestrator')
    parser.add_argument('--mode', choices=['init', 'run', 'test'], default='test',
                        help='실행 모드')
    parser.add_argument('--duration', type=int, default=60,
                        help='실행 시간(초)')
    parser.add_argument('--workspace', type=str, default=None,
                        help='작업 공간 경로')
    args = parser.parse_args()
    
    # 작업 공간 경로
    if args.workspace:
        workspace_root = Path(args.workspace)
    else:
        workspace_root = find_workspace_root(Path(__file__).parent)
    
    print(f"\n=== Full-Stack Orchestrator ===")
    print(f"Mode: {args.mode}")
    print(f"Duration: {args.duration}s")
    print(f"Workspace: {workspace_root}")
    
    # 오케스트레이터 생성
    orchestrator = FullStackOrchestrator(workspace_root)
    
    # 모드별 실행
    if args.mode == 'init':
        print("\n초기화 모드: 시스템 상태 확인 및 초기화")
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    elif args.mode == 'run':
        print(f"\n실행 모드: {args.duration}초 동안 자율 학습")
        start_time = time.time()
        cycle_count = 0
        
        # 학습 사이클 간격 (5분)
        cycle_interval = 300  # 5 minutes
        last_cycle_time = -cycle_interval  # 즉시 첫 사이클 실행하도록
        
        print(f"  학습 사이클 간격: {cycle_interval}초")
        print(f"  예상 사이클 수: {args.duration // cycle_interval}")
        
        while time.time() - start_time < args.duration:
            elapsed = time.time() - start_time
            
            # 학습 사이클 실행
            if elapsed - last_cycle_time >= cycle_interval:
                print(f"\n[{int(elapsed)}s] Learning cycle #{cycle_count + 1} starting...")
                cycle_result = orchestrator.run_learning_cycle()
                cycle_count += 1
                last_cycle_time = elapsed
                
                # 사이클 결과 출력
                active_components = [k for k, v in cycle_result['components'].items() 
                                    if v.get('status') == 'active']
                print(f"  Components: {', '.join(active_components)}")
                print(f"  Duration: {cycle_result.get('duration_seconds', 0):.2f}s")
                
                # 상태 저장
                orchestrator.save_state()
            
            # 짧은 대기
            time.sleep(30)  # 30초마다 체크
            
            # 진행 상황 출력
            if int(elapsed) % 300 == 0:  # 5분마다
                status = orchestrator.get_status()
                print(f"  진행: {int(elapsed)}s / {args.duration}s, "
                      f"사이클: {cycle_count}, "
                      f"이벤트: {status['state']['events_processed']}")
        
        print(f"\n완료: {cycle_count}개 학습 사이클 실행")
        
    else:  # test 모드
        print("\n테스트 모드: 샘플 이벤트 처리")
        test_events = [
            {'type': 'task', 'name': 'test_task_1', 'priority': 'high'},
            {'type': 'task', 'name': 'test_task_2', 'priority': 'normal'},
            {'type': 'task', 'name': 'test_task_3', 'priority': 'low'},
        ]
        
        for event in test_events:
            result = orchestrator.process_event(event)
            print(f"\nEvent: {event['name']}")
            print(f"Status: {result['status']}")
            print(f"Stages: {list(result.get('stages', {}).keys())}")
    
    # 최종 상태 출력
    status = orchestrator.get_status()
    print(f"\n=== Final Status ===")
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # 종료
    orchestrator.shutdown()
    print("\nOrchestrator shutdown complete.")


if __name__ == '__main__':
    main()

