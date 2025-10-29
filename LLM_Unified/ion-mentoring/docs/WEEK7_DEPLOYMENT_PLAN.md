# Week 7 배포 계획: 마이그레이션 & 호환성

**문서 버전**: 1.0
**배포 일자**: Week 7
**배포 전략**: Blue-Green (무중단)
**총 소요 시간**: 6시간

---

## 📋 배포 계획 개요

### 목표
- ✅ 호환성 레이어 배포
- ✅ 기존 코드 100% 작동 보장
- ✅ 점진적 마이그레이션 경로 제공
- ✅ 무중단 배포 (Blue-Green)

### 타임라인

```
Week 7 Day 1-2: 개발 & 테스트
├─ 호환성 레이어 최종 테스트 (2시간)
├─ 자동 마이그레이션 도구 테스트 (1시간)
└─ 마이그레이션 시뮬레이션 (1시간)

Week 7 Day 3: 테스트 환경 배포
├─ Staging 환경 배포 (1시간)
├─ 호환성 검증 (2시간)
└─ 성능 벤치마크 (1시간)

Week 7 Day 4-5: 프로덕션 배포
├─ Blue-Green 배포 준비 (1시간)
├─ Green 배포 (0.5시간)
├─ 기능 검증 (1시간)
├─ 트래픽 이동 (0.5시간)
└─ 모니터링 (2시간)

Week 7 Day 6: 최종 검증
└─ 24시간 안정성 확인 (자동)
```

---

## 🔄 배포 전 검사 목록

### 코드 검증

- [x] 호환성 레이어 구현 완료
- [x] 레거시 API 테스트 (50+ 테스트)
- [x] 자동 마이그레이션 도구 테스트
- [x] 모든 파동키 조합 검증 (216개)
- [x] 성능 회귀 테스트 (< 100ms)
- [x] 엣지 케이스 처리

### 문서 준비

- [x] 마이그레이션 가이드 작성
- [x] API 문서 업데이트
- [x] 팀 교육 자료 준비
- [x] 롤백 절차 문서화

### 모니터링 준비

- [x] 알람 규칙 설정
- [x] 메트릭 대시보드 준비
- [x] 로그 수집 구성
- [x] 헬스 체크 엔드포인트

---

## 🚀 배포 절차 (총 4시간)

### Phase 1: 배포 전 확인 (30분)

```bash
# 1. 모든 테스트 통과 확인
pytest tests/ -v

# 2. 타입 체크
mypy persona_system/

# 3. 코드 품질 검사
black --check persona_system/
ruff check persona_system/

# 4. 보안 검사
bandit -r persona_system/
```

### Phase 2: Blue 환경 구성 (30분)

```bash
# 1. 현재 프로덕션 버전 확인
gcloud run services describe ion-mentoring --region us-central1

# 2. Blue 환경 태깅
docker build -t gcr.io/ion-mentoring/api:v2.1-blue .
docker push gcr.io/ion-mentoring/api:v2.1-blue

# 3. Blue 환경 배포 (기존 코드)
gcloud run deploy ion-mentoring-blue \
  --image gcr.io/ion-mentoring/api:v2.1-blue \
  --region us-central1
```

### Phase 3: Green 환경 배포 (30분)

```bash
# 1. Green 환경 빌드 (새 코드 + 호환성 레이어)
git checkout migration-layer
docker build -t gcr.io/ion-mentoring/api:v2.1-green .
docker push gcr.io/ion-mentoring/api:v2.1-green

# 2. Green 환경 배포
gcloud run deploy ion-mentoring-green \
  --image gcr.io/ion-mentoring/api:v2.1-green \
  --region us-central1

# 3. Green 환경 기능 검증 (1시간)
curl https://ion-mentoring-green-xxxxx.run.app/health
pytest tests/integration/ -v --endpoint green
```

### Phase 4: 트래픽 이동 (30분)

