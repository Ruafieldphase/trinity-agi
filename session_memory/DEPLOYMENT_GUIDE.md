# Priority 7: 배포 자동화 및 운영 가이드

## 개요

Agent System을 개발, 스테이징, 프로덕션 환경에 자동으로 배포하고 관리하는 완전한 시스템입니다.

**구현 완료도: 100%**

---

## 배포 인프라 구성

### 파일 구조

```
프로젝트/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                # GitHub Actions CI/CD 파이프라인
├── k8s/
│   └── deployment.yaml              # Kubernetes 배포 설정
├── docker-compose.yml               # 개발 환경 (Docker Compose)
├── docker-compose.staging.yml       # 스테이징 환경
├── docker-compose.prod.yml          # 프로덕션 환경
├── Dockerfile                       # 컨테이너 이미지 정의
├── nginx.conf                       # Nginx 리버스 프록시 설정
├── deploy.sh                        # 자동 배포 스크립트
├── prometheus.yml                   # 모니터링 설정
└── requirements.txt                 # Python 의존성
```

---

## 1. 개발 환경 배포

### 전제 조건

```bash
# 필수 도구 설치
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+
```

### 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/yourorg/agent-system.git
cd agent-system

# 권한 설정
chmod +x deploy.sh

# 개발 환경 시작
./deploy.sh dev up

# 서비스 확인
docker-compose ps

# 헬스 체크
curl http://localhost:5000/api/health
```

### 접근 주소

```
API 서버:        http://localhost:5000
메트릭:          http://localhost:8000
Prometheus:      http://localhost:9090
Grafana:         http://localhost:3000
PostgreSQL:      localhost:5432
Redis:           localhost:6379
```

### 기본 인증 정보

```
PostgreSQL:
  사용자: agent_user
  비밀번호: agent_password_123
  데이터베이스: agent_system

Redis:
  비밀번호: redis_password_123

Grafana:
  사용자: admin
  비밀번호: admin_password_123
```

### 개발 환경 명령어

```bash
# 로그 보기
./deploy.sh dev logs

# 서비스 중지
./deploy.sh dev stop

# 전체 클린업
./deploy.sh dev clean

# 헬스 체크
./deploy.sh dev health

# 데이터베이스 마이그레이션
./deploy.sh dev up && docker-compose exec agent-api python database_migration.py --migrate-up
```

---

## 2. CI/CD 파이프라인 (GitHub Actions)

### 파이프라인 단계

#### 1단계: 코드 품질 검사
```yaml
- Black (코드 포매팅)
- Flake8 (린팅)
- 기본 구문 검사
```

#### 2단계: 단위 테스트
```yaml
- Priority 1 테스트 (에이전트 시스템)
- Priority 5 테스트 (데이터 영속성)
- Priority 6 테스트 (보안)
- 커버리지 리포트
```

#### 3단계: 보안 스캔
```yaml
- Bandit (보안 취약점)
- Safety (의존성 보안)
```

#### 4단계: Docker 이미지 빌드
```yaml
- 이미지 빌드
- GHCR 푸시
- 메타데이터 태깅
```

#### 5단계: 배포
```yaml
Develop 브랜치:  → Staging 환경
Main 브랜치:     → Production 환경 (승인 필요)
```

### 트리거 조건

```yaml
- push to main branch      → 프로덕션 배포
- push to develop branch   → 스테이징 배포
- pull requests            → 코드 검사만 수행
```

### 워크플로우 상태 확인

```bash
# GitHub Actions 상태 확인
gh run list --repo yourorg/agent-system

# 최근 실행 로그 보기
gh run view <run-id> --log
```

---

## 3. 스테이징 환경 배포

### 전제 조건

```bash
# 필수 도구
- kubectl 1.24+
- Kubernetes 클러스터
- Docker Registry 접근
- 환경 변수 설정 파일 (.env.staging)
```

### 스테이징 환경 변수

```bash
cat > .env.staging << 'EOF'
ENVIRONMENT=staging
STAGING_DB_USER=staging_user
STAGING_DB_PASS=your_secure_password
STAGING_DB_HOST=postgres.staging.svc.cluster.local
STAGING_REDIS_PASS=your_redis_password
STAGING_REDIS_HOST=redis.staging.svc.cluster.local
FLASK_ENV=staging
LOG_LEVEL=INFO
EOF
```

### 스테이징 배포

```bash
# 클러스터 컨텍스트 확인
kubectl config current-context

