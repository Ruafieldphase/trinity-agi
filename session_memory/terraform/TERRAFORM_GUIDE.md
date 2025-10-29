# Terraform 배포 가이드 - Agent System

## 개요

Terraform을 사용하여 AWS에 Agent System을 완전자동으로 배포합니다.

**지원 환경:**
- Development
- Staging
- Production

---

## 사전 요구사항

### 필수 도구 설치

```bash
# Terraform 설치
brew install terraform        # macOS
choco install terraform       # Windows
apt-get install terraform     # Linux

# AWS CLI 설치
brew install awscli          # macOS
pip install awscliv2         # 또는 pip

# kubectl 설치 (선택사항)
brew install kubectl         # macOS

# 버전 확인
terraform --version
aws --version
```

### AWS 계정 설정

```bash
# AWS 자격 증명 설정
aws configure

# 또는 환경 변수
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 인증 확인
aws sts get-caller-identity
```

---

## 초기 설정

### 1단계: Terraform 초기화

```bash
cd terraform

# 초기화 스크립트 실행 (권장)
chmod +x init.sh
./init.sh production

# 또는 수동으로
terraform init

# 워크스페이스 생성
terraform workspace new production
terraform workspace select production
```

### 2단계: 변수 파일 준비

**production.tfvars:**
```hcl
environment = "production"
aws_region  = "ap-northeast-1"

# 필수: 데이터베이스 비밀번호 (강력한 비밀번호)
database_password = "Your_Secure_Password_123!"

# 필수: Redis 인증 토큰
redis_auth_token = "Your_Redis_Token_1234567890123456"
```

---

## 배포 프로세스

### 계획 확인

```bash
# 계획 생성 (무엇이 생성될지 확인)
terraform plan -var-file="environments/production.tfvars" -out=tfplan

# 계획 상세 보기
terraform show tfplan

# 계획을 파일로 저장
terraform show -json tfplan > plan.json
```

### 배포 실행

```bash
# 계획 적용
terraform apply tfplan

# 또는 직접 적용 (승인 필요)
terraform apply -var-file="environments/production.tfvars"

# 배포 진행 시간: 약 15-30분
```

### 배포 완료 확인

```bash
# 배포된 리소스 확인
terraform show

# 주요 정보 출력
terraform output

# 특정 정보 조회
terraform output eks_cluster_endpoint
terraform output rds_endpoint
terraform output redis_endpoint
```

---

## 모듈 구조

### VPC 모듈 (`modules/vpc/`)

**생성되는 리소스:**
- VPC (Virtual Private Cloud)
- 공개 서브넷 (3개, 각각 다른 AZ)
- 프라이빗 서브넷 (3개)
- 인터넷 게이트웨이
- NAT 게이트웨이
- 라우팅 테이블
- VPC Flow Logs

**사용:**
```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr = "10.0.0.0/16"
  # ... 추가 설정
}
```

### EKS 모듈 (`modules/eks/`)

**생성되는 리소스:**
- EKS 클러스터
- 노드 그룹
- IAM 역할 및 정책
- CloudWatch 로깅
- 보안 그룹

**사용:**
```hcl
module "eks" {
  source = "./modules/eks"

  cluster_name = "agent-system-prod-cluster"
  cluster_version = "1.28"
  # ... 추가 설정
}
```

### RDS 모듈 (`modules/rds/`)

**생성되는 리소스:**
- PostgreSQL 데이터베이스
- DB 서브넷 그룹
- 백업 설정
- 모니터링

### ElastiCache 모듈 (`modules/elasticache/`)

**생성되는 리소스:**
- Redis 클러스터
- 자동 페일오버
- 암호화 설정

---

## 환경별 배포

### Development

```bash
terraform workspace select development
terraform apply -var-file="environments/development.tfvars"
```

**특징:**
- 최소 리소스
- 자동 스케일링 비활성화
- 백업 비활성화

### Staging

```bash
terraform workspace select staging
terraform apply -var-file="environments/staging.tfvars"
```

**특징:**
- 프로덕션과 동일한 구성
- 백업 활성화 (7일)
- 비용 최적화

### Production

```bash
terraform workspace select production
terraform apply -var-file="environments/production.tfvars"
```

**특징:**
- Multi-AZ 배포
- 자동 페일오버
- 백업 30일
- 고가용성

---

## 주요 명령어

```bash
# 계획
terraform plan -var-file="environments/production.tfvars"

# 적용
terraform apply -var-file="environments/production.tfvars"

# 특정 리소스만 적용
terraform apply -target=module.eks -var-file="environments/production.tfvars"

# 상태 확인
terraform state list
terraform state show module.eks.aws_eks_cluster.main

# 상태 백업
terraform state pull > backup.state

# 리소스 제거
terraform destroy -var-file="environments/production.tfvars"

# 특정 리소스만 제거
terraform destroy -target=module.rds -var-file="environments/production.tfvars"

# 리소스 새로고침
terraform refresh -var-file="environments/production.tfvars"

# 포매팅
terraform fmt .
terraform fmt -recursive .
```

