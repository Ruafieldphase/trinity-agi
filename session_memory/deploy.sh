#!/bin/bash

# =============================================================================
# Agent System 자동 배포 스크립트
# =============================================================================
# 사용법: ./deploy.sh [환경] [액션]
# 예제:
#   ./deploy.sh dev up           # 개발 환경 시작
#   ./deploy.sh prod deploy      # 프로덕션 배포
#   ./deploy.sh staging logs     # 스테이징 로그 확인
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
ENVIRONMENT=${1:-dev}
ACTION=${2:-up}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Agent System 자동 배포 시스템${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "환경: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "액션: ${GREEN}${ACTION}${NC}"

# =============================================================================
# 함수 정의
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 환경별 설정 로드
load_environment() {
    case "$ENVIRONMENT" in
        dev)
            export DOCKER_COMPOSE_FILE="docker-compose.yml"
            export ENVIRONMENT_TYPE="development"
            export DATABASE_URL="postgresql://agent_user:agent_password_123@localhost:5432/agent_system"
            export CACHE_REDIS_URL="redis://:redis_password_123@localhost:6379"
            export FLASK_ENV="development"
            export LOG_LEVEL="DEBUG"
            ;;
        staging)
            export DOCKER_COMPOSE_FILE="docker-compose.staging.yml"
            export ENVIRONMENT_TYPE="staging"
            export DATABASE_URL="postgresql://${STAGING_DB_USER}:${STAGING_DB_PASS}@${STAGING_DB_HOST}:5432/agent_system"
            export CACHE_REDIS_URL="redis://:${STAGING_REDIS_PASS}@${STAGING_REDIS_HOST}:6379"
            export FLASK_ENV="staging"
            export LOG_LEVEL="INFO"
            ;;
        prod)
            export DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
            export ENVIRONMENT_TYPE="production"
            export DATABASE_URL="${PROD_DATABASE_URL}"
            export CACHE_REDIS_URL="${PROD_CACHE_REDIS_URL}"
            export FLASK_ENV="production"
            export LOG_LEVEL="WARNING"
            ;;
        *)
            log_error "알 수 없는 환경: $ENVIRONMENT"
            echo "사용 가능한 환경: dev, staging, prod"
            exit 1
            ;;
    esac

    log_success "환경 로드 완료: $ENVIRONMENT_TYPE"
}

# Docker 설정 확인
check_docker() {
    log_info "Docker 설치 확인 중..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되어 있지 않습니다."
        exit 1
    fi
    log_success "Docker 설치됨"

    log_info "Docker Compose 설치 확인 중..."
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되어 있지 않습니다."
        exit 1
    fi
    log_success "Docker Compose 설치됨"
}

# Kubernetes 설정 확인
check_kubernetes() {
    log_info "Kubernetes 설치 확인 중..."
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl이 설치되어 있지 않습니다."
        exit 1
    fi
    log_success "kubectl 설치됨"

    log_info "Kubernetes 클러스터 접속 확인 중..."
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes 클러스터에 접속할 수 없습니다."
        exit 1
    fi
    log_success "Kubernetes 클러스터 접속됨"
}

# 사전 요구사항 확인
pre_check() {
    log_info "사전 요구사항 확인 중..."

    # 환경 파일 확인
    if [ "$ENVIRONMENT" != "dev" ] && [ ! -f ".env.$ENVIRONMENT" ]; then
        log_warning "환경 파일이 없습니다: .env.$ENVIRONMENT"
    fi

    # Dockerfile 확인
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile을 찾을 수 없습니다."
        exit 1
    fi

    # 필수 파일 확인
    local required_files=("requirements.txt" "config_manager.py" "health_check_system.py")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "필수 파일을 찾을 수 없습니다: $file"
            exit 1
        fi
    done

    log_success "사전 요구사항 확인 완료"
}

# 테스트 실행
run_tests() {
    log_info "테스트 실행 중..."

    if ! python -m pytest test_*.py -v --tb=short; then
        log_error "테스트 실패"
        exit 1
    fi

    log_success "모든 테스트 통과"
}

