"""
Trial-and-Error Engine
Phase 2.5 Day 7: Reinforcement Learning Style Self-Learning

Features:
1. 실행 → 실패 → 다른 방법 시도 (Trial-and-Error)
2. Resonance Ledger 통합 (학습 기록)
3. BQI 기반 성공률 평가
4. 패턴 마이닝 및 재사용

Design:
- State-Action-Reward 패턴
- Experience Replay (과거 경험 재사용)
- Epsilon-Greedy 탐색 전략
- Resonance Ledger 자동 기록
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class TrialErrorConfig:
    """Trial-and-Error Engine 설정"""
    output_dir: Path = Path("outputs/trial_error")
    ledger_path: Path = Path("memory/resonance_ledger.jsonl")
    experience_db: Path = Path("memory/trial_error_experience.jsonl")
    
    # 학습 파라미터
    max_trials: int = 5  # 최대 시도 횟수
    success_threshold: float = 0.7  # 성공 판정 임계값
    
    # 탐색 전략
    epsilon: float = 0.3  # Epsilon-Greedy (탐색 확률)
    epsilon_decay: float = 0.95  # Epsilon 감소율
    min_epsilon: float = 0.1  # 최소 Epsilon
    
    # 보상 설정
    success_reward: float = 1.0
    failure_penalty: float = -0.5
    timeout_penalty: float = -0.3
    
    log_level: str = "INFO"


# ============================================================================
# Data Models
# ============================================================================

class ActionStatus(str, Enum):
    """액션 상태"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RETRY = "retry"


@dataclass
class Action:
    """실행 액션"""
    name: str
    params: Dict[str, Any]
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrialResult:
    """시도 결과"""
    action: Action
    status: ActionStatus
    reward: float
    duration: float  # 실행 시간 (초)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['action'] = self.action.to_dict()
        return data


@dataclass
class Experience:
    """학습 경험"""
    state: Dict[str, Any]  # 시작 상태
    action: Action  # 수행한 액션
    reward: float  # 보상
    next_state: Dict[str, Any]  # 결과 상태
    trial_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['action'] = self.action.to_dict()
        return data


# ============================================================================
# Trial-and-Error Engine
# ============================================================================

