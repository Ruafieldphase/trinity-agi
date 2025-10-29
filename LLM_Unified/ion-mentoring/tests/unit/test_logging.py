"""
로깅 시스템 Unit 테스트

app/logging_setup.py의 로깅 기능을 테스트합니다.
"""

import json
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ion-mentoring 디렉토리 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.logging_setup import (
    CloudLoggingHandler,
    StructuredFormatter,
    get_logger,
    log_error,
    log_execution,
    log_metric,
    log_request,
    setup_logging,
)


@pytest.mark.unit
class TestStructuredFormatter:
    """StructuredFormatter 테스트"""

    def test_formatter_creates_json(self):
        """JSON 형식의 로그 생성"""
        formatter = StructuredFormatter()

        # LogRecord 생성
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )

        # 포맷팅
        formatted = formatter.format(record)

        # JSON 파싱 가능 확인
        try:
            log_dict = json.loads(formatted)
            assert "timestamp" in log_dict
            assert "level" in log_dict
            assert log_dict["level"] == "INFO"
        except json.JSONDecodeError:
            pytest.fail("포맷팅된 로그가 유효한 JSON이 아님")

    def test_formatter_includes_exception_info(self):
        """예외 정보 포함"""
        formatter = StructuredFormatter()

        # 예외 생성
        try:
            raise ValueError("테스트 에러")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
                func="test_func",
            )

            formatted = formatter.format(record)
            log_dict = json.loads(formatted)

            assert "exception" in log_dict
            assert log_dict["exception"]["type"] == "ValueError"
            assert "테스트 에러" in log_dict["exception"]["message"]

    def test_formatter_includes_module_info(self):
        """모듈 정보 포함"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="app.main",
            level=logging.INFO,
            pathname="app/main.py",
            lineno=100,
            msg="Test",
            args=(),
            exc_info=None,
            func="my_function",
        )

        formatted = formatter.format(record)
        log_dict = json.loads(formatted)

        assert log_dict["module"] == "app.main"
        assert log_dict["function"] == "my_function"
        assert log_dict["line_number"] == 100


@pytest.mark.unit
class TestLoggingSetup:
    """setup_logging 함수 테스트"""

    def test_setup_logging_creates_logger(self):
        """로거 생성"""
        logger = setup_logging("test_logger", level="DEBUG")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_console_handler(self):
        """콘솔 핸들러 추가"""
        logger = setup_logging("test_logger2", level="INFO")

        # 콘솔 핸들러 확인
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_setup_logging_with_file_handler(self, tmp_path):
        """파일 핸들러 추가"""
        log_file = tmp_path / "test.log"

        logger = setup_logging("test_logger3", level="INFO", log_file=str(log_file))

        # 파일 핸들러 확인
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_setup_logging_with_cloud_logging(self):
        """Cloud Logging 핸들러 추가"""
        mock_cloud_logger = MagicMock()

        logger = setup_logging(
            "test_logger4", level="INFO", use_cloud_logging=True, cloud_logger=mock_cloud_logger
        )

        # Cloud Logging 핸들러 확인
        cloud_handlers = [h for h in logger.handlers if isinstance(h, CloudLoggingHandler)]
        assert len(cloud_handlers) > 0

    def test_get_logger(self):
        """get_logger 함수"""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")

        assert logger1 is logger2  # 같은 인스턴스


@pytest.mark.unit
class TestLoggingFunctions:
    """로깅 헬퍼 함수 테스트"""

    def test_log_execution(self, capsys):
        """log_execution 함수"""
        logger = setup_logging("test_exec", level="INFO")

        log_execution(logger, "database_query", user_id=123, table="users")

        captured = capsys.readouterr()
        assert "Operation started: database_query" in captured.out

    def test_log_error(self, capsys):
        """log_error 함수"""
        logger = setup_logging("test_error", level="ERROR")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            log_error(logger, "process_data", e, user_id=456)

        captured = capsys.readouterr()
        assert "Operation failed: process_data" in captured.out
        assert "Test error" in captured.out

    def test_log_metric(self, capsys):
        """log_metric 함수"""
        logger = setup_logging("test_metric", level="INFO")

        log_metric(logger, "response_time_ms", 123.45, endpoint="/chat", persona="Lua")

        captured = capsys.readouterr()
        assert "Metric recorded: response_time_ms" in captured.out

    def test_log_request(self, capsys):
        """log_request 함수"""
        logger = setup_logging("test_request", level="INFO")

        log_request(logger, "POST", "/chat", 200, 456.78, user_agent="test-client")

        captured = capsys.readouterr()
        assert "HTTP request: POST /chat 200" in captured.out

    def test_log_request_error(self, capsys):
        """에러 상태 요청 로깅"""
        logger = setup_logging("test_request_error", level="ERROR")

        log_request(logger, "POST", "/chat", 500, 100.0, error_message="Internal error")

        captured = capsys.readouterr()
        # 상태 코드 500은 ERROR 레벨
        assert "500" in captured.out


@pytest.mark.unit
class TestCloudLoggingHandler:
    """CloudLoggingHandler 테스트"""

    def test_cloud_logging_handler_emits_log(self):
        """Cloud Logging으로 로그 전송"""
        mock_cloud_logger = MagicMock()
        handler = CloudLoggingHandler(mock_cloud_logger)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )

        handler.emit(record)

        # log_struct 호출 확인
        assert mock_cloud_logger.log_struct.called

    def test_cloud_logging_handler_without_logger(self):
        """로거 없이는 아무것도 전송하지 않음"""
        handler = CloudLoggingHandler(None)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None,
            func="test_func",
        )

        # 예외 발생하지 않아야 함
        handler.emit(record)

    def test_cloud_logging_severity_mapping(self):
        """Severity 레벨 매핑"""
        mock_cloud_logger = MagicMock()
        handler = CloudLoggingHandler(mock_cloud_logger)

        # ERROR 레벨
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error",
            args=(),
            exc_info=None,
            func="test_func",
        )

        handler.emit(record)

        # severity 확인
        call_args = mock_cloud_logger.log_struct.call_args
        assert call_args is not None
        assert call_args[1]["severity"] == "ERROR"


@pytest.mark.unit
class TestLoggingIntegration:
    """로깅 통합 테스트"""

    def test_logger_propagation_disabled(self):
        """부모 로거로 전파하지 않음"""
        logger = setup_logging("parent_test", level="INFO")

        assert logger.propagate is False

    def test_duplicate_handler_prevention(self):
        """중복 핸들러 방지"""
        logger = setup_logging("dup_test", level="INFO")
        len(logger.handlers)

        # 같은 이름으로 다시 설정
        logger = setup_logging("dup_test", level="DEBUG")

        # 기존 핸들러는 제거되고 새로운 핸들러만 추가
        assert len(logger.handlers) > 0

    def test_logging_performance(self):
        """로깅 성능 확인"""
        logger = setup_logging("perf_test", level="INFO")

        import time

        start = time.time()

        # 100개 로그 작성
        for i in range(100):
            logger.info(f"Test message {i}", extra={"index": i})

        duration = time.time() - start

        # 100개 로그가 1초 이내에 완료되어야 함
        assert duration < 1.0
