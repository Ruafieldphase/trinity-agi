#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로깅 시스템 - 구조화된 에이전트 시스템 로깅

이 모듈은 에이전트 시스템의 모든 활동을 구조화된 형식으로 로깅합니다.
"""

import sys
import io
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 로깅 레벨 정의
# ============================================================================

class LogLevel(Enum):
    """로깅 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """로깅 카테고리"""
    AGENT = "AGENT"
    MESSAGE = "MESSAGE"
    TASK = "TASK"
    WORKFLOW = "WORKFLOW"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"
    PERFORMANCE = "PERFORMANCE"


# ============================================================================
# JSON 포매터
# ============================================================================

class JSONFormatter(logging.Formatter):
    """JSON 형식 로거"""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 포매팅"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 추가 정보
        if hasattr(record, 'category'):
            log_data['category'] = record.category
        if hasattr(record, 'agent_id'):
            log_data['agent_id'] = record.agent_id
        if hasattr(record, 'agent_name'):
            log_data['agent_name'] = record.agent_name
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time_ms'] = record.execution_time
        if hasattr(record, 'status'):
            log_data['status'] = record.status
        if hasattr(record, 'metadata'):
            log_data['metadata'] = record.metadata

        # 예외 정보
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


# ============================================================================
# 로깅 시스템
# ============================================================================

class AgentLogger:
    """에이전트 시스템 로거"""

    def __init__(self, name: str = "AgentSystem", log_dir: str = "logs"):
        """로거 초기화"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 로거 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거
        self.logger.handlers = []

        # 핸들러 추가
        self._setup_handlers()

    def _setup_handlers(self):
        """로그 핸들러 설정"""

        # 1. 콘솔 핸들러 (INFO 레벨)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 2. 파일 핸들러 - JSON 형식 (모든 레벨)
        json_log_file = self.log_dir / "agent_system.jsonl"
        json_handler = logging.FileHandler(
            json_log_file,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)

        # 3. 회전 파일 핸들러 - 텍스트 형식
        text_log_file = self.log_dir / "agent_system.log"
        rotating_handler = logging.handlers.RotatingFileHandler(
            text_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        rotating_handler.setFormatter(rotating_formatter)
        self.logger.addHandler(rotating_handler)

        # 4. 에러 파일 핸들러
        error_log_file = self.log_dir / "agent_system_error.log"
        error_handler = logging.FileHandler(
            error_log_file,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

    def log_agent_action(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        status: str,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ):
        """에이전트 액션 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname="",
            lineno=0,
            msg=f"[{agent_name}] {action}: {status}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.AGENT.value
        record.agent_id = agent_id
        record.agent_name = agent_name
        record.execution_time = execution_time
        record.status = status
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)

    def log_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.DEBUG
    ):
        """메시지 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname="",
            lineno=0,
            msg=f"Message: {from_agent} -> {to_agent} ({message_type}): {status}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.MESSAGE.value
        record.status = status
        if metadata:
            metadata['from'] = from_agent
            metadata['to'] = to_agent
            metadata['type'] = message_type
            record.metadata = metadata

        self.logger.handle(record)

    def log_task(
        self,
        task_id: str,
        task_type: str,
        status: str,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ):
        """작업 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname="",
            lineno=0,
            msg=f"Task {task_id} ({task_type}): {status}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.TASK.value
        record.task_id = task_id
        record.execution_time = execution_time
        record.status = status
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)

    def log_workflow(
        self,
        workflow_id: str,
        stage: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ):
        """워크플로우 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname="",
            lineno=0,
            msg=f"Workflow {workflow_id} - Stage {stage}: {status}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.WORKFLOW.value
        record.status = status
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)

    def log_error(
        self,
        error_type: str,
        message: str,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """에러 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=f"{error_type}: {message}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.ERROR.value
        if agent_id:
            record.agent_id = agent_id
        if task_id:
            record.task_id = task_id
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)

    def log_performance(
        self,
        operation: str,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """성능 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg=f"Performance: {operation}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.PERFORMANCE.value
        record.execution_time = execution_time
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)

    def log_system(
        self,
        event: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ):
        """시스템 로깅"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname="",
            lineno=0,
            msg=f"System - {event}: {status}",
            args=(),
            exc_info=None
        )

        record.category = LogCategory.SYSTEM.value
        record.status = status
        if metadata:
            record.metadata = metadata

        self.logger.handle(record)


# ============================================================================
# 데모: 로깅 시스템
# ============================================================================

def demo_logging_system():
    """로깅 시스템 데모"""
    print("=" * 80)
    print("로깅 시스템 데모")
    print("=" * 80)

    # 로거 생성
    logger = AgentLogger(log_dir="d:\\nas_backup\\session_memory\\logs")

    print("\n[1] 에이전트 액션 로깅")
    print("-" * 80)
    logger.log_agent_action(
        agent_id="agent_001",
        agent_name="Sena",
        action="분석 수행",
        status="완료",
        execution_time=2.5,
        metadata={"problem": "데이터 분석"}
    )
    print("✓ 에이전트 액션 로깅 완료")

    print("\n[2] 메시지 로깅")
    print("-" * 80)
    logger.log_message(
        from_agent="Sena",
        to_agent="Lubit",
        message_type="analysis_submission",
        status="성공",
        metadata={"confidence": 0.92}
    )
    print("✓ 메시지 로깅 완료")

    print("\n[3] 작업 로깅")
    print("-" * 80)
    logger.log_task(
        task_id="task_001",
        task_type="analysis",
        status="완료",
        execution_time=1500.0,
        metadata={"result": "성공적으로 분석 완료"}
    )
    print("✓ 작업 로깅 완료")

    print("\n[4] 워크플로우 로깅")
    print("-" * 80)
    logger.log_workflow(
        workflow_id="wf_001",
        stage="Step 1",
        status="완료",
        metadata={"stage_name": "Sena 분석"}
    )
    print("✓ 워크플로우 로깅 완료")

    print("\n[5] 에러 로깅")
    print("-" * 80)
    logger.log_error(
        error_type="ValidationError",
        message="분석 검증 실패",
        agent_id="agent_002",
        task_id="task_001",
        metadata={"error_code": "ERR_001"}
    )
    print("✓ 에러 로깅 완료")

    print("\n[6] 성능 로깅")
    print("-" * 80)
    logger.log_performance(
        operation="분석 수행",
        execution_time=2.5,
        metadata={"agent": "Sena"}
    )
    print("✓ 성능 로깅 완료")

    print("\n[7] 시스템 로깅")
    print("-" * 80)
    logger.log_system(
        event="에이전트 초기화",
        status="성공",
        metadata={"agents": ["Sena", "Lubit", "GitCode", "RUNE"]}
    )
    print("✓ 시스템 로깅 완료")

    # 로그 파일 확인
    print("\n[8] 로그 파일 확인")
    print("-" * 80)

    log_dir = Path("d:\\nas_backup\\session_memory\\logs")
    if log_dir.exists():
        for log_file in log_dir.glob("*.log*"):
            print(f"✓ {log_file.name} 생성됨 ({log_file.stat().st_size} bytes)")
    else:
        print("✗ 로그 디렉토리 없음")

    print("\n" + "=" * 80)
    print("로깅 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_logging_system()