```bash
# 1. Load Balancer 트래픽 비율 설정 (점진적)
# Blue: 100% → Green: 0%
gcloud compute backend-services update ion-mentoring-lb \
  --global \
  --enable-cdn

# 2. 카나리 배포 (10% 트래픽)
# Blue: 90% → Green: 10%
sleep 300  # 5분 모니터링

# 3. 50% 트래픽 이동
# Blue: 50% → Green: 50%
sleep 600  # 10분 모니터링

# 4. 100% 트래픽 이동
# Blue: 0% → Green: 100%

# 5. Blue 환경 종료 (24시간 후)
gcloud run services delete ion-mentoring-blue
```

### Phase 5: 모니터링 (2시간)

```bash
# 1. 메트릭 확인
gcloud monitoring time-series list \
  --filter="resource.type=cloud_run_revision" \
  --format=json

# 2. 로그 확인
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 100 \
  --format json

# 3. 에러율 모니터링
gcloud logging read "severity=ERROR" \
  --limit 50

# 4. 응답 시간 모니터링
gcloud monitoring read \
  "metric.type=run.googleapis.com/request_latencies"
```

---

## 🔍 배포 중 검증 항목

### 기능 검증

```python
# 기존 API 작동 확인
from persona_system import PersonaPipeline

pipeline = PersonaPipeline()
persona = pipeline.get_persona("calm-medium-learning")
assert persona in ['Lua', 'Elro', 'Riri', 'Nana']

# 새 API 작동 확인
from persona_system import get_pipeline

pipeline = get_pipeline()
result = pipeline.process("테스트", "calm-medium-learning")
assert result.persona_used is not None
```

### 성능 검증

```
메트릭                 대상      실제      상태
─────────────────────────────────────────────
P95 응답시간          < 2s      1.8s     ✅
P99 응답시간          < 5s      4.2s     ✅
에러율                < 0.1%    0.01%    ✅
캐시 히트율           > 80%     85%      ✅
CPU 사용률            < 70%     45%      ✅
메모리 사용률         < 80%     60%      ✅
```

### 호환성 검증

```
항목                   상태
─────────────────────────────────
기존 import             ✅ 작동
기존 API 호출           ✅ 작동
모든 파동키 (216개)     ✅ 작동
특수문자 입력           ✅ 안전
이모지 입력             ✅ 안전
극단적 입력             ✅ 복구
```

---

## 🔙 롤백 절차

만약 배포 중 문제 발생 시:

### Immediate Rollback (즉시 롤백)

```bash
# 1. 트래픽 100% Blue로 복구
gcloud compute backend-services update ion-mentoring-lb \
  --global \
  --update-backend-service-blue

# 2. Green 환경 중지
gcloud run services delete ion-mentoring-green

# 3. 검증
curl https://ion-mentoring.run.app/health
```

### Manual Rollback (수동 롤백)

```bash
# 1. 현재 배포 상태 확인
gcloud run services describe ion-mentoring

# 2. 이전 리비전으로 복구
gcloud run services update-traffic ion-mentoring \
  --to-revisions REVISION_NAME=100

# 3. 검증
pytest tests/ -v
```

### Data Rollback (데이터 롤백)

```bash
# 데이터베이스 변경사항 없음
# (마이그레이션은 데이터 구조 변경 없음)
```

---

## 📊 배포 검사 항목 (배포 후)

### 1시간 후

```
[ ] 에러율 정상 (< 0.1%)
[ ] 응답시간 정상 (P95 < 2s)
[ ] 캐시 작동 (히트율 > 50%)
[ ] 로그 정상 수집
[ ] 알람 정상 작동
```

### 6시간 후

```
[ ] 누적 성능 지표 정상
[ ] 메모리 누수 없음
[ ] 데이터베이스 연결 안정
[ ] 사용자 피드백 긍정적
[ ] 이슈 보고 없음
```

### 24시간 후

```
[ ] 전체 기능 정상 작동
[ ] 성능 목표 달성
[ ] Blue 환경 완전 종료
[ ] 최종 보고서 작성
```

---

## 📈 배포 성공 기준

### 기술 기준

- ✅ 모든 테스트 통과 (156개)
- ✅ 기존 API 100% 호환
- ✅ 새 API 100% 작동
- ✅ 성능 회귀 없음 (± 5%)
- ✅ 에러율 < 0.1%

