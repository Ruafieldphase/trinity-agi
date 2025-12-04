"""
Failsafe Mechanism
Phase 2.5 Week 2 Day 12

RPA 실행 안전장치
- 긴급 중단 (마우스 모서리)
- 타임아웃
- 에러 자동 복구
- 롤백
"""

import time
import threading
from dataclasses import dataclass
from typing import Optional, Callable, Any
from pathlib import Path
import logging

import pyautogui

logger = logging.getLogger(__name__)


@dataclass
class FailsafeConfig:
    """Failsafe 설정"""
    # pyautogui 기본 안전장치
    enable_pyautogui_failsafe: bool = True  # 마우스를 화면 모서리로 이동하면 중단
    pause_between_actions: float = 0.1       # 액션 간 일시정지
    
    # 타임아웃
    enable_timeout: bool = True
    action_timeout: float = 30.0             # 개별 액션 타임아웃 (초)
    total_timeout: float = 3600.0            # 전체 실행 타임아웃 (초)
    
    # 에러 복구
    enable_auto_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 긴급 중단
    emergency_stop_key: str = "esc"          # 긴급 중단 단축키
    enable_emergency_listener: bool = False  # 키보드 리스너 (백그라운드)
    
    # 롤백
    enable_snapshot: bool = True             # 실행 전 상태 스냅샷
    max_snapshots: int = 10                  # 최대 스냅샷 개수


class FailsafeException(Exception):
    """Failsafe로 인한 중단"""
    pass


class TimeoutException(Exception):
    """타임아웃"""
    pass


