#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 시스템 - 환경별 설정 관리

이 모듈은 개발, 테스트, 운영 환경별 설정을 관리합니다.
"""

import sys
import io
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 환경 정의
# ============================================================================

class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


# ============================================================================
# 설정 클래스
# ============================================================================

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    host: str = "localhost"
    port: int = 5432
    username: str = "agent_user"
    password: str = "password"
    database: str = "agent_db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    def get_connection_string(self) -> str:
        """연결 문자열 생성"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ServerConfig:
    """서버 설정"""
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    workers: int = 4
    timeout: int = 30
    max_connections: int = 100


@dataclass
class LoggingConfig:
    """로깅 설정"""
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_dir: str = "./logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True


@dataclass
class CacheConfig:
    """캐시 설정"""
    enabled: bool = True
    backend: str = "memory"  # memory, redis
    default_ttl: int = 3600  # 1시간
    max_size: int = 1000
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


@dataclass
class SecurityConfig:
    """보안 설정"""
    secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    enable_cors: bool = False
    cors_origins: list = None
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 100

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    enable_metrics: bool = True
    enable_health_check: bool = True
    health_check_interval: int = 30
    metrics_port: int = 8000
    enable_tracing: bool = True
    trace_sample_rate: float = 0.1


# ============================================================================
# 통합 설정
# ============================================================================