# 클러스터 전환 (필요시)
kubectl config use-context staging-cluster

# 배포 실행
./deploy.sh staging up

# 배포 상태 확인
kubectl get deployments -n agent-system
kubectl get pods -n agent-system

# 로그 확인
./deploy.sh staging logs

# 롤아웃 상태
kubectl rollout status deployment/agent-system-api -n agent-system
```

### 스테이징 접근

```
API 서버:    https://api-staging.example.com
Grafana:     https://grafana-staging.example.com
Prometheus:  https://prometheus-staging.example.com
```

---

## 4. 프로덕션 환경 배포

### 전제 조건

```bash
# 필수 도구
- kubectl 1.24+
- Kubernetes 클러스터 (고가용성)
- 모니터링 시스템
- 백업 시스템
- 로깅 중앙화
```

### 프로덕션 환경 변수

```bash
cat > .env.prod << 'EOF'
ENVIRONMENT=production
PROD_DATABASE_URL=postgresql://prod_user:secure_password@postgres.prod.svc.cluster.local:5432/agent_system
PROD_CACHE_REDIS_URL=redis://:secure_password@redis.prod.svc.cluster.local:6379
FLASK_ENV=production
LOG_LEVEL=WARNING
JWT_SECRET=production_secret_key_change_me
MONITORING_ENABLED=true
ALERTING_ENABLED=true
EOF
```

### 프로덕션 배포 체크리스트

배포 전 다음을 확인하세요:

```
[ ] 모든 테스트 통과 (100%)
[ ] 보안 스캔 완료
[ ] 코드 검토 승인
[ ] 데이터베이스 백업 완료
[ ] 롤백 계획 수립
[ ] 모니터링 설정 완료
[ ] 알림 설정 완료
[ ] 보안 인증서 갱신
[ ] SSL/TLS 설정 확인
[ ] 환경 변수 설정 확인
[ ] 데이터베이스 마이그레이션 테스트
[ ] 성능 기준 설정
```

### 프로덕션 배포

```bash
# 클러스터 전환
kubectl config use-context prod-cluster

# 배포 실행 (확인 필요)
./deploy.sh prod up

# 배포 진행 중...
# 배포 시간: 약 5-10분

# 배포 상태 모니터링
watch kubectl get deployment agent-system-api -n agent-system

# 롤아웃 상태 확인
kubectl rollout status deployment/agent-system-api -n agent-system

# 최종 확인
kubectl get pods -n agent-system
```

### 프로덕션 접근

```
API 서버:    https://api.example.com
Grafana:     https://grafana.example.com (내부용)
Prometheus:  https://prometheus.example.com (내부용)
```

---

## 5. 모니터링 및 로깅

### Prometheus 메트릭

```yaml
# 수집되는 메트릭
- http_requests_total
- http_request_duration_seconds
- http_requests_in_progress
- agent_tasks_total
- agent_tasks_completed
- agent_tasks_failed
```

### Grafana 대시보드

기본 대시보드:
- API 요청 통계
- 응답 시간 분포
- 에러율
- 데이터베이스 성능
- Redis 캐시 히트율

### 로깅

```bash
# 개발 환경 로그
./deploy.sh dev logs

# 스테이징/프로덕션 로그
./deploy.sh staging logs
./deploy.sh prod logs

# 특정 Pod 로그
kubectl logs -f pod/agent-system-api-abc123 -n agent-system

# 마지막 100줄
kubectl logs --tail=100 deployment/agent-system-api -n agent-system
```

---

## 6. 롤백 절차

### Kubernetes 롤백

```bash
# 배포 이력 확인
kubectl rollout history deployment/agent-system-api -n agent-system

# 이전 버전으로 롤백
kubectl rollout undo deployment/agent-system-api -n agent-system

# 특정 리비전으로 롤백
kubectl rollout undo deployment/agent-system-api --to-revision=5 -n agent-system

# 롤백 진행 상황 모니터링
kubectl rollout status deployment/agent-system-api -n agent-system
```

### 롤백 자동 트리거

다음 조건에서 자동 롤백됨:
- Pod 5분 이상 CrashLoopBackOff
- 헬스 체크 연속 실패
- 에러율 > 50%

---

## 7. 유지보수

### 데이터베이스 유지보수

```bash
# 마이그레이션 상태 확인
kubectl exec -n agent-system deployment/agent-system-api -- python database_migration.py --status

# 마이그레이션 업그레이드
kubectl exec -n agent-system deployment/agent-system-api -- python database_migration.py --migrate-up