---

## 배포 후 설정

### 1. kubectl 설정

```bash
# kubeconfig 업데이트
aws eks update-kubeconfig \
    --name agent-system-prod-cluster \
    --region ap-northeast-1

# 클러스터 접속 확인
kubectl cluster-info
kubectl get nodes
```

### 2. 애플리케이션 배포

```bash
# Kubernetes 매니페스트 적용
kubectl apply -f k8s/deployment.yaml

# 배포 상태 확인
kubectl get deployments -n agent-system
kubectl get pods -n agent-system
```

### 3. 데이터베이스 초기화

```bash
# DB 마이그레이션
kubectl exec -it deployment/agent-system-api -n agent-system -- \
    python database_migration.py --migrate-up
```

---

## 모니터링 및 관리

### CloudWatch 로그 확인

```bash
# EKS 클러스터 로그
aws logs tail /aws/eks/agent-system-prod-cluster --follow

# 특정 로그 그룹
aws logs describe-log-groups

# 로그 필터
aws logs filter-log-events \
    --log-group-name /aws/eks/agent-system-prod-cluster \
    --filter-pattern "ERROR"
```

### 비용 추적

```bash
# AWS Billing Dashboard 확인
# https://console.aws.amazon.com/billingv2/home

# 또는 CLI
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

---

## 문제 해결

### Terraform 상태 손상

```bash
# 상태 백업
cp terraform.tfstate terraform.tfstate.backup

# 상태 잠금 해제
terraform force-unlock <LOCK_ID>

# 상태 새로고침
terraform refresh
```

### AWS 리소스 문제

```bash
# 리소스 정보 확인
aws eks describe-cluster --name agent-system-prod-cluster --region ap-northeast-1

# RDS 상태 확인
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]'

# Redis 상태 확인
aws elasticache describe-cache-clusters --query 'CacheClusters[*].[CacheClusterId,CacheClusterStatus]'
```

### 배포 재시도

```bash
# 실패한 리소스만 재배포
terraform apply -target=module.eks

# 또는 전체 재배포
terraform destroy
terraform apply
```

---

## 리소스 제거

### 안전한 제거 절차

```bash
# 1단계: 애플리케이션 제거
kubectl delete deployment agent-system-api -n agent-system

# 2단계: PVC 제거 (데이터 삭제)
kubectl delete pvc --all -n agent-system

# 3단계: Terraform으로 인프라 제거
terraform destroy -var-file="environments/production.tfvars"

# 4단계: 상태 파일 정리
rm terraform.tfstate*
```

### S3 및 DynamoDB 정리 (선택사항)

```bash
# S3 버킷 비우기
aws s3 rm s3://agent-system-terraform-state --recursive

# DynamoDB 테이블 삭제
aws dynamodb delete-table --table-name terraform-state-lock
```

---

## 베스트 프랙티스

### 1. 상태 파일 관리

✅ **DO:**
- S3에 상태 파일 저장
- 버전 관리 활성화
- 암호화 활성화
- DynamoDB로 잠금 설정

❌ **DON'T:**
- 로컬에 상태 파일 저장
- 상태 파일을 버전 관리에 커밋
- 상태 파일 공유

### 2. 변수 관리

✅ **DO:**
- 민감한 정보는 `.tfvars` 파일에
- `.tfvars` 파일을 `.gitignore`에 추가
- AWS Secrets Manager 사용

❌ **DON'T:**
- 하드코딩된 시크릿
- 기본값으로 민감 정보 설정
- 버전 관리에 시크릿 커밋

### 3. 워크스페이스 사용

✅ **DO:**
- 각 환경별 워크스페이스 사용
- 환경별 변수 파일 분리
- 명확한 워크스페이스 명칭

❌ **DON'T:**
- 모든 환경을 한 상태로 관리
- 워크스페이스 혼동

### 4. 계획 검토

✅ **DO:**
- 항상 계획을 먼저 검토
- 예상과 다른 변경 확인
- 팀 검토 후 적용

❌ **DON'T:**
- 계획 없이 직접 적용
- 자동 승인 설정

---

## 주요 설정값

### Production 환경 기본값

```hcl
# EKS 클러스터
kubernetes_version = "1.28"
node_group_desired_size = 5
node_group_max_size = 20

# RDS
db_instance_class = "db.t3.small"
db_allocated_storage = 100
multi_az = true
backup_retention_days = 30

# Redis
redis_node_type = "cache.t3.small"
automatic_failover = true

# VPC
vpc_cidr = "10.0.0.0/16"
enable_nat_gateway = true
enable_flow_logs = true
```

---

## 지원 및 피드백

- 문서: [README.md](../README.md)
- 이슈: GitHub Issues
- 질문: GitHub Discussions

---

**마지막 업데이트: 2025-10-19**
**Terraform 버전: >= 1.0**
