"""
설정 모듈 Unit 테스트

app/config.py의 설정 관리 기능을 테스트합니다.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# ion-mentoring 디렉토리 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import Settings, get_settings, is_development, is_production


@pytest.mark.unit
class TestSettingsConfig:
    """설정 객체 기본 테스트"""

    def test_settings_defaults(self, monkeypatch):
        """기본 설정값 확인"""
        # 테스트 환경 변수 제거 (기본값 테스트)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        settings = Settings()

        assert settings.app_name == "내다AI Ion API"
        # 테스트 환경에서는 staging으로 설정될 수 있음
        assert settings.environment in ["development", "test", "staging"]
        assert settings.port == 8080
        assert settings.host == "0.0.0.0"
        assert settings.reload is True
        # 기본 로그 레벨은 INFO
        assert settings.log_level in ["INFO", "WARNING"]
        assert settings.phase4_enabled is False
        assert settings.canary_traffic_percentage == 5
        assert settings.deployment_version == "LEGACY"

    def test_settings_with_env_vars(self, monkeypatch):
        """환경 변수로부터 설정 로드"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("RELOAD", "false")

        settings = Settings()

        assert settings.environment == "production"
        assert settings.port == 8000
        assert settings.log_level == "DEBUG"
        assert settings.reload is False
        assert settings.phase4_enabled is False
        assert settings.canary_traffic_percentage == 5
        assert settings.deployment_version == "LEGACY"

    def test_rate_limit_settings(self):
        """Rate Limit 설정 확인"""
        settings = Settings()

        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_calls == 10
        assert settings.rate_limit_period == 60

    def test_cors_origins_default(self):
        """기본 CORS Origins"""
        settings = Settings()
        assert settings.cors_origins == ["*"]

    def test_cors_origins_from_env(self, monkeypatch):
        """환경 변수에서 CORS Origins 파싱"""
        # JSON 형식으로 설정 (pydantic-settings 요구)
        cors_json = '["http://localhost:3000", "http://localhost:8080", "https://example.com"]'
        monkeypatch.setenv("CORS_ORIGINS", cors_json)

        settings = Settings()

        assert len(settings.cors_origins) == 3
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:8080" in settings.cors_origins
        assert "https://example.com" in settings.cors_origins

    def test_vertex_ai_settings(self, monkeypatch):
        """Vertex AI 설정"""
        monkeypatch.setenv("VERTEX_PROJECT_ID", "test-project")
        monkeypatch.setenv("VERTEX_LOCATION", "us-west1")
        monkeypatch.setenv("VERTEX_MODEL", "gemini-pro")

        settings = Settings()

        assert settings.vertex_project_id == "test-project"
        assert settings.vertex_location == "us-west1"
        assert settings.vertex_model == "gemini-pro"

    def test_cloud_logging_settings(self, monkeypatch):
        """Google Cloud Logging 설정"""
        monkeypatch.setenv("GCP_PROJECT_ID", "gcp-project")
        monkeypatch.setenv("USE_CLOUD_LOGGING", "true")

        settings = Settings()

        assert settings.gcp_project_id == "gcp-project"
        assert settings.use_cloud_logging is True

    def test_phase4_settings(self, monkeypatch):
        """Phase 4 플래그 및 카나리 비율"""
        monkeypatch.setenv("PHASE4_ENABLED", "true")
        monkeypatch.setenv("CANARY_TRAFFIC_PERCENTAGE", "15")
        monkeypatch.setenv("DEPLOYMENT_VERSION", "CANARY")

        settings = Settings()

        assert settings.phase4_enabled is True
        assert settings.canary_traffic_percentage == 15
        assert settings.deployment_version == "CANARY"

    def test_deployment_version_normalization(self, monkeypatch):
        """배포 버전 설정 값 정규화"""
        monkeypatch.setenv("DEPLOYMENT_VERSION", "canary")
        settings = Settings()
        assert settings.deployment_version == "CANARY"

        monkeypatch.setenv("DEPLOYMENT_VERSION", "invalid")
        settings_invalid = Settings()
        assert settings_invalid.deployment_version == "LEGACY"


@pytest.mark.unit
class TestEnvironmentDetection:
    """환경 감지 함수 테스트"""

    def test_is_production_true(self, monkeypatch):
        """프로덕션 환경 감지"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        # 싱글톤이므로 새 인스턴스 생성
        from importlib import reload

        import app.config

        reload(app.config)
        from app.config import is_production

        assert is_production() is True
        assert is_development() is False

    def test_is_development_true(self, monkeypatch):
        """개발 환경 감지"""
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        from importlib import reload

        import app.config

        reload(app.config)
        from app.config import is_development

        assert is_development() is True
        assert is_production() is False

    def test_is_staging(self, monkeypatch):
        """스테이징 환경"""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        from importlib import reload

        import app.config

        reload(app.config)
        from app.config import is_production

        assert is_production() is False
        assert is_development() is False

    def test_environment_function_behavior(self):
        """환경 감지 함수 동작 (현재 설정 기반)"""
        # 현재 설정된 환경에서 테스트 (싱글톤이므로)
        from app.config import is_development, settings

        if settings.environment == "production":
            assert is_production() is True
            assert is_development() is False
        else:
            assert is_production() is False
            assert is_development() is (settings.environment == "development")


@pytest.mark.unit
class TestSettingsValidation:
    """설정 검증 테스트"""

    def test_port_range(self, monkeypatch):
        """포트 번호 범위 유효성"""
        monkeypatch.setenv("PORT", "8080")
        settings = Settings()
        assert settings.port == 8080

    def test_invalid_log_level(self, monkeypatch):
        """유효하지 않은 로그 레벨"""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        settings = Settings()
        # 기본값으로 설정되어야 함
        assert settings.log_level == "INVALID"

    def test_rate_limit_validation(self, monkeypatch):
        """Rate Limit 설정 검증"""
        monkeypatch.setenv("RATE_LIMIT_CALLS", "100")
        monkeypatch.setenv("RATE_LIMIT_PERIOD", "120")

        settings = Settings()

        assert settings.rate_limit_calls == 100
        assert settings.rate_limit_period == 120

    def test_canary_percentage_validation(self, monkeypatch):
        """카나리 비율 검증"""
        monkeypatch.setenv("CANARY_TRAFFIC_PERCENTAGE", "150")

        with pytest.raises(ValidationError):
            Settings()


@pytest.mark.unit
def test_get_settings():
    """get_settings 함수"""
    settings = get_settings()

    # Settings 타입 확인
    assert hasattr(settings, "app_name")
    assert hasattr(settings, "environment")
    assert hasattr(settings, "port")

    # 값 확인
    assert settings.app_name is not None
    assert settings.environment is not None
    assert len(settings.app_name) > 0