# 마이그레이션 다운그레이드
kubectl exec -n agent-system deployment/agent-system-api -- python database_migration.py --migrate-down --target=5
```

### 캐시 초기화

```bash
# Redis 캐시 플러시
kubectl exec -n agent-system -it <pod-name> -- redis-cli FLUSHDB

# 특정 키 삭제
kubectl exec -n agent-system -it <pod-name> -- redis-cli DEL key_pattern*
```

### 로그 정리

```bash
# 오래된 로그 삭제
kubectl exec -n agent-system deployment/agent-system-api -- find /app/logs -mtime +30 -delete
```

---

## 8. 성능 튜닝

### 스케일링 조정

```bash
# 현재 스케일 조회
kubectl get deployment agent-system-api -n agent-system

# 수동 스케일링
kubectl scale deployment agent-system-api --replicas=5 -n agent-system

# HPA 상태 확인
kubectl get hpa agent-system-api-hpa -n agent-system

# HPA 수정
kubectl edit hpa agent-system-api-hpa -n agent-system
```

### 리소스 모니터링

```bash
# Pod 리소스 사용량
kubectl top pods -n agent-system

# 노드 리소스 사용량
kubectl top nodes
```

---

## 9. 보안

### 비밀 정보 관리

```bash
# Secret 생성
kubectl create secret generic agent-system-secret \
  --from-literal=jwt-secret=your-secret \
  --from-literal=db-password=your-password \
  -n agent-system

# Secret 업데이트
kubectl patch secret agent-system-secret \
  -p '{"data":{"jwt-secret":"'$(echo -n 'new-secret' | base64)'"}}' \
  -n agent-system
```

### SSL/TLS 인증서

```bash
# Let's Encrypt 자동 갱신 (cert-manager 사용)
kubectl get certificate agent-system-tls -n agent-system

# 인증서 만료 확인
kubectl describe certificate agent-system-tls -n agent-system
```

---

## 10. 트러블슈팅

### 배포 실패

```bash
# Pod 상태 확인
kubectl describe pod <pod-name> -n agent-system

# 최근 이벤트 확인
kubectl get events -n agent-system --sort-by='.lastTimestamp'

# 로그 확인
kubectl logs <pod-name> -n agent-system

# Pod 재시작
kubectl delete pod <pod-name> -n agent-system
```

### 성능 문제

```bash
# 메트릭 확인
kubectl top pods -n agent-system

# 느린 쿼리 로그 확인
kubectl logs deployment/agent-system-api -n agent-system | grep "Duration"

# 데이터베이스 연결 확인
kubectl exec -it <pod-name> -n agent-system -- psql -h postgres -U agent_user
```

### 메모리 누수

```bash
# 메모리 사용량 추이
kubectl top pod <pod-name> -n agent-system --containers

# Pod 재시작
kubectl rollout restart deployment/agent-system-api -n agent-system
```

---

## 체크리스트

### 배포 전

- [ ] 모든 테스트 통과
- [ ] 코드 검토 완료
- [ ] 보안 스캔 완료
- [ ] 환경 변수 설정
- [ ] 데이터베이스 백업
- [ ] 모니터링 준비

### 배포 중

- [ ] 롤아웃 상태 모니터링
- [ ] 로그 확인
- [ ] 헬스 체크 확인
- [ ] 메트릭 수집

### 배포 후

- [ ] 기능 테스트
- [ ] 성능 확인
- [ ] 로그 분석
- [ ] 알림 설정 확인

---

## 자주 묻는 질문 (FAQ)

### Q: 배포 시간은 얼마나 걸립니까?
A: 개발/스테이징은 2-3분, 프로덕션은 5-10분입니다.

### Q: 배포 중 서비스 다운타임이 있습니까?
A: 아니오, Rolling Update로 무중단 배포합니다.

### Q: 롤백은 얼마나 빠릅니까?
A: 1-2분 정도 소요됩니다.

### Q: 이미지 크기는 얼마입니까?
A: 약 200-300MB입니다.

### Q: 자동 스케일링은 어떻게 작동합니까?
A: CPU/메모리 사용률에 따라 3-10개 Pod으로 자동 조정됩니다.

---

## 연락처 및 지원

- 문서: https://docs.example.com
- 이슈: https://github.com/yourorg/agent-system/issues
- 이메일: ops@example.com

---

**마지막 업데이트: 2025-10-19**
**버전: 1.0.0**