@dataclass
class AppConfig:
    """애플리케이션 전체 설정"""
    environment: Environment
    app_name: str = "Agent Orchestration System"
    version: str = "1.0.0"
    debug: bool = False

    # 하위 설정들
    server: ServerConfig = None
    database: DatabaseConfig = None
    logging: LoggingConfig = None
    cache: CacheConfig = None
    security: SecurityConfig = None
    monitoring: MonitoringConfig = None

    def __post_init__(self):
        if self.server is None:
            self.server = ServerConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "environment": self.environment.value,
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "server": self._asdict_convert(self.server),
            "database": self._asdict_convert(self.database),
            "logging": self._asdict_convert(self.logging),
            "cache": self._asdict_convert(self.cache),
            "security": self._asdict_convert(self.security),
            "monitoring": self._asdict_convert(self.monitoring),
        }

    @staticmethod
    def _asdict_convert(obj) -> Dict[str, Any]:
        """dataclass를 딕셔너리로 변환"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field in obj.__dataclass_fields__:
                value = getattr(obj, field)
                if isinstance(value, Enum):
                    result[field] = value.value
                elif isinstance(value, (str, int, float, bool)) or value is None:
                    result[field] = value
                else:
                    result[field] = str(value)
            return result
        return {}


# ============================================================================
# 설정 매니저
# ============================================================================

class ConfigManager:
    """설정 관리자"""

    _instance = None
    _config: Optional[AppConfig] = None

    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def load_config(self, environment: Optional[str] = None) -> AppConfig:
        """설정 로드"""
        env = environment or os.getenv("ENVIRONMENT", "development")

        if env == "production":
            self._config = self._create_production_config()
        elif env == "staging":
            self._config = self._create_staging_config()
        elif env == "testing":
            self._config = self._create_testing_config()
        else:
            self._config = self._create_development_config()

        # 환경 변수로 오버라이드
        self._apply_env_overrides()

        return self._config

    def get_config(self) -> AppConfig:
        """설정 조회"""
        if self._config is None:
            self.load_config()
        return self._config

    def _create_development_config(self) -> AppConfig:
        """개발 환경 설정"""
        return AppConfig(
            environment=Environment.DEVELOPMENT,
            debug=True,
            server=ServerConfig(host="127.0.0.1", port=5000, debug=True, workers=1),
            database=DatabaseConfig(
                host="localhost",
                port=5432,
                database="agent_db_dev"
            ),
            logging=LoggingConfig(log_level="DEBUG"),
            cache=CacheConfig(enabled=True, backend="memory"),
            security=SecurityConfig(enable_cors=True),
            monitoring=MonitoringConfig(enable_metrics=True, enable_tracing=True)
        )

    def _create_testing_config(self) -> AppConfig:
        """테스트 환경 설정"""
        return AppConfig(
            environment=Environment.TESTING,
            debug=False,
            server=ServerConfig(host="127.0.0.1", port=5001, workers=1),
            database=DatabaseConfig(
                host="localhost",
                port=5432,
                database="agent_db_test"
            ),
            logging=LoggingConfig(log_level="WARNING"),
            cache=CacheConfig(enabled=True, backend="memory", max_size=100),
            security=SecurityConfig(enable_cors=False),
            monitoring=MonitoringConfig(enable_metrics=False)
        )

    def _create_staging_config(self) -> AppConfig:
        """스테이징 환경 설정"""
        return AppConfig(
            environment=Environment.STAGING,
            debug=False,
            server=ServerConfig(host="0.0.0.0", port=5000, workers=2),
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database="agent_db_staging"
            ),
            logging=LoggingConfig(log_level="INFO"),
            cache=CacheConfig(enabled=True, backend="redis"),
            security=SecurityConfig(enable_cors=False),
            monitoring=MonitoringConfig(enable_metrics=True)
        )

    def _create_production_config(self) -> AppConfig:
        """운영 환경 설정"""
        return AppConfig(
            environment=Environment.PRODUCTION,
            debug=False,
            server=ServerConfig(
                host="0.0.0.0",
                port=5000,
                workers=4,
                max_connections=100
            ),
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                username=os.getenv("DB_USER", "agent_user"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "agent_db")
            ),
            logging=LoggingConfig(log_level="INFO", enable_file=True),
            cache=CacheConfig(
                enabled=True,
                backend="redis",
                redis_host=os.getenv("REDIS_HOST", "localhost")
            ),
            security=SecurityConfig(
                secret_key=os.getenv("SECRET_KEY", ""),
                enable_rate_limiting=True
            ),
            monitoring=MonitoringConfig(
                enable_metrics=True,
                enable_health_check=True,
                enable_tracing=True
            )
        )

    def _apply_env_overrides(self):
        """환경 변수로 설정 오버라이드"""
        if not self._config:
            return

        # 서버 설정
        if os.getenv("SERVER_HOST"):
            self._config.server.host = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            self._config.server.port = int(os.getenv("SERVER_PORT"))

        # 로깅 설정
        if os.getenv("LOG_LEVEL"):
            self._config.logging.log_level = os.getenv("LOG_LEVEL")

        # 캐시 설정
        if os.getenv("CACHE_BACKEND"):
            self._config.cache.backend = os.getenv("CACHE_BACKEND")

    def print_config(self):
        """설정 출력"""
        if not self._config:
            self.load_config()

        print("\n" + "=" * 80)
        print(f"설정: {self._config.environment.value.upper()}")
        print("=" * 80)

        config_dict = self._config.to_dict()
        print(json.dumps(config_dict, indent=2, ensure_ascii=False))


# ============================================================================
# 데모
# ============================================================================

def demo_config_manager():
    """설정 관리 데모"""
    print("=" * 80)
    print("설정 관리 시스템 데모")
    print("=" * 80)

    # 개발 환경
    print("\n[1단계] 개발 환경 설정")
    print("-" * 80)

    manager = ConfigManager()
    dev_config = manager.load_config("development")
    print(f"환경: {dev_config.environment.value}")
    print(f"디버그: {dev_config.debug}")
    print(f"서버: {dev_config.server.host}:{dev_config.server.port}")
    print(f"데이터베이스: {dev_config.database.host}:{dev_config.database.port}")
    print(f"로그 레벨: {dev_config.logging.log_level}")

    # 운영 환경
    print("\n[2단계] 운영 환경 설정")
    print("-" * 80)

    prod_config = manager.load_config("production")
    print(f"환경: {prod_config.environment.value}")
    print(f"디버그: {prod_config.debug}")
    print(f"서버: {prod_config.server.host}:{prod_config.server.port}")
    print(f"워커: {prod_config.server.workers}")
    print(f"로그 레벨: {prod_config.logging.log_level}")
    print(f"캐시 백엔드: {prod_config.cache.backend}")

    # 전체 설정 출력
    print("\n[3단계] 전체 설정 조회")
    print("-" * 80)

    manager.print_config()

    print("\n" + "=" * 80)
    print("설정 관리 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_config_manager()
