#!/bin/bash

# =============================================================================
# Terraform 초기화 스크립트
# =============================================================================
# 사용법: ./init.sh [environment]
# 예제: ./init.sh production
# =============================================================================

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================================================"
echo "Terraform 초기화 - Agent System"
echo "========================================================================"
echo "환경: $ENVIRONMENT"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# 사전 검사
# =============================================================================

log_info "사전 요구사항 확인 중..."

# Terraform 설치 확인
if ! command -v terraform &> /dev/null; then
    log_error "Terraform이 설치되어 있지 않습니다."
    exit 1
fi
log_success "Terraform 설치됨: $(terraform --version | head -1)"

# AWS CLI 설치 확인
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI가 설치되어 있지 않습니다."
    exit 1
fi
log_success "AWS CLI 설치됨"

# AWS 인증 확인
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS 인증 실패. 자격 증명을 확인하세요."
    exit 1
fi
log_success "AWS 인증 완료"

# 환경 파일 확인
ENV_FILE="$SCRIPT_DIR/environments/${ENVIRONMENT}.tfvars"
if [ ! -f "$ENV_FILE" ]; then
    log_error "환경 파일을 찾을 수 없습니다: $ENV_FILE"
    exit 1
fi
log_success "환경 파일 발견: $ENV_FILE"

# =============================================================================
# Terraform 초기화
# =============================================================================

log_info "Terraform 백엔드 초기화 중..."

# S3 버킷 생성 (상태 파일용)
BUCKET_NAME="agent-system-terraform-state"
REGION="ap-northeast-1"

if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q "NoSuchBucket"; then
    log_info "S3 버킷 생성 중: $BUCKET_NAME"
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION" 2>/dev/null || true

    # 버킷 버전 관리 활성화
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled

    # 서버 측 암호화 활성화
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'

    log_success "S3 버킷 생성 완료"
else
    log_success "S3 버킷 이미 존재함"
fi

# DynamoDB 테이블 생성 (상태 잠금용)
TABLE_NAME="terraform-state-lock"

if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" 2>/dev/null; then
    log_info "DynamoDB 테이블 생성 중: $TABLE_NAME"
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region "$REGION" \
        --sse-specification Enabled=true

    log_success "DynamoDB 테이블 생성 완료"
else
    log_success "DynamoDB 테이블 이미 존재함"
fi

# =============================================================================
# Terraform 초기화
# =============================================================================

cd "$SCRIPT_DIR"

log_info "Terraform 초기화 중..."
terraform init \
    -backend-config="bucket=$BUCKET_NAME" \
    -backend-config="key=production/terraform.tfstate" \
    -backend-config="region=$REGION" \
    -backend-config="dynamodb_table=$TABLE_NAME" \
    -backend-config="encrypt=true"

log_success "Terraform 초기화 완료"

# =============================================================================
# 워크스페이스 설정
# =============================================================================

log_info "Terraform 워크스페이스 설정 중..."

# 워크스페이스 생성
terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"
log_success "워크스페이스 설정 완료: $ENVIRONMENT"

# =============================================================================
# 계획 생성
# =============================================================================

log_info "Terraform 계획 생성 중..."
terraform plan \
    -var-file="environments/${ENVIRONMENT}.tfvars" \
    -out="tfplan" \
    -no-color > tfplan.log 2>&1

# 계획 요약 표시
echo ""
log_info "계획 요약:"
echo "========================================================================"
grep -E "Plan:|will be|No changes" tfplan.log || true
echo "========================================================================"

log_success "Terraform 초기화 완료!"

echo ""
echo "다음 단계:"
echo "1. 계획 검토: cat tfplan.log"
echo "2. 배포 실행: terraform apply tfplan"
echo "3. 또는 리뷰 후 적용: terraform apply -var-file=\"environments/${ENVIRONMENT}.tfvars\""