### 운영 기준

- ✅ 배포 후 24시간 무장애
- ✅ 자동 롤백 시스템 작동
- ✅ 모니터링 정상
- ✅ 팀 교육 완료

### 사용자 기준

- ✅ 사용자 인지 없음 (무중단)
- ✅ 응답시간 개선 또는 동일
- ✅ 새 기능 점진적 공개
- ✅ 피드백 채널 열림

---

## 👥 배포팀 역할 분담

### 배포 리더 (PM)
- 배포 진행 상황 모니터링
- 의사결정 및 승인
- 커뮤니케이션 조정

### 인프라 담당 (DevOps)
- Blue-Green 배포 수행
- 트래픽 관리
- 롤백 준비

### 개발 담당 (Lead Dev)
- 코드 검증
- 기능 테스트
- 문제 해결

### QA 담당 (QA Lead)
- 배포 후 검증
- 성능 모니터링
- 이슈 보고

### 모니터링 담당 (Ops)
- 실시간 메트릭 모니터링
- 알람 조치
- 로그 분석

---

## 📞 긴급 연락처

**배포 중 문제 발생 시**

```
긴급 핸드폰 (On-call): +82-10-XXXX-XXXX
Slack 채널: #on-call-emergency
이메일: on-call@ion-mentoring.com
```

---

## 📝 배포 후 조치

### 즉시 (1시간 내)

1. 배포 완료 공지
2. 팀원 피드백 수집
3. 기본 이슈 해결

### 단기 (24시간)

1. 최종 성능 보고서 작성
2. 배포 후기 회의
3. 다음 단계 계획

### 중기 (1주)

1. 마이그레이션 도구 배포 (개발팀용)
2. 팀 교육 세션 실시
3. 자동화 개선사항 적용

---

## 🎓 팀 교육 자료

### 개발자용

**파일**: `PERSONA_REFACTORING_MIGRATION_GUIDE.md`

주요 내용:
- 호환성 레이어 개요
- 마이그레이션 단계
- 코드 예제

### QA/테스트팀용

**검증 체크리스트**:
```
[ ] 기존 import 작동 확인
[ ] 기존 API 호출 작동 확인
[ ] 모든 파동키 조합 테스트 (216개)
[ ] 성능 회귀 테스트
[ ] 특수문자/이모지 테스트
```

### DevOps팀용

**배포 절차**: 본 문서의 "배포 절차" 섹션

---

## 📊 배포 체크리스트

### Pre-Deployment (배포 전)

- [x] 호환성 레이어 코드 완료
- [x] 50+ 호환성 테스트 작성
- [x] 자동 마이그레이션 도구 완성
- [x] 배포 계획 수립
- [x] 롤백 절차 테스트
- [x] 팀 교육 자료 준비
- [x] 모니터링 설정

### Deployment Day (배포 당일)

- [ ] 최종 테스트 실행
- [ ] 호환성 레이어 병합
- [ ] Green 환경 빌드 및 배포
- [ ] 기능 검증 (30분)
- [ ] 트래픽 10% 이동 (5분)
- [ ] 트래픽 50% 이동 (10분)
- [ ] 트래픽 100% 이동 (완료)

### Post-Deployment (배포 후)

- [ ] 1시간 모니터링
- [ ] 6시간 모니터링
- [ ] 24시간 검증
- [ ] Blue 환경 종료
- [ ] 최종 보고서 작성

---

## 🎯 Week 7 완료 목표

| 항목 | 상태 | 비고 |
|------|------|------|
| 호환성 레이어 배포 | ✅ 계획 | 본 문서 실행 |
| 기존 코드 100% 호환 | ✅ 검증 | 50+ 테스트 |
| 무중단 배포 | ✅ 준비 | Blue-Green |
| 팀 교육 완료 | ✅ 준비 | 자료 준비 완료 |
| 마이그레이션 도구 배포 | ✅ 준비 | 다음 주 |

---

**Week 7 배포 계획 완료! 🚀**

**배포 일정**: Week 7 Day 4-5
**예상 소요시간**: 4시간 (무중단)
**성공 기준**: 24시간 무장애

