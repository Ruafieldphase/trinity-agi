"""
Realtime Feedback Loop - Phase 9
실시간 학습 및 최적화 시스템

Gateway 성능 메트릭 → BQI 학습 → Resonance 정책 조정
완전 자동화된 피드백 루프
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


class RealtimeFeedbackLoop:
    """
    실시간 피드백 루프
    
    주기적으로:
    1. Gateway 성능 메트릭 수집
    2. BQI 모델로 분석 및 학습
    3. Resonance 정책 조정
    4. Gateway 파라미터 업데이트
    """
    
    def __init__(
        self,
        workspace_root: Path,
        collection_interval: int = 300,  # 5분
        learning_threshold: int = 10,    # 10개 샘플마다 학습
        optimization_threshold: float = 0.1  # 10% 성능 변화 시 최적화
    ):
        """
        피드백 루프 초기화
        
        Args:
            workspace_root: 작업 공간 루트
            collection_interval: 메트릭 수집 주기 (초)
            learning_threshold: 학습 트리거 임계값
            optimization_threshold: 최적화 트리거 임계값
        """
        self.workspace_root = Path(workspace_root)
        self.outputs_dir = self.workspace_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        self.collection_interval = collection_interval
        self.learning_threshold = learning_threshold
        self.optimization_threshold = optimization_threshold
        
        # 로깅
        self.logger = self._setup_logging()
        
        # 메트릭 버퍼
        self.metrics_buffer: List[Dict[str, Any]] = []
        
        # 학습 상태
        self.learning_state = {
            'samples_collected': 0,
            'learning_cycles': 0,
            'last_learning': None,
            'last_optimization': None
        }
        
        # 성능 베이스라인
        self.baseline = {
            'latency_mean': 0,
            'latency_std': 0,
            'success_rate': 0
        }
        
        self.logger.info("RealtimeFeedbackLoop initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('RealtimeFeedbackLoop')
        logger.setLevel(logging.INFO)
        
        log_file = self.outputs_dir / 'realtime_feedback_loop.log'
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Gateway 성능 메트릭 수집
        
        Returns:
            수집된 메트릭 또는 None
        """
        try:
            # Gateway 최적화 로그 읽기
            log_path = self.outputs_dir / 'gateway_optimization_log.jsonl'
            
            if not log_path.exists():
                self.logger.warning(f"Gateway log not found: {log_path}")
                return None
            
            # 마지막 라인 읽기
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return None
                
                last_line = lines[-1].strip()
                if not last_line:
                    return None
                
                metrics = json.loads(last_line)
                
                # 타임스탬프 추가
                metrics['collected_at'] = datetime.now().isoformat()
                
                return metrics
        
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def add_to_buffer(self, metrics: Dict[str, Any]):
        """메트릭을 버퍼에 추가"""
        self.metrics_buffer.append(metrics)
        self.learning_state['samples_collected'] += 1
        
        self.logger.debug(f"Added metrics to buffer (size: {len(self.metrics_buffer)})")
    
    def should_learn(self) -> bool:
        """학습이 필요한지 확인"""
        return len(self.metrics_buffer) >= self.learning_threshold
    
    def learn_from_metrics(self) -> Dict[str, Any]:
        """
        메트릭으로부터 학습
        
        Returns:
            학습 결과
        """
        if not self.metrics_buffer:
            return {'status': 'no_data'}
        
        self.logger.info(f"Learning from {len(self.metrics_buffer)} samples")
        
        # 메트릭 분석
        analysis = self._analyze_metrics(self.metrics_buffer)
        
        # BQI 모델 업데이트
        bqi_update = self._update_bqi_model(analysis)
        
        # Resonance 정책 조정
        policy_adjustment = self._adjust_resonance_policy(analysis)
        
        # 학습 결과
        learning_result = {
            'timestamp': datetime.now().isoformat(),
            'samples_used': len(self.metrics_buffer),
            'analysis': analysis,
            'bqi_update': bqi_update,
            'policy_adjustment': policy_adjustment
        }
        
        # 버퍼 클리어
        self.metrics_buffer.clear()
        
        # 상태 업데이트
        self.learning_state['learning_cycles'] += 1
        self.learning_state['last_learning'] = datetime.now().isoformat()
        
        # 학습 결과 저장
        self._save_learning_result(learning_result)
        
        self.logger.info(f"Learning cycle {self.learning_state['learning_cycles']} completed")
        
        return learning_result
    
    def _analyze_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """메트릭 분석"""
        if not metrics_list:
            return {}
        
        # 레이턴시 추출
        latencies = []
        successes = 0
        total = len(metrics_list)
        
        for m in metrics_list:
            if 'latency_ms' in m:
                latencies.append(m['latency_ms'])
            if m.get('success', False):
                successes += 1
        
        if not latencies:
            return {}
        
        # 통계 계산
        import statistics
        
        mean_latency = statistics.mean(latencies)
        std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
        success_rate = successes / total if total > 0 else 0
        
        # 베이스라인 대비 변화
        if self.baseline['latency_mean'] > 0:
            latency_change = (mean_latency - self.baseline['latency_mean']) / self.baseline['latency_mean']
        else:
            latency_change = 0
            # 첫 베이스라인 설정
            self.baseline['latency_mean'] = mean_latency
            self.baseline['latency_std'] = std_latency
            self.baseline['success_rate'] = success_rate
        
        return {
            'mean_latency': mean_latency,
            'std_latency': std_latency,
            'success_rate': success_rate,
            'latency_change': latency_change,
            'samples': len(latencies)
        }
    
    def _update_bqi_model(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """BQI 모델 업데이트"""
        # 성능이 좋으면 가중치 증가, 나쁘면 감소
        latency_change = analysis.get('latency_change', 0)
        
        adjustment = 'none'
        if latency_change < -0.1:  # 10% 개선
            adjustment = 'increase_weight'
        elif latency_change > 0.1:  # 10% 저하
            adjustment = 'decrease_weight'
        
        return {
            'adjustment': adjustment,
            'reason': f"Latency change: {latency_change:.2%}"
        }
    
    def _adjust_resonance_policy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Resonance 정책 조정"""
        # 성공률이 낮으면 ops-safety로 전환
        # 레이턴시가 높으면 latency-first로 전환
        
        success_rate = analysis.get('success_rate', 1.0)
        mean_latency = analysis.get('mean_latency', 0)
        
        recommended_policy = 'quality-first'  # 기본값
        
        if success_rate < 0.8:
            recommended_policy = 'ops-safety'
        elif mean_latency > 400:
            recommended_policy = 'latency-first'
        
        return {
            'recommended_policy': recommended_policy,
            'current_metrics': {
                'success_rate': success_rate,
                'mean_latency': mean_latency
            }
        }
    
    def should_optimize(self, analysis: Dict[str, Any]) -> bool:
        """최적화가 필요한지 확인"""
        latency_change = abs(analysis.get('latency_change', 0))
        return latency_change > self.optimization_threshold
    
    def optimize_gateway(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway 파라미터 최적화"""
        mean_latency = analysis.get('mean_latency', 0)
        std_latency = analysis.get('std_latency', 0)
        
        # 현재 시각 기준으로 최적 타임아웃 계산
        current_hour = datetime.now().hour
        is_peak = 9 <= current_hour < 16
        
        # 동적 타임아웃 조정
        if is_peak:
            base_timeout = 250
        else:
            base_timeout = 400
        
        # 표준편차가 크면 타임아웃 증가
        adjusted_timeout = base_timeout + (std_latency * 0.5)
        
        optimization = {
            'timestamp': datetime.now().isoformat(),
            'new_timeout': int(adjusted_timeout),
            'reason': f"Mean={mean_latency:.0f}ms, Std={std_latency:.0f}ms",
            'phase': 'peak' if is_peak else 'off_peak'
        }
        
        self.learning_state['last_optimization'] = datetime.now().isoformat()
        
        self.logger.info(f"Gateway optimized: timeout={int(adjusted_timeout)}ms")
        
        return optimization
    
    def _save_learning_result(self, result: Dict[str, Any]):
        """학습 결과 저장"""
        log_path = self.outputs_dir / 'feedback_loop_learning.jsonl'
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    def run_cycle(self) -> Dict[str, Any]:
        """피드백 루프 1사이클 실행"""
        cycle_result = {
            'timestamp': datetime.now().isoformat(),
            'actions': []
        }
        
        # 1. 메트릭 수집
        metrics = self.collect_metrics()
        if metrics:
            self.add_to_buffer(metrics)
            cycle_result['actions'].append('metrics_collected')
        
        # 2. 학습 필요 여부 확인
        if self.should_learn():
            learning_result = self.learn_from_metrics()
            cycle_result['actions'].append('learning_completed')
            cycle_result['learning'] = learning_result
            
            # 3. 최적화 필요 여부 확인
            analysis = learning_result.get('analysis', {})
            if self.should_optimize(analysis):
                optimization = self.optimize_gateway(analysis)
                cycle_result['actions'].append('optimization_applied')
                cycle_result['optimization'] = optimization
        
        return cycle_result
    
    def run_continuous(self, duration_hours: int = 24):
        """연속 실행"""
        self.logger.info(f"Starting continuous feedback loop for {duration_hours} hours")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        while datetime.now() < end_time:
            try:
                cycle_result = self.run_cycle()
                
                if cycle_result['actions']:
                    self.logger.info(f"Cycle completed: {', '.join(cycle_result['actions'])}")
                
                # 다음 사이클까지 대기
                time.sleep(self.collection_interval)
            
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in feedback loop: {e}")
                time.sleep(self.collection_interval)
        
        self.logger.info("Continuous feedback loop ended")
        self._print_summary()
    
    def _print_summary(self):
        """요약 출력"""
        print("\n" + "="*60)
        print("  Realtime Feedback Loop Summary")
        print("="*60)
        print(f"Samples Collected: {self.learning_state['samples_collected']}")
        print(f"Learning Cycles: {self.learning_state['learning_cycles']}")
        print(f"Last Learning: {self.learning_state['last_learning']}")
        print(f"Last Optimization: {self.learning_state['last_optimization']}")
        print("="*60 + "\n")


def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1:
        workspace_root = Path(sys.argv[1])
    else:
        workspace_root = Path(__file__).parent.parent.parent
    
    # 피드백 루프 생성
    feedback_loop = RealtimeFeedbackLoop(
        workspace_root=workspace_root,
        collection_interval=60,  # 1분마다
        learning_threshold=5,     # 5개 샘플마다 학습
        optimization_threshold=0.1
    )
    
    # 연속 실행 (1시간)
    feedback_loop.run_continuous(duration_hours=1)


if __name__ == '__main__':
    main()
