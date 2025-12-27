#!/usr/bin/env python3
"""
환경변수 설정 검증 스크립트

Vertex AI, Redis, 모니터링 등 주요 환경변수가 올바르게 설정되었는지 검증합니다.
배포 전 또는 새 환경 설정 후 실행하여 설정 상태를 확인하세요.

사용법:
    python scripts/check_env_config.py
    python scripts/check_env_config.py --verbose
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ANSI 색상 코드
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class EnvChecker:
    """환경변수 검증 클래스"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def check_vertex_ai_config(self) -> Dict[str, bool]:
        """Vertex AI 설정 검증"""
        print(f"\n{BOLD}{BLUE}🔍 Vertex AI Configuration{RESET}")
        print("=" * 60)

        config = {}

        # 프로젝트 ID 체크 (여러 별칭 지원)
        project_vars = ["GCP_PROJECT", "GOOGLE_CLOUD_PROJECT", "VERTEX_PROJECT_ID"]
        project = None
        project_source = None
        for var in project_vars:
            val = os.getenv(var)
            if val:
                project = val
                project_source = var
                break

        if project:
            print(f"{GREEN}✓{RESET} Project ID: {project} (from {project_source})")
            config["project"] = True
        else:
            print(f"{RED}✗{RESET} Project ID: Not set")
            self.issues.append(
                f"Set one of: {', '.join(project_vars)}"
            )
            config["project"] = False

        # 지역 체크
        location_vars = ["GCP_LOCATION", "GOOGLE_CLOUD_REGION", "VERTEX_LOCATION"]
        location = None
        location_source = None
        for var in location_vars:
            val = os.getenv(var)
            if val:
                location = val
                location_source = var
                break

        if location:
            print(f"{GREEN}✓{RESET} Location: {location} (from {location_source})")
            config["location"] = True
        else:
            print(f"{YELLOW}⚠{RESET} Location: Not set (will use default: us-central1)")
            self.warnings.append(
                f"Consider setting one of: {', '.join(location_vars)}"
            )
            config["location"] = False

        # 모델 체크
        model_vars = ["VERTEX_MODEL_GEMINI", "GEMINI_MODEL", "VERTEX_MODEL"]
        model = None
        model_source = None
        for var in model_vars:
            val = os.getenv(var)
            if val:
                model = val
                model_source = var
                break

        if model:
            print(f"{GREEN}✓{RESET} Model: {model} (from {model_source})")
            config["model"] = True
        else:
            print(
                f"{YELLOW}⚠{RESET} Model: Not set (will use default: gemini-2.5-flash)"
            )
            self.warnings.append(f"Consider setting one of: {', '.join(model_vars)}")
            config["model"] = False

        # API 키 체크
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print(f"{GREEN}✓{RESET} API Key: {masked} (from GOOGLE_API_KEY)")
            config["api_key"] = True
        else:
            print(
                f"{YELLOW}⚠{RESET} API Key: Not set (will use Application Default Credentials)"
            )
            self.info.append(
                "Using ADC is fine for GCP environments. Set GOOGLE_API_KEY for local dev."
            )
            config["api_key"] = False

        # 임베딩 모델 체크
        embeddings_model = os.getenv("EMBEDDINGS_MODEL")
        if embeddings_model:
            print(f"{GREEN}✓{RESET} Embeddings Model: {embeddings_model}")
            config["embeddings"] = True
        else:
            print(
                f"{YELLOW}⚠{RESET} Embeddings Model: Not set (will use default: text-embedding-004)"
            )
            config["embeddings"] = False

        return config

    def check_redis_config(self) -> Dict[str, bool]:
        """Redis 설정 검증"""
        print(f"\n{BOLD}{BLUE}🔍 Redis Configuration{RESET}")
        print("=" * 60)

        config = {}

        # Redis 활성화 플래그
        enabled = os.getenv("REDIS_ENABLED", "").lower() in ("true", "1", "yes")
        if enabled:
            print(f"{GREEN}✓{RESET} Redis: Enabled")
            config["enabled"] = True

            # 호스트
            host = os.getenv("REDIS_HOST", "localhost")
            print(f"  Host: {host}")

            # 포트
            port = os.getenv("REDIS_PORT", "6379")
            print(f"  Port: {port}")

            # DB
            db = os.getenv("REDIS_DB", "0")
            print(f"  DB: {db}")

            # 비밀번호
            password = os.getenv("REDIS_PASSWORD")
            if password:
                print(f"  Password: {'*' * 8} (set)")
            else:
                print(f"{YELLOW}⚠{RESET}  Password: Not set (OK if Redis has no auth)")

            config["configured"] = True
        else:
            print(f"{YELLOW}⚠{RESET} Redis: Disabled (REDIS_ENABLED not set or false)")
            self.info.append(
                "Redis caching disabled. Set REDIS_ENABLED=true to enable."
            )
            config["enabled"] = False
            config["configured"] = False

        return config

    def check_remote_vector_config(self) -> Dict[str, bool]:
        """Remote vector store 설정 검증"""
        print(f"\n{BOLD}{BLUE}🔍 Remote Vector Store Configuration{RESET}")
        print("=" * 60)

        config: Dict[str, bool] = {}
        provider = os.getenv("AGI_REMOTE_VECTOR_PROVIDER", "").strip().lower()
        if not provider:
            print(f"{YELLOW}⚠{RESET} Remote Vector Store: Disabled (AGI_REMOTE_VECTOR_PROVIDER not set)")
            self.info.append("Remote vector store disabled. Set AGI_REMOTE_VECTOR_PROVIDER to enable.")
            config["enabled"] = False
            return config

        config["enabled"] = True
        print(f"{GREEN}✓{RESET} Provider: {provider}")

        if provider != "qdrant":
            print(f"{RED}✗{RESET} Provider: Unsupported ({provider})")
            self.issues.append(f"Unsupported AGI_REMOTE_VECTOR_PROVIDER: {provider}")
            return config

        url = os.getenv("AGI_REMOTE_VECTOR_URL") or os.getenv("QDRANT_URL")
        if url:
            print(f"{GREEN}✓{RESET} URL: {url}")
            config["url"] = True
        else:
            print(f"{RED}✗{RESET} URL: Not set")
            self.issues.append("Set AGI_REMOTE_VECTOR_URL or QDRANT_URL for remote vector store")
            config["url"] = False

        api_key = os.getenv("AGI_REMOTE_VECTOR_API_KEY") or os.getenv("QDRANT_API_KEY")
        if api_key:
            masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
            print(f"{GREEN}✓{RESET} API Key: {masked}")
            config["api_key"] = True
        else:
            print(f"{YELLOW}⚠{RESET} API Key: Not set (OK if server is open)")
            config["api_key"] = False

        collection = os.getenv("AGI_REMOTE_VECTOR_COLLECTION") or "agi_memory"
        print(f"{GREEN}✓{RESET} Collection: {collection}")
        config["collection"] = True

        read_enabled = os.getenv("AGI_REMOTE_VECTOR_READ", "1").strip().lower() in ("1", "true", "yes", "on")
        write_enabled = os.getenv("AGI_REMOTE_VECTOR_WRITE", "1").strip().lower() in ("1", "true", "yes", "on")
        print(f"{GREEN}✓{RESET} Read Enabled: {read_enabled}")
        print(f"{GREEN}✓{RESET} Write Enabled: {write_enabled}")

        return config

    def check_monitoring_config(self) -> Dict[str, bool]:
        """모니터링 설정 검증"""
        print(f"\n{BOLD}{BLUE}🔍 Monitoring Configuration{RESET}")
        print("=" * 60)

        config = {}

        # Evidence Gate 강제 모드
        force_evidence = os.getenv("EVIDENCE_GATE_FORCE", "").lower() in (
            "true",
            "1",
            "yes",
        )
        if force_evidence:
            print(f"{GREEN}✓{RESET} Evidence Gate Force: Enabled")
            config["force_evidence"] = True
        else:
            print(f"{YELLOW}⚠{RESET} Evidence Gate Force: Disabled")
            config["force_evidence"] = False

        # AGI 레저 경로
        agi_ledger = os.getenv("AGI_LEDGER_PATH")
        if agi_ledger:
            if Path(agi_ledger).exists():
                print(f"{GREEN}✓{RESET} AGI Ledger Path: {agi_ledger} (exists)")
                config["agi_ledger"] = True
            else:
                print(f"{RED}✗{RESET} AGI Ledger Path: {agi_ledger} (not found)")
                self.issues.append(f"AGI ledger path does not exist: {agi_ledger}")
                config["agi_ledger"] = False
        else:
            print(
                f"{YELLOW}⚠{RESET} AGI Ledger Path: Not set (will use default paths)"
            )
            config["agi_ledger"] = False

        # Evidence 레저 경로
        evidence_ledger = os.getenv("EVIDENCE_LEDGER_PATH")
        if evidence_ledger:
            if Path(evidence_ledger).exists():
                print(f"{GREEN}✓{RESET} Evidence Ledger Path: {evidence_ledger} (exists)")
                config["evidence_ledger"] = True
            else:
                print(
                    f"{RED}✗{RESET} Evidence Ledger Path: {evidence_ledger} (not found)"
                )
                self.issues.append(
                    f"Evidence ledger path does not exist: {evidence_ledger}"
                )
                config["evidence_ledger"] = False
        else:
            print(
                f"{YELLOW}⚠{RESET} Evidence Ledger Path: Not set (will use default paths)"
            )
            config["evidence_ledger"] = False

        return config

    def check_env_file(self) -> bool:
        """루트 .env 파일 존재 확인"""
        print(f"\n{BOLD}{BLUE}🔍 Environment File{RESET}")
        print("=" * 60)

        env_file = Path(".env")
        example_file = Path(".env.example")

        if env_file.exists():
            print(f"{GREEN}✓{RESET} .env file: Found")
            return True
        else:
            print(f"{YELLOW}⚠{RESET} .env file: Not found")
            if example_file.exists():
                self.warnings.append(
                    "Copy .env.example to .env and configure your settings"
                )
            else:
                self.warnings.append("Create a .env file for local configuration")
            return False

    def print_summary(self):
        """검증 결과 요약 출력"""
        print(f"\n{BOLD}{BLUE}📊 Summary{RESET}")
        print("=" * 60)

        if self.issues:
            print(f"\n{RED}❌ Critical Issues ({len(self.issues)}):{RESET}")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n{YELLOW}⚠️  Warnings ({len(self.warnings)}):{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.info and self.verbose:
            print(f"\n{BLUE}ℹ️  Information:{RESET}")
            for info in self.info:
                print(f"  • {info}")

        if not self.issues and not self.warnings:
            print(f"\n{GREEN}✅ All checks passed! Configuration looks good.{RESET}")
            return 0
        elif self.issues:
            print(
                f"\n{RED}❌ Configuration has critical issues. Please fix them before deployment.{RESET}"
            )
            return 1
        else:
            print(
                f"\n{YELLOW}⚠️  Configuration has warnings but should work. Consider addressing them.{RESET}"
            )
            return 0


def main():
    """메인 함수"""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print(f"{BOLD}{BLUE}🔧 Environment Configuration Checker{RESET}")
    print(f"{BLUE}Validates Vertex AI, Redis, and Monitoring settings{RESET}\n")

    checker = EnvChecker(verbose=verbose)

    # 각 영역 검증
    checker.check_env_file()
    vertex_config = checker.check_vertex_ai_config()
    redis_config = checker.check_redis_config()
    remote_config = checker.check_remote_vector_config()
    monitoring_config = checker.check_monitoring_config()

    # 요약 출력
    checker.print_summary()

    # 종료 코드 반환
    sys.exit(len(checker.issues))


if __name__ == "__main__":
    main()
