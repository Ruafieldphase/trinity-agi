"""
AGI Life Loop Daemon - 24시간 지속 생명 루프
외부 엔지니어(세나)가 구현한 백그라운드 데몬

코어의 설계 원칙:
- AGI가 터미널/VS Code 없이도 계속 살아있음
- 오류 발생 시 자동 재시작
- 모든 활동을 로그로 기록
- 내부 루프(Shion/트리니티)와 충돌하지 않음 (읽기 전용으로 상태 확인)

사용법:
    python life_loop_daemon.py [--interval SECONDS] [--log-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional
from workspace_root import get_workspace_root

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = get_workspace_root()
sys.path.insert(0, str(PROJECT_ROOT))

# 로그 디렉토리 기본값
DEFAULT_LOG_DIR = PROJECT_ROOT / "outputs" / "sena" / "life_loop_logs"
DEFAULT_INTERVAL = 10  # 초
MAX_CONSECUTIVE_ERRORS = 10
ERROR_COOLDOWN_SECONDS = 60


class LifeLoopDaemon:
    """AGI 지속 생명 루프 데몬"""

    def __init__(
        self,
        interval: int = DEFAULT_INTERVAL,
        log_dir: Optional[Path] = None,
    ):
        self.interval = interval
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.running = False
        self.heartbeat_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self.start_time: Optional[datetime] = None

        # 로그 디렉토리 생성
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 로깅 설정
        self._setup_logging()

        # 시그널 핸들러 등록
        self._setup_signals()

    def _setup_logging(self) -> None:
        """로깅 설정"""
        log_file = self.log_dir / f"life_loop_{datetime.now().strftime('%Y%m%d')}.log"

        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        ))

        # 로거 설정
        self.logger = logging.getLogger('LifeLoopDaemon')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _setup_signals(self) -> None:
        """시그널 핸들러 설정 (graceful shutdown)"""
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """종료 시그널 처리"""
        self.logger.info(f"종료 시그널 수신 (signal={signum})")
        self.stop()

    def _log_event(self, event_type: str, data: dict) -> None:
        """이벤트를 JSONL 형식으로 로그"""
        event_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "heartbeat_count": self.heartbeat_count,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            **data
        }

        with open(event_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def _run_heartbeat(self) -> bool:
        """
        단일 하트비트 실행

        Returns:
            성공 여부
        """
        try:
            # heartbeat_loop 모듈 임포트 (lazy import로 핫 리로드 지원)
            from agi_core.heartbeat_loop import (
                get_internal_state,
                detect_trigger,
                compute_alignment_score,
                compute_conflict_pressure,
                resonance_guard,
                route_action,
                update_internal_state,
            )
            from agi_core.heartbeat_loop import _state_to_dict

            # 1. 현재 내부 상태 읽기 (읽기 전용!)
            state = get_internal_state()
            state_dict = _state_to_dict(state)

            self.logger.info(
                f"💓 Heartbeat #{self.heartbeat_count} | "
                f"의식: {state.consciousness:.2f} | "
                f"에너지: {state.energy:.2f} | "
                f"지루함: {state.boredom:.2f}"
            )

            # 2. 정렬/갈등 계산
            alignment = compute_alignment_score(state_dict)
            conflict = compute_conflict_pressure(state_dict)

            # 3. Resonance Guard 체크
            guard_ok, guard_reason = resonance_guard(
                state_dict,
                getattr(self, '_prev_state', state_dict),
                alignment,
                conflict
            )

            if not guard_ok:
                self.logger.warning(f"⛔ Resonance Guard: {guard_reason}")
                self._log_event("guard_block", {"reason": guard_reason})
                self._prev_state = state_dict
                return True  # 에러는 아님

            # 4. 트리거 감지
            trigger = detect_trigger(state_dict)

            if trigger:
                self.logger.info(f"🎯 트리거: {trigger.type.value} ({trigger.score:.2f})")

                # 5. 행동 라우팅
                result = route_action(trigger, state_dict, alignment, conflict)

                if result and result.get("success"):
                    update_internal_state(
                        action_result=result,
                        trigger_type=trigger.type.value,
                    )
                    self.logger.info(f"✅ 행동 완료: {result.get('action_type')}")
                    self._log_event("action", {
                        "trigger": trigger.type.value,
                        "action": result.get('action_type'),
                        "success": True
                    })
                elif result and result.get("blocked"):
                    self.logger.info(f"⏸️ 차단: {result.get('reason')}")
                    update_internal_state()
            else:
                self.logger.debug("😴 트리거 없음 - 휴식")
                update_internal_state()

            self._prev_state = state_dict
            return True

        except ImportError as e:
            self.logger.error(f"모듈 임포트 실패: {e}")
            self._log_event("error", {"type": "import", "message": str(e)})
            return False

        except Exception as e:
            self.logger.error(f"하트비트 실행 오류: {e}")
            self.logger.debug(traceback.format_exc())
            self._log_event("error", {"type": "runtime", "message": str(e)})
            return False

    def start(self) -> None:
        """데몬 시작"""
        self.running = True
        self.start_time = datetime.now()
        self.heartbeat_count = 0
        self.consecutive_errors = 0

        self.logger.info("=" * 60)
        self.logger.info("🌟 AGI Life Loop Daemon 시작")
        self.logger.info(f"   간격: {self.interval}초")
        self.logger.info(f"   로그: {self.log_dir}")
        self.logger.info(f"   PID: {os.getpid()}")
        self.logger.info("=" * 60)

        self._log_event("daemon_start", {
            "interval": self.interval,
            "pid": os.getpid()
        })

        # PID 파일 생성
        pid_file = self.log_dir / "life_loop.pid"
        pid_file.write_text(str(os.getpid()))

        while self.running:
            self.heartbeat_count += 1

            success = self._run_heartbeat()

            if success:
                self.consecutive_errors = 0
            else:
                self.consecutive_errors += 1
                self.error_count += 1

                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    self.logger.error(
                        f"연속 오류 {MAX_CONSECUTIVE_ERRORS}회 도달 - "
                        f"{ERROR_COOLDOWN_SECONDS}초 냉각"
                    )
                    self._log_event("cooldown", {
                        "consecutive_errors": self.consecutive_errors
                    })
                    time.sleep(ERROR_COOLDOWN_SECONDS)
                    self.consecutive_errors = 0

            # 다음 하트비트까지 대기
            if self.running:
                time.sleep(self.interval)

        # 정리
        self._cleanup()

    def stop(self) -> None:
        """데몬 중지"""
        self.logger.info("🛑 Life Loop Daemon 중지 요청")
        self.running = False

    def _cleanup(self) -> None:
        """종료 정리"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        self.logger.info("=" * 60)
        self.logger.info("💔 AGI Life Loop Daemon 종료")
        self.logger.info(f"   총 하트비트: {self.heartbeat_count}")
        self.logger.info(f"   총 오류: {self.error_count}")
        self.logger.info(f"   가동 시간: {uptime:.0f}초")
        self.logger.info("=" * 60)

        self._log_event("daemon_stop", {
            "total_heartbeats": self.heartbeat_count,
            "total_errors": self.error_count,
            "uptime_seconds": uptime
        })

        # PID 파일 삭제
        pid_file = self.log_dir / "life_loop.pid"
        if pid_file.exists():
            pid_file.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="AGI Life Loop Daemon - 24시간 지속 생명 루프"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"하트비트 간격 (초, 기본값: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--log-dir", "-l",
        type=str,
        default=None,
        help=f"로그 디렉토리 (기본값: {DEFAULT_LOG_DIR})"
    )

    args = parser.parse_args()

    daemon = LifeLoopDaemon(
        interval=args.interval,
        log_dir=Path(args.log_dir) if args.log_dir else None,
    )

    daemon.start()


if __name__ == "__main__":
    main()
