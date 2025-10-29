"""
구조화된 로깅 설정 모듈

JSON 형식의 구조화된 로깅을 제공합니다.
로컬 로깅 + Google Cloud Logging 지원
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from app.config import settings


class StructuredFormatter(jsonlogger.JsonFormatter):
    """
    구조화된 JSON 포맷터

    모든 로그를 JSON 형식으로 변환합니다.
    timestamp, level, message, context 등을 포함합니다.
    """

    def add_fields(
        self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
    ) -> None:
        """JSON에 추가 필드 추가"""
        super().add_fields(log_record, record, message_dict)

        # 타임스탬프
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # 로그 레벨
        log_record["level"] = record.levelname.upper()

        # 모듈 정보
        log_record["module"] = record.name
        log_record["function"] = record.funcName
        log_record["line_number"] = record.lineno

        # 예외 정보
        if record.exc_info and record.exc_info[0] is not None:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exc(),
            }

        # 환경 정보
        log_record["environment"] = settings.environment
        log_record["service"] = settings.app_name
        log_record["version"] = settings.app_version


class CloudLoggingHandler(logging.Handler):
    """
    Google Cloud Logging 핸들러

    프로덕션 환경에서 Google Cloud Logging에 로그를 전송합니다.
    """

    def __init__(self, cloud_logger=None):
        """
        Args:
            cloud_logger: Google Cloud Logging logger 인스턴스
        """
        super().__init__()
        self.cloud_logger = cloud_logger

    def emit(self, record: logging.LogRecord) -> None:
        """로그를 Google Cloud Logging으로 전송"""
        if not self.cloud_logger:
            return

        try:
            message = self.format(record)

            # JSON 파싱
            try:
                log_dict = json.loads(message)
            except json.JSONDecodeError:
                log_dict = {"message": message}

            # severity 매핑
            severity_map = {
                "DEBUG": "DEBUG",
                "INFO": "INFO",
                "WARNING": "WARNING",
                "ERROR": "ERROR",
                "CRITICAL": "CRITICAL",
            }
            severity = severity_map.get(record.levelname, "DEFAULT")

            # Cloud Logging에 전송
            self.cloud_logger.log_struct(log_dict, severity=severity)
        except Exception:
            self.handleError(record)


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_cloud_logging: bool = False,
    cloud_logger=None,
) -> logging.Logger:
    """
    로깅 시스템 초기화

    Args:
        name: 로거 이름
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (선택)
        use_cloud_logging: Google Cloud Logging 사용 여부
        cloud_logger: Google Cloud Logging logger 인스턴스

    Returns:
        설정된 Logger 인스턴스
    """
    logger = logging.getLogger(name)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers = []

    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 포맷터 설정
    formatter = StructuredFormatter()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (선택)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Google Cloud Logging 핸들러 (프로덕션)
    if use_cloud_logging and cloud_logger:
        cloud_handler = CloudLoggingHandler(cloud_logger)
        cloud_handler.setFormatter(formatter)
        logger.addHandler(cloud_handler)

    # 부모 로거에 전파하지 않음 (중복 로그 방지)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기

    Args:
        name: 로거 이름

    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name)


def log_execution(logger: logging.Logger, operation: str, **context):
    """
    작업 실행 로깅

    Args:
        logger: Logger 인스턴스
        operation: 작업 이름
        **context: 추가 컨텍스트 정보
    """
    logger.info(
        f"Operation started: {operation}", extra={"operation": operation, "context": context}
    )


def log_error(logger: logging.Logger, operation: str, error: Exception, **context):
    """
    에러 로깅

    Args:
        logger: Logger 인스턴스
        operation: 작업 이름
        error: Exception 인스턴스
        **context: 추가 컨텍스트 정보
    """
    logger.error(
        f"Operation failed: {operation} - {str(error)}",
        exc_info=True,
        extra={
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
        },
    )


def log_metric(logger: logging.Logger, metric_name: str, value: float, **tags):
    """
    메트릭 로깅

    Args:
        logger: Logger 인스턴스
        metric_name: 메트릭 이름
        value: 메트릭 값
        **tags: 태그 정보
    """
    logger.info(
        f"Metric recorded: {metric_name}",
        extra={
            "metric_name": metric_name,
            "metric_value": value,
            "metric_type": "gauge",
            "tags": tags,
        },
    )


def log_request(
    logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float, **context
):
    """
    HTTP 요청 로깅

    Args:
        logger: Logger 인스턴스
        method: HTTP 메서드
        path: 요청 경로
        status_code: 응답 상태 코드
        duration_ms: 처리 시간 (밀리초)
        **context: 추가 컨텍스트 정보
    """
    level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"
    log_func = getattr(logger, level)

    log_func(
        f"HTTP request: {method} {path} {status_code} ({duration_ms:.1f}ms)",
        extra={
            "http": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
            "context": context,
        },
    )