class Failsafe:
    """
    RPA 안전장치 관리자
    
    Features:
    - pyautogui FAILSAFE (마우스 모서리)
    - 액션 타임아웃
    - 에러 자동 재시도
    - 긴급 중단 (ESC)
    - 상태 스냅샷 및 롤백
    """
    
    def __init__(self, config: Optional[FailsafeConfig] = None):
        """
        Args:
            config: Failsafe 설정 (None이면 기본값)
        """
        self.config = config or FailsafeConfig()
        
        # pyautogui 설정
        if self.config.enable_pyautogui_failsafe:
            pyautogui.FAILSAFE = True
            logger.info("pyautogui FAILSAFE enabled (move mouse to corner to abort)")
        else:
            pyautogui.FAILSAFE = False
        
        pyautogui.PAUSE = self.config.pause_between_actions
        logger.info(f"pyautogui PAUSE: {self.config.pause_between_actions}s")
        
        # 상태
        self._emergency_stop = False
        self._listener_thread = None
        self._snapshots = []
        
        # 긴급 중단 리스너 시작
        if self.config.enable_emergency_listener:
            self.start_emergency_listener()
    
    # ========================================================================
    # Emergency Stop
    # ========================================================================
    
    def start_emergency_listener(self):
        """긴급 중단 키보드 리스너 시작"""
        if self._listener_thread and self._listener_thread.is_alive():
            logger.warning("Emergency listener already running")
            return
        
        try:
            from pynput import keyboard
        except ImportError:
            logger.error("pynput not installed. Install with: pip install pynput")
            return
        
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == self.config.emergency_stop_key:
                    logger.warning(f"Emergency stop triggered: {key}")
                    self._emergency_stop = True
            except AttributeError:
                if key == keyboard.Key.esc and self.config.emergency_stop_key == "esc":
                    logger.warning("Emergency stop triggered: ESC")
                    self._emergency_stop = True
        
        listener = keyboard.Listener(on_press=on_press)
        
        self._listener_thread = threading.Thread(target=listener.start, daemon=True)
        self._listener_thread.start()
        
        logger.info(f"Emergency listener started (key: {self.config.emergency_stop_key})")
    
    def check_emergency_stop(self):
        """긴급 중단 확인"""
        if self._emergency_stop:
            raise FailsafeException("Emergency stop triggered")
    
    def reset_emergency_stop(self):
        """긴급 중단 플래그 리셋"""
        self._emergency_stop = False
        logger.debug("Emergency stop flag reset")
    
    # ========================================================================
    # Timeout
    # ========================================================================
    
    def with_timeout(
        self,
        func: Callable,
        timeout: Optional[float] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        타임아웃과 함께 함수 실행
        
        Args:
            func: 실행할 함수
            timeout: 타임아웃 (None이면 config 기본값)
            *args, **kwargs: func에 전달할 인자
        
        Returns:
            함수 반환값
        
        Raises:
            TimeoutException: 타임아웃 발생
        """
        if not self.config.enable_timeout:
            return func(*args, **kwargs)
        
        timeout = timeout or self.config.action_timeout
        
        result = [None]
        exception = [None]
        
        def wrapper():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            logger.error(f"Timeout after {timeout}s")
            raise TimeoutException(f"Function timeout after {timeout}s")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    # ========================================================================
    # Retry
    # ========================================================================
    
    def with_retry(
        self,
        func: Callable,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        재시도와 함께 함수 실행
        
        Args:
            func: 실행할 함수
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간
            *args, **kwargs: func에 전달할 인자
        
        Returns:
            함수 반환값
        
        Raises:
            마지막 예외
        """
        if not self.config.enable_auto_retry:
            return func(*args, **kwargs)
        
        max_retries = max_retries or self.config.max_retries
        retry_delay = retry_delay or self.config.retry_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}, "
                        f"retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        raise last_exception
    
    # ========================================================================
    # Snapshot & Rollback
    # ========================================================================
    
    def take_snapshot(
        self,
        name: str,
        data: dict
    ):
        """
        상태 스냅샷 저장
        
        Args:
            name: 스냅샷 이름
            data: 저장할 데이터
        """
        if not self.config.enable_snapshot:
            return
        
        snapshot = {
            "name": name,
            "timestamp": time.time(),
            "data": data
        }
        
        self._snapshots.append(snapshot)
        
        # 최대 개수 초과 시 오래된 것 삭제
        if len(self._snapshots) > self.config.max_snapshots:
            removed = self._snapshots.pop(0)
            logger.debug(f"Snapshot removed (max reached): {removed['name']}")
        
        logger.debug(f"Snapshot taken: {name}")
    
    def get_snapshot(self, name: str) -> Optional[dict]:
        """
        스냅샷 조회
        
        Args:
            name: 스냅샷 이름
        
        Returns:
            스냅샷 데이터 (없으면 None)
        """
        for snapshot in reversed(self._snapshots):
            if snapshot["name"] == name:
                return snapshot["data"]
        return None
    
    def get_latest_snapshot(self) -> Optional[dict]:
        """
        최신 스냅샷 조회
        
        Returns:
            최신 스냅샷 (없으면 None)
        """
        if self._snapshots:
            return self._snapshots[-1]["data"]
        return None
    
    def rollback(
        self,
        rollback_func: Callable[[dict], None],
        snapshot_name: Optional[str] = None
    ):
        """
        스냅샷으로 롤백
        
        Args:
            rollback_func: 롤백 실행 함수 (snapshot_data를 인자로 받음)
            snapshot_name: 롤백할 스냅샷 이름 (None이면 최신)
        """
        if snapshot_name:
            snapshot_data = self.get_snapshot(snapshot_name)
            if not snapshot_data:
                logger.error(f"Snapshot not found: {snapshot_name}")
                return
        else:
            snapshot_data = self.get_latest_snapshot()
            if not snapshot_data:
                logger.error("No snapshots available for rollback")
                return
        
        logger.info(f"Rolling back to snapshot: {snapshot_name or 'latest'}")
        
        try:
            rollback_func(snapshot_data)
            logger.info("Rollback successful")
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
    
    def clear_snapshots(self):
        """모든 스냅샷 삭제"""
        count = len(self._snapshots)
        self._snapshots.clear()
        logger.info(f"Cleared {count} snapshots")
    
    # ========================================================================
    # Safe Execution
    # ========================================================================
    
    def safe_execute(
        self,
        func: Callable,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        안전한 함수 실행 (타임아웃 + 재시도 + 긴급 중단 체크)
        
        Args:
            func: 실행할 함수
            timeout: 타임아웃
            max_retries: 재시도 횟수
            *args, **kwargs: func 인자
        
        Returns:
            함수 반환값
        """
        # 긴급 중단 체크
        self.check_emergency_stop()
        
        # 재시도와 함께 실행
        def with_checks():
            # 긴급 중단 체크
            self.check_emergency_stop()
            
            # 타임아웃과 함께 실행
            return self.with_timeout(func, timeout, *args, **kwargs)
        
        return self.with_retry(with_checks, max_retries=max_retries)
    
    # ========================================================================
    # Context Manager
    # ========================================================================
    
    def __enter__(self):
        """Context manager 시작"""
        self.reset_emergency_stop()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        if exc_type is FailsafeException:
            logger.warning("Execution stopped by failsafe")
        elif exc_type is TimeoutException:
            logger.error("Execution timed out")
        return False  # 예외 전파


# ============================================================================
# Convenience Functions
# ============================================================================

def enable_failsafe():
    """pyautogui FAILSAFE 활성화"""
    pyautogui.FAILSAFE = True
    logger.info("pyautogui FAILSAFE enabled")


def disable_failsafe():
    """pyautogui FAILSAFE 비활성화 (주의!)"""
    pyautogui.FAILSAFE = False
    logger.warning("pyautogui FAILSAFE disabled (use with caution)")


def set_pause(seconds: float):
    """액션 간 일시정지 시간 설정"""
    pyautogui.PAUSE = seconds
    logger.info(f"pyautogui PAUSE set to {seconds}s")


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("\n" + "="*60)
    print("  Failsafe Mechanism Test")
    print("="*60 + "\n")
    
    # 설정
    config = FailsafeConfig(
        enable_pyautogui_failsafe=True,
        pause_between_actions=0.1,
        enable_timeout=True,
        action_timeout=5.0,
        enable_auto_retry=True,
        max_retries=2
    )
    
    failsafe = Failsafe(config=config)
    
    # Test 1: 정상 실행
    print("[Test 1] Normal execution")
    def test_func():
        print("  Executing...")
        time.sleep(0.5)
        return "OK"
    
    result = failsafe.safe_execute(test_func)
    print(f"  Result: {result}\n")
    
    # Test 2: 재시도 (실패 후 성공)
    print("[Test 2] Retry mechanism")
    attempt = [0]
    def flaky_func():
        attempt[0] += 1
        if attempt[0] < 2:
            raise ValueError("Simulated error")
        return "OK after retry"
    
    try:
        result = failsafe.safe_execute(flaky_func)
        print(f"  Result: {result}\n")
    except Exception as e:
        print(f"  Failed: {e}\n")
    
    # Test 3: 스냅샷
    print("[Test 3] Snapshot")
    failsafe.take_snapshot("state1", {"data": "test"})
    snapshot = failsafe.get_latest_snapshot()
    print(f"  Snapshot: {snapshot}\n")
    
    print("="*60)
    print("  ⚠️  pyautogui FAILSAFE is enabled:")
    print("  Move mouse to screen corner to trigger emergency stop")
    print("="*60 + "\n")