# 데이터베이스 마이그레이션
migrate_database() {
    log_info "데이터베이스 마이그레이션 중..."

    case "$ENVIRONMENT" in
        dev)
            docker-compose -f "$DOCKER_COMPOSE_FILE" exec agent-api python database_migration.py --migrate-up
            ;;
        staging|prod)
            kubectl exec -n agent-system deployment/agent-system-api -- python database_migration.py --migrate-up
            ;;
    esac

    log_success "데이터베이스 마이그레이션 완료"
}

# 배포 실행
deploy() {
    log_info "${ENVIRONMENT} 환경 배포 시작..."

    case "$ENVIRONMENT" in
        dev)
            log_info "Docker Compose로 개발 환경 시작..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
            log_success "개발 환경 시작됨"
            echo ""
            log_info "서비스 상태:"
            docker-compose -f "$DOCKER_COMPOSE_FILE" ps
            ;;
        staging)
            log_info "스테이징 환경에 배포 중..."
            check_kubernetes
            log_info "Kubernetes 배포 중..."
            kubectl apply -f k8s/deployment.yaml --namespace agent-system
            log_success "스테이징 환경에 배포됨"
            ;;
        prod)
            log_info "프로덕션 환경에 배포하시겠습니까? (y/n)"
            read -r confirm
            if [[ "$confirm" != "y" ]]; then
                log_error "배포 취소됨"
                exit 1
            fi

            log_info "프로덕션 환경에 배포 중..."
            check_kubernetes
            log_info "Kubernetes 배포 중..."
            kubectl apply -f k8s/deployment.yaml --namespace agent-system
            log_success "프로덕션 환경에 배포됨"
            ;;
    esac
}

# 건강 상태 확인
health_check() {
    log_info "헬스 체크 시작..."

    case "$ENVIRONMENT" in
        dev)
            sleep 5
            if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
                log_success "API 서버 정상 작동"
            else
                log_error "API 서버가 응답하지 않습니다"
                exit 1
            fi
            ;;
        staging|prod)
            log_info "Kubernetes 헬스 체크..."
            kubectl wait --for=condition=ready pod -l app=agent-system,component=api --timeout=300s -n agent-system
            log_success "모든 Pod 정상 작동"
            ;;
    esac
}

# 로그 확인
show_logs() {
    log_info "로그 조회 중..."

    case "$ENVIRONMENT" in
        dev)
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f --tail=50
            ;;
        staging|prod)
            kubectl logs -f deployment/agent-system-api -n agent-system --tail=50
            ;;
    esac
}

# 중지
stop_services() {
    log_info "서비스 중지 중..."

    case "$ENVIRONMENT" in
        dev)
            docker-compose -f "$DOCKER_COMPOSE_FILE" down
            log_success "서비스 중지됨"
            ;;
        staging|prod)
            log_error "프로덕션/스테이징 중지는 지원되지 않습니다."
            exit 1
            ;;
    esac
}

# 클린업
cleanup() {
    log_info "클린업 중..."

    case "$ENVIRONMENT" in
        dev)
            docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
            log_success "클린업 완료"
            ;;
        *)
            log_warning "클린업은 개발 환경에서만 지원됩니다."
            ;;
    esac
}

# 메인 실행 로직
main() {
    load_environment
    pre_check

    case "$ACTION" in
        up)
            check_docker
            run_tests
            deploy
            migrate_database
            health_check
            log_success "배포 완료!"
            ;;
        deploy)
            check_docker
            run_tests
            deploy
            migrate_database
            health_check
            log_success "배포 완료!"
            ;;
        logs)
            show_logs
            ;;
        stop)
            stop_services
            ;;
        clean)
            cleanup
            ;;
        health)
            health_check
            ;;
        *)
            log_error "알 수 없는 액션: $ACTION"
            echo "사용 가능한 액션:"
            echo "  up       - 배포 시작"
            echo "  deploy   - 배포"
            echo "  logs     - 로그 조회"
            echo "  stop     - 서비스 중지"
            echo "  clean    - 전체 클린업"
            echo "  health   - 헬스 체크"
            exit 1
            ;;
    esac
}

# 실행
main
