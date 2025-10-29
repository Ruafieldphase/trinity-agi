# Docker 이미지 빌드 파일
# AI 에이전트 오케스트레이션 시스템

FROM python:3.9-slim

LABEL maintainer="Sena Agent System"
LABEL version="1.0"
LABEL description="AI Agent Orchestration System - Production Ready"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 파일 복사
COPY requirements.txt .

# 파이썬 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 5000 8000

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV LOG_LEVEL=INFO

# 애플리케이션 실행
CMD ["python", "agent_api_server.py", "--host", "0.0.0.0", "--port", "5000"]
