# ============================================================================
# Stage 1: Builder - 의존성 설치 및 빌드
# ============================================================================
FROM python:3.11-slim as builder

# 작업 디렉토리 설정
WORKDIR /build

# 시스템 의존성 설치 (빌드 도구)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements-api.txt .

# 의존성 설치 (--user로 /root/.local에 설치)
RUN pip install --user --no-cache-dir -r requirements-api.txt

# ============================================================================
# Stage 2: Runtime - 최종 실행 이미지
# ============================================================================
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="Ion Mentoring <ion@naeda.ai>"
LABEL version="1.0.0"
LABEL description="내다AI Ion Multi-Persona Chat API"

# 비root 사용자 생성 (보안)
RUN useradd -m -u 1000 ion && \
    mkdir -p /app /app/logs && \
    chown -R ion:ion /app

# 작업 디렉토리
WORKDIR /app

# Stage 1에서 설치된 Python 패키지 복사
COPY --from=builder /root/.local /home/ion/.local

# 애플리케이션 코드 복사
COPY --chown=ion:ion ./app ./app
COPY --chown=ion:ion ./persona_system ./persona_system
COPY --chown=ion:ion ./persona_pipeline.py .
COPY --chown=ion:ion ./persona_router.py .
COPY --chown=ion:ion ./resonance_converter.py .
COPY --chown=ion:ion ./ion_first_vertex_ai.py .
COPY --chown=ion:ion ./prompt_client.py .

# AGI Integration Components (Phase 4)
COPY --chown=ion:ion ./multi_persona_orchestrator.py .
COPY --chown=ion:ion ./persona_phase_registry.py .
COPY --chown=ion:ion ./rune_integration.py .
COPY --chown=ion:ion ./phase_injection.py .
COPY --chown=ion:ion ./tool_integration.py .


# 환경 변수 설정
ENV PATH=/home/ion/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# 비root 사용자로 전환
USER ion

# 헬스체크 (Cloud Run 호환 - 동적 PORT 사용)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8080\")}/health')" || exit 1

# 포트 노출 (Cloud Run은 동적으로 PORT 환경변수 설정)
EXPOSE 8080

# 애플리케이션 실행 - Cloud Run의 PORT 환경변수 사용
CMD sh -c "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
