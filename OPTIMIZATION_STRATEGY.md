# LM Studio & Docker 백엔드 최적화 전략

## 문제 분석 결과

### 1. LM_Support.exe CPU 점유율 512% (극도로 높음)
- **원인**: LM Studio의 서포트 프로세스가 자동 모델 로드 중
- **영향**: 시스템 전체 응답 속도 저하 (재부팅 직후에도 발생)
- **증상**: 데스크탑 기반 AI 시스템에서 초기 시작 시간 오래 걸림

### 2. 다중 LM Studio 인스턴스 실행
- **현황**: 8개 이상의 LM Studio.exe 프로세스 실행 중
- **문제**: 메모리 중복 할당, 리소스 낭비
- **예상 원인**: 자동 재시작, 멀티플 창 열림, 또는 설정 오류

### 3. Docker 백엔드 높은 CPU 사용
- **Docker Desktop**: CPU 52% 점유 (과도함)
- **원인**: 불필요한 컨테이너 실행 또는 과도한 로깅
- **현황**: PostgreSQL, Redis, Agent API, Nginx, Prometheus, Grafana 모두 실행 중

---

## 최적화 계획

### Phase 1: LM Studio 최적화

#### 1.1 LM Studio 시작 성능 개선
```ini
# LM Studio 설정 파일 위치: %APPDATA%\LMStudio\settings.json
최적화 항목:
- Auto-load model on startup: DISABLED
- Model preload threads: 1 (default 4)
- GPU memory allocation: 8GB (조정 필요)
- CPU thread pool: 4 (조정 필요)
```

#### 1.2 프로세스 정책 설정
```powershell
1. 일일 1회 자동 시작 (예: 오전 9시)
2. 유휴 시간 자동 언로드
3. 메모리 누수 감시 및 자동 재시작
```

#### 1.3 API 끝점 최적화
```yaml
# /fdo_agi_repo/configs/app.yaml 수정
llm:
  endpoint: http://localhost:8080/v1/chat/completions
  connection_pool_size: 5
  request_timeout: 30s
  retry_policy:
    max_retries: 2
    backoff_multiplier: 2
  fallback:
    - provider: gemini
    - provider: ollama
```

---

### Phase 2: Docker 백엔드 최적화

#### 2.1 불필요한 서비스 비활성화
```yaml
# /session_memory/docker-compose.yml 수정
제거/비활성화:
- nginx: 현재 사용 안 함
- prometheus + grafana: 개발 환경에서는 선택적

유지:
- postgres: 필수 (데이터 저장)
- redis: 필수 (캐시/세션)
- agent-api: 필수 (메인 API)
```

#### 2.2 Docker 리소스 할당 제한
```yaml
services:
  agent-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

#### 2.3 Docker Desktop 설정 최적화
```ini
# Docker Desktop Settings
Resources:
- CPU: 4 (시스템의 50%)
- Memory: 4GB (시스템의 50%)
- Disk: 64GB
- Swap: 1GB

WSL 2:
- CPU cores limit: 4
- Memory limit: 4GB
```

---

### Phase 3: 프로세스 관리 및 자동화

#### 3.1 스마트 프로세스 감시 스크립트
```powershell
# /scripts/lm_studio_optimizer.ps1
목표:
1. LM_Support CPU > 80% 감시
2. 유휴 상태 자동 언로드
3. 메모리 누수 감시
4. 일일 정크 정리
```

#### 3.2 Docker 상태 모니터링
```powershell
# /scripts/docker_health_check.ps1
목표:
1. 컨테이너 상태 확인
2. 리소스 사용량 추적
3. 비정상 서비스 자동 재시작
4. 성능 메트릭 기록
```

---

### Phase 4: 통합 오케스트레이션

#### 4.1 통합 시작 스크립트
```powershell
# /scripts/ai_system_startup.ps1
순서:
1. Docker Desktop 상태 확인
2. 필수 서비스 시작 (postgres, redis)
3. Agent API 시작
4. LM Studio 시작 (비동기)
5. 헬스 체크 및 대기시간 측정
```

#### 4.2 성능 대시보드
```
모니터링 항목:
- LM Studio 응답 시간
- Docker 서비스 상태
- 시스템 리소스 (CPU, 메모리)
- API 응답 속도
- 에러율
```

---

## 예상 효과

### 현재 상태
- LM_Support CPU: 512% (매우 높음)
- Docker CPU: 52% (높음)
- 전체 응답 시간: 느림
- 초기 시작 시간: 5-10분

### 최적화 후 기대값
- LM_Support CPU: < 20% (유휴 상태)
- Docker CPU: < 20% (최소 필수 서비스만)
- 전체 응답 시간: 2배 향상
- 초기 시작 시간: 30초

---

## 구현 순서

1. **즉각적 (오늘)**
   - [ ] LM_Support 프로세스 종료
   - [ ] Docker 불필요 서비스 비활성화
   - [ ] 시스템 재부팅 및 성능 측정

2. **단기 (1-2일)**
   - [ ] LM Studio 설정 파일 최적화
   - [ ] Docker 리소스 제한 적용
   - [ ] 프로세스 감시 스크립트 작성

3. **중기 (3-5일)**
   - [ ] 통합 시작/중지 스크립트 구현
   - [ ] 성능 모니터링 대시보드 구축
   - [ ] 자동 최적화 규칙 적용

4. **장기 (1주)**
   - [ ] 24시간 연속 운영 테스트
   - [ ] 성능 베이스라인 설정
   - [ ] 자동 재시작 정책 미세조정

---

## 주요 설정 파일 수정 대상

1. `C:\workspace\agi\fdo_agi_repo\configs\app.yaml` - LLM 설정
2. `C:\workspace\agi\session_memory\docker-compose.yml` - Docker 구성
3. `%APPDATA%\LMStudio\settings.json` - LM Studio 설정
4. Docker Desktop Settings - 리소스 할당
5. Windows Task Scheduler - 자동화 작업

---

## 추가 고려사항

- **네트워크**: LM Studio 로컬 포트 (8080) 안정성 확인
- **메모리**: 시스템 총 메모리 기준으로 Docker 할당 조정 필요
- **모니터링**: 성능 저하 시 자동 알림 설정
- **백업**: 최적화 전 현재 설정 백업