class TrialErrorEngine:
    """Trial-and-Error 학습 엔진"""
    
    def __init__(self, config: Optional[TrialErrorConfig] = None):
        self.config = config or TrialErrorConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Output 디렉토리 생성
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Experience Database 로드
        self.experiences: List[Experience] = []
        self._load_experiences()
        
        # 현재 Epsilon
        self.current_epsilon = self.config.epsilon
        
        self.logger.info("Trial-and-Error Engine initialized")
    
    async def execute_with_retry(
        self,
        task_fn: Callable[..., Any],
        task_name: str,
        initial_params: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[TrialResult]]:
        """
        Trial-and-Error 방식으로 작업 실행
        
        Returns:
            (성공 여부, 시도 결과 리스트)
        """
        state = state or {}
        results = []
        
        self.logger.info(f"Starting trial-and-error execution: {task_name}")
        
        for trial_num in range(self.config.max_trials):
            self.logger.info(f"Trial {trial_num + 1}/{self.config.max_trials}")
            
            # 액션 선택 (Epsilon-Greedy)
            action = self._select_action(task_name, initial_params, state)
            
            # 액션 실행
            trial_result = await self._execute_action(task_fn, action)
            results.append(trial_result)
            
            # 성공 판정
            if trial_result.status == ActionStatus.SUCCESS:
                self.logger.info(f"✅ Task succeeded on trial {trial_num + 1}")
                
                # 경험 저장
                experience = Experience(
                    state=state,
                    action=action,
                    reward=trial_result.reward,
                    next_state={"status": "success"}
                )
                await self._save_experience(experience)
                
                # Resonance Ledger 기록
                await self._log_to_ledger(task_name, results, success=True)
                
                return True, results
            
            # 실패 시 다음 시도 준비
            self.logger.warning(
                f"❌ Trial {trial_num + 1} failed: {trial_result.error_message}"
            )
            
            # 파라미터 조정 (간단한 휴리스틱)
            initial_params = self._adjust_params(initial_params, trial_result)
            
            # Epsilon 감소
            self._decay_epsilon()
        
        # 모든 시도 실패
        self.logger.error(f"❌ Task failed after {self.config.max_trials} trials")
        
        # Resonance Ledger 기록
        await self._log_to_ledger(task_name, results, success=False)
        
        return False, results
    
    def _select_action(
        self,
        task_name: str,
        params: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Action:
        """
        Epsilon-Greedy 전략으로 액션 선택
        
        - Epsilon 확률로 랜덤 탐색
        - (1-Epsilon) 확률로 과거 경험 활용
        """
        import random
        
        if random.random() < self.current_epsilon:
            # 탐색: 파라미터 약간 변형
            self.logger.debug("Exploration: Random action")
            return Action(
                name=task_name,
                params=self._randomize_params(params),
                description="Exploration action"
            )
        else:
            # 활용: 과거 성공 경험 재사용
            self.logger.debug("Exploitation: Using past experience")
            best_experience = self._get_best_experience(task_name, state)
            
            if best_experience:
                return best_experience.action
            else:
                # 경험 없으면 기본 파라미터
                return Action(
                    name=task_name,
                    params=params,
                    description="Default action (no experience)"
                )
    
    async def _execute_action(
        self,
        task_fn: Callable[..., Any],
        action: Action
    ) -> TrialResult:
        """액션 실행 및 결과 평가"""
        import time
        
        start_time = time.time()
        
        try:
            # 작업 실행
            result = await asyncio.wait_for(
                task_fn(**action.params),
                timeout=30.0
            )
            
            duration = time.time() - start_time
            
            # 성공 판정 (간단한 휴리스틱)
            if result and (isinstance(result, bool) and result):
                return TrialResult(
                    action=action,
                    status=ActionStatus.SUCCESS,
                    reward=self.config.success_reward,
                    duration=duration
                )
            else:
                return TrialResult(
                    action=action,
                    status=ActionStatus.FAILURE,
                    reward=self.config.failure_penalty,
                    duration=duration,
                    error_message="Task returned falsy value"
                )
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TrialResult(
                action=action,
                status=ActionStatus.TIMEOUT,
                reward=self.config.timeout_penalty,
                duration=duration,
                error_message="Task timeout"
            )
        
        except Exception as e:
            duration = time.time() - start_time
            return TrialResult(
                action=action,
                status=ActionStatus.FAILURE,
                reward=self.config.failure_penalty,
                duration=duration,
                error_message=str(e)
            )
    
    def _adjust_params(
        self,
        params: Dict[str, Any],
        trial_result: TrialResult
    ) -> Dict[str, Any]:
        """실패 후 파라미터 조정 (간단한 휴리스틱)"""
        adjusted = params.copy()
        
        # 타임아웃이면 타임아웃 값 증가
        if trial_result.status == ActionStatus.TIMEOUT:
            if 'timeout' in adjusted:
                adjusted['timeout'] *= 1.5
        
        # TODO: 더 정교한 파라미터 조정 로직
        
        return adjusted
    
    def _randomize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """파라미터 랜덤 변형 (탐색용)"""
        import random
        
        randomized = params.copy()
        
        # 간단한 랜덤화 (숫자 파라미터만)
        for key, value in randomized.items():
            if isinstance(value, (int, float)):
                randomized[key] = value * random.uniform(0.8, 1.2)
        
        return randomized
    
    def _get_best_experience(
        self,
        task_name: str,
        state: Dict[str, Any]
    ) -> Optional[Experience]:
        """과거 경험 중 가장 보상이 높았던 경험 반환"""
        relevant_experiences = [
            exp for exp in self.experiences
            if exp.action.name == task_name and exp.reward > 0
        ]
        
        if not relevant_experiences:
            return None
        
        # 보상 기준 정렬
        relevant_experiences.sort(key=lambda x: x.reward, reverse=True)
        return relevant_experiences[0]
    
    def _decay_epsilon(self):
        """Epsilon 감소"""
        self.current_epsilon = max(
            self.config.min_epsilon,
            self.current_epsilon * self.config.epsilon_decay
        )
        self.logger.debug(f"Epsilon decayed to {self.current_epsilon:.3f}")
    
    async def _save_experience(self, experience: Experience):
        """경험 저장"""
        self.experiences.append(experience)
        
        # JSONL 파일에 추가
        with open(self.config.experience_db, "a", encoding="utf-8") as f:
            f.write(json.dumps(experience.to_dict(), ensure_ascii=False) + "\n")
        
        self.logger.debug(f"Experience saved: {experience.trial_id}")
    
    def _load_experiences(self):
        """경험 DB 로드"""
        if not self.config.experience_db.exists():
            self.logger.info("No experience database found. Starting fresh.")
            return
        
        with open(self.config.experience_db, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # TODO: Experience 객체로 복원
                    # self.experiences.append(Experience(...))
                except json.JSONDecodeError:
                    continue
        
        self.logger.info(f"Loaded {len(self.experiences)} experiences")
    
    async def _log_to_ledger(
        self,
        task_name: str,
        results: List[TrialResult],
        success: bool
    ):
        """Resonance Ledger에 기록"""
        event = {
            "ts": datetime.utcnow().isoformat() + "+00:00",
            "event": "trial_error_complete",
            "task_name": task_name,
            "success": success,
            "total_trials": len(results),
            "total_duration": sum(r.duration for r in results),
            "final_reward": results[-1].reward if results else 0,
            "epsilon": self.current_epsilon
        }
        
        # JSONL 파일에 추가
        with open(self.config.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        self.logger.info(f"Logged to Resonance Ledger: {task_name}")


# ============================================================================
# CLI Interface
# ============================================================================

async def example_task(x: int, y: int) -> bool:
    """예제 작업"""
    await asyncio.sleep(0.5)
    return x + y > 10


async def main():
    """CLI 테스트"""
    logging.basicConfig(level=logging.INFO)
    
    engine = TrialErrorEngine()
    
    # 테스트 실행
    success, results = await engine.execute_with_retry(
        task_fn=example_task,
        task_name="add_numbers",
        initial_params={"x": 5, "y": 6},
        state={"context": "test"}
    )
    
    print(f"\n✅ Task completed: {'SUCCESS' if success else 'FAILURE'}")
    print(f"   Total trials: {len(results)}")
    print(f"   Total duration: {sum(r.duration for r in results):.2f}s")
    print(f"   Final epsilon: {engine.current_epsilon:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
