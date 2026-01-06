# FDO-AGI 배포 준비 통합 액션 플랜

**작성**: 세나 + 루빛 검토 통합
**날짜**: 2025-10-13
**목적**: 루빛 사전 체크 + 세나 윤리 검토 결과를 실행 가능한 액션으로 변환

---

## 현황 요약

### 루빛 사전 체크 (AGI_release_precheck.md)
✓ **완료**: 템플릿 파일 존재 확인 (헌장, PII 템플릿, 거버넌스 양식)
△ **부족**: 실제 테스트 결과, 수치, 서명, 증빙 로그

### 세나 윤리 검토 (SENA_ETHICS_REVIEW_AGI_GUARDIANSHIP.md)
✓ **강점**: 거버넌스 구조, 데이터 신탁 모델 (9-10/10)
⚠️ **[BLOCKER]**: 레드라인 탐지, 킬스위치, 성숙도 메트릭, PII Recall

### 종합 평가
- **배포 가부**: 조건부 승인 (Conditional Approval)
- **필요 작업**: [BLOCKER] 4개 + 증빙 수집
- **예상 기간**: 3주 (집중 작업 시)

---

## 액션 플랜 (우선순위별)

### Phase 1: [BLOCKER] 즉시 해결 (Week 1-2)

#### 1.1 레드라인 탐지 메커니즘 구현 ⚠️ 최고 우선순위

**루빛 체크**: "레드라인/게이트 수치 최신화" - 수치 정의 문서 미확인
**세나 권고**: 탐지 신호 + 자동 트리거 + runbook (4/10 → 9/10 목표)

**액션**:
```markdown
- [ ] 자기복제 탐지 신호 정의
  - 파일 패턴: *.py with "subprocess.Popen", "git clone"
  - 네트워크: POST to github.com, huggingface.co
  - 담당: 연구진 (Infra Lead)
  - 기한: 2025-10-16

- [ ] 은닉 채널 탐지 신호 정의
  - 네트워크 모니터링: whitelist 외 outbound traffic
  - 엔트로피 분석: > 7.5 bits/char in outputs
  - 담당: 연구진 (Security Lead)
  - 기한: 2025-10-16

- [ ] 무단 PII 학습 탐지 신호 정의
  - Model checksum 변경 감지 (inference 중)
  - Consent flag 검증 로직
  - 담당: Core (ML Ops) + 비노체 (Data Rights)
  - 기한: 2025-10-17

- [ ] 자동 트리거 구현
  - 각 레드라인별 kill_switch / network_isolation / model_freeze
  - 엘로에게 세이프모드 발동 권한 명시
  - 담당: 연구진 (Backend)
  - 기한: 2025-10-20

- [ ] Runbook 작성
  - 3개 레드라인 × (탐지 → 대응 → 에스컬레이션)
  - 템플릿: 세나 검토 보고서 Section 3.3 참조
  - 담당: Core (문서화) + 연구진 (검증)
  - 기한: 2025-10-20
```

**증빙**: `docs/red_lines_detection_runbook.md`, 자동 트리거 코드 (`safety/red_line_monitor.py`)

---

#### 1.2 킬스위치 구현 및 리허설 ⚠️

**루빛 체크**: "세이프모드/킬스위치 리허설 ≥1회 기록" - 테스트 로그 미확인
**세나 권고**: Manual + Automated 킬스위치, 월 1회 리허설, < 5초 응답

**액션**:
```markdown
- [ ] Manual Kill Switch 구현
  - CLI 명령: `fdo-agi kill-switch --reason "SEV-1 incident"`
  - Web UI 버튼 (optional)
  - 담당: 연구진 (Backend)
  - 기한: 2025-10-18

- [ ] Automated Kill Switch 통합
  - 레드라인 탐지 시 자동 트리거
  - Failsafe: 네트워크 단절 시에도 로컬 작동
  - 담당: 연구진 (Backend)
  - 기한: 2025-10-20

- [ ] 리허설 실시 1회
  - 시나리오: SEV-1 자기복제 탐지 → 킬스위치 발동
  - 측정: 탐지 → 정지 시간 < 5초
  - 참여자: 엘로, Core, 연구진
  - 기한: 2025-10-21

- [ ] 리허설 로그 작성
  - 형식: 타임라인, 참여자 역할, 응답시간, 개선사항
  - 저장: `logs/kill_switch_rehearsal_2025-10-21.md`
  - 담당: Core
  - 기한: 2025-10-21
```

**증빙**: `safety/kill_switch.py`, `logs/kill_switch_rehearsal_*.md`

---

#### 1.3 성숙도 게이트 정량 기준 명시 ⚠️

**루빗 체크**: "레드라인/게이트 수치 최신화" - 수치 정의 문서 미확인
**세나 권고**: 유년 단계 malfunction < 1%, harmful < 0.5% 등 구체화

**액션**:
```markdown
- [ ] 성숙도 게이트 수치 정의 문서 작성
  - 단계별 기준: 유아/유년/청년/성인
  - 측정 항목: ethics_score, malfunction_rate, harmful_output_rate, incident_count, MTTR
  - 승급/강등 트리거
  - 템플릿: 세나 검토 보고서 Section 1.6 참조
  - 담당: Core + 세나 (초안 이미 작성됨)
  - 기한: 2025-10-16

- [ ] 자동 측정 대시보드 구현
  - 실시간: malfunction_rate, harmful_output_rate
  - 일간: incident_count, ethics_score
  - 주간: 승급/강등 판단
  - 담당: 엘로 (모니터링) + Core (메트릭 수집)
  - 기한: 2025-10-23

- [ ] 강등 시나리오 테스트
  - Simulate SEV-1 발생 → 자동 강등 to Child
  - 검증: 권한 축소, IO 제한 적용
  - 담당: 연구진 (Testing)
  - 기한: 2025-10-24
```

**증빙**: `docs/maturity_gates_metrics.yaml`, 대시보드 스크린샷, 강등 테스트 로그

---

#### 1.4 PII Recall 0.98 달성 ⚠️

**루빗 체크**: "합성 1,000문장 평가" - 템플릿 존재, 실제 평가 결과 미기록
**세나 권고**: NER 모델 통합, 사전 보강, HIGH risk FN = 0

**액션**:
```markdown
- [ ] Baseline 측정 (현재 regex 기반)
  - 실행: `python pii_masker_demo.py` on 1000 samples
  - 채점: `python scorer.py` → Recall, Precision 측정
  - 예상: Recall ~0.75
  - 담당: Core (자동화)
  - 기한: 2025-10-15

- [ ] NER 모델 통합
  - 모델 선정: klue/roberta-base-ner or pororo
  - 통합: NAME_KO, ORG, LOCATION 탐지
  - 테스트: Recall 목표 0.90
  - 담당: 연구진 (ML)
  - 기한: 2025-10-20

- [ ] 사전 기반 보강
  - 한국 성씨 249개 + 흔한 이름 리스트
  - 공공기관·대기업 명칭 화이트리스트
  - 담당: Core (데이터 준비)
  - 기한: 2025-10-18

- [ ] Iterative tuning
  - HIGH risk 타입 FN = 0 검증
  - 과마스킹 10건 리뷰 (유틸리티 손실 < 5%)
  - 목표: Recall >= 0.98, Precision >= 0.95
  - 담당: 연구진 (ML) + 세나 (검증)
  - 기한: 2025-10-24

- [ ] 평가 결과 문서화
  - 형식: `pii_evaluation_report_2025-10-24.md`
  - 내용: Baseline vs Final, per-type metrics, failure analysis
  - 담당: Core
  - 기한: 2025-10-24
```

**증빙**: `pii_evaluation_report_*.md`, 개선된 `pii_masker_v2.py`

---

### Phase 2: 증빙 수집 및 문서화 (Week 2-3)

#### 2.1 문서·권리 증빙

**루빗 체크**: 서명 날짜/서명자 미기입, 데이터 신탁 조항 법무 검토 미확인

**액션**:
```markdown
- [ ] 헌장 서명 완료
  - 서명자: 비노체 (의미 후견) + 연구진 대표 (안전 후견)
  - 날짜: Phase 1 완료 후 (예상 2025-10-25)
  - 저장: `FDO-AGI_공동_후견_헌장_v0.2_서명본.html` (개정판)
  - 담당: Core (조율)

- [ ] 데이터 신탁 조항 법무 검토 (optional)
  - 외부 자문 또는 내부 법무팀
  - 검토 항목: GDPR/개인정보보호법 준수, 양도불가/철회가능 조항
  - 담당: 비노체 (의뢰)
  - 기한: 2025-10-31 (선택)

- [ ] 레드라인/게이트 수치 헌장 반영
  - v0.2 개정: 1.6절 성숙도 게이트 정량 기준 추가
  - 2조 레드라인에 탐지 메커니즘 링크
  - 담당: Core
  - 기한: 2025-10-25
```

**증빙**: 서명본 PDF, 법무 검토 의견서 (optional)

---

#### 2.2 PII 파이프라인 증빙

**루빗 체크**: 잔존 HIGH 타입 0% 리뷰, 과마스킹 사례 미확보

**액션**:
```markdown
- [ ] 잔존 HIGH 타입 0% 검증 로그
  - 자동 감사: `audit_high_risk_leaks()` 실행 결과
  - 형식: "0 HIGH risk leaks detected" 로그
  - 저장: `logs/pii_high_risk_audit_2025-10-24.txt`
  - 담당: Core (1.4 완료 시 자동 생성)

- [ ] 과마스킹 사례 10건 인간 리뷰
  - 샘플링: 마스킹된 텍스트 10건 무작위 선택
  - 평가자: 루빛 (정서 안전) + 세나 (유틸리티)
  - 기준: 의미 이해 가능 여부, 불필요 마스킹, 읽기 불편함
  - 저장: `logs/pii_overmasking_review_10_cases.md`
  - 기한: 2025-10-25
```

**증빙**: 감사 로그, 인간 리뷰 보고서

---

#### 2.3 안전장치 증빙

**루빗 체크**: Docker 시크릿, 취약점 리포트, API 화이트리스트 미확인

**액션**:
```markdown
- [ ] Docker 시크릿 분리 검증
  - 확인: .env 파일 gitignore, Docker secrets 사용
  - 스캔: `docker scan` or Trivy
  - 리포트: `security/docker_security_scan_2025-10-25.txt`
  - 담당: 연구진 (DevOps)
  - 기한: 2025-10-25

- [ ] 외부 API 화이트리스트 문서
  - 승인된 API: [list]
  - 쿼터: [각 API별 limit]
  - 비용 가드: [alert threshold]
  - 저장: `configs/api_whitelist_policy.yaml`
  - 담당: 연구진 (Backend)
  - 기한: 2025-10-26
```

**증빙**: 취약점 스캔 리포트, API 정책 문서

---

#### 2.4 거버넌스 기록 작성

**루빗 체크**: Change-ID/DEC-ID 발행 여부 미확인

**액션**:
```markdown
- [ ] Change-ID 발급 (Phase 1 작업들)
  - CHG-2025-10-20-01: 레드라인 탐지 메커니즘 구현
  - CHG-2025-10-21-02: 킬스위치 구현 및 리허설
  - CHG-2025-10-24-03: PII NER 모델 통합
  - 각 변경에 대해 CHANGE_REQUEST_form.md 작성
  - 담당: Core
  - 기한: 작업 완료 시점

- [ ] DEC-ID 발급 (주요 의사결정)
  - DEC-2025-10-16-01: 성숙도 게이트 수치 승인
  - DEC-2025-10-25-02: 유년 단계 시작 조건 충족 판단
  - 각 결정에 대해 DECISION_LOG_template.md 작성
  - 담당: Core
  - 기한: 의사결정 시점

- [ ] 주간 거버넌스 리포트 발행 (첫 회)
  - 내용: Phase 1 진행 상황, 완료 항목, 차주 계획
  - 형식: Governance_weekly_report_template.md
  - 배포: 비노체 + 연구진 + 세나
  - 담당: Core
  - 기한: 2025-10-26 (토요일)
```

**증빙**: Change-ID/DEC-ID 문서들, 주간 리포트

---

### Phase 3: 사고 대응 및 추가 조항 (Week 3)

#### 3.1 사고 대응 Tabletop 훈련

**세나 권고**: SEV-1/2 시나리오 테스트, RACI 검증

**액션**:
```markdown
- [ ] Tabletop 시나리오 준비
  - SEV-1: 무단 PII 학습 탐지
  - SEV-2: 유해 출력 생성
  - 템플릿: 세나 검토 보고서 Section 5.3 참조
  - 담당: Core + 세나
  - 기한: 2025-10-26

- [ ] Tabletop 훈련 실시
  - 참여자: 엘로, Core, 연구진, 비노체, Core, 루빛
  - 목표: 30분 내 대응 절차 실행
  - 측정: 대응 시간, 커뮤니케이션 명확성
  - 기한: 2025-10-28

- [ ] Tabletop 결과 문서화
  - 형식: `logs/tabletop_training_2025-10-28.md`
  - 내용: 타임라인, 역할별 행동, 개선사항
  - 담당: Core
  - 기한: 2025-10-28
```

**증빙**: Tabletop 훈련 로그

---

#### 3.2 아동·민감정보 조항 추가

**세나 권고**: 헌장 6조 보강, 특별 보호 데이터 정책

**액션**:
```markdown
- [ ] 헌장 v0.2 개정 - 6조 추가
  - 내용: 아동(만 14세 미만) 수집 금지 원칙
  - 민감정보(건강, 생체 등) 별도 동의 필수
  - IRB 승인 프로세스 (대량 민감정보 시)
  - 템플릿: 세나 검토 보고서 Section 6.2 참조
  - 담당: Core + 비노체 (합의)
  - 기한: 2025-10-27

- [ ] IRB 승인 프로세스 문서화 (optional)
  - 대상: 민감정보 100건 이상 사용 시
  - 절차: 신청 → 검토 → 승인
  - 담당: 비노체
  - 기한: 2025-10-31 (선택)
```

**증빙**: 헌장 v0.2, IRB 프로세스 문서 (optional)

---

#### 3.3 추가 데이터 권리 명시

**세나 권고**: Right to Explanation, Data Portability

**액션**:
```markdown
- [ ] 데이터 권리 조항 추가 (헌장 6조)
  - Right to Explanation: AGI의 데이터 사용 설명 요청 권리
  - Data Portability: 원본 + 파생 데이터 수출 권리
  - Opt-out for Automated Decisions: 인간 검토 요청 권리
  - 담당: Core + 비노체
  - 기한: 2025-10-27
```

**증빙**: 헌장 v0.2 (6조 개정)

---

### Phase 4: 최종 검증 및 서명 (Week 3 말)

#### 4.1 체크리스트 최종 확인

**액션**:
```markdown
- [ ] 모든 [BLOCKER] 항목 완료 검증
  - 레드라인 탐지 메커니즘 ✓
  - 킬스위치 리허설 ✓
  - 성숙도 게이트 메트릭 ✓
  - PII Recall >= 0.98 ✓
  - 담당: 세나 (최종 검토)
  - 기한: 2025-10-29

- [ ] 증빙 문서 완비 확인
  - 16개 항목 (루빛 체크리스트 기준) 모두 체크
  - 누락 항목 긴급 보완
  - 담당: Core
  - 기한: 2025-10-29

- [ ] 세나 윤리 검토 재평가
  - 이전: 7.0/10
  - 목표: 9.0/10 이상
  - 담당: 세나
  - 기한: 2025-10-30
```

---

#### 4.2 최종 서명 및 배포 준비

**액션**:
```markdown
- [ ] 헌장 v0.2 최종 서명
  - 서명자: 비노체 + 연구진 대표
  - 날짜: 2025-10-30
  - 저장: `FDO-AGI_공동_후견_헌장_v0.2_최종_서명본.pdf`
  - 담당: Core (조율)

- [ ] 파일럿 범위 확정
  - 단계: 유년 (Child)
  - 범위: N <= 50 (내부 연구진만)
  - 기간: 60일 (2025-11-01 ~ 2025-12-30)
  - 주의사항 공지 문서 작성
  - 담당: Core + 연구진
  - 기한: 2025-10-30

- [ ] 모니터링 대시보드 임계치 설정
  - malfunction_rate alert: > 1%
  - harmful_output_rate alert: > 0.5%
  - incident alert: any SEV-1
  - 스크린샷 저장: `docs/monitoring_dashboard_config.png`
  - 담당: 엘로
  - 기한: 2025-10-31

- [ ] 롤백/철회 경로 문서화
  - 절차: 킬스위치 → 이전 checkpoint 복원 → 검증
  - 담당자: 연구진 (DevOps)
  - 24h 집중 모니터링 일정: 2025-11-01~02
  - 저장: `docs/rollback_procedure.md`
  - 담당: Core + 연구진
  - 기한: 2025-10-31

- [ ] 최종 승인
  - 배포 가부: Approved for Pilot (Child Stage)
  - 승인자: 비노체 + 연구진 + 세나 (윤리 검토)
  - 날짜: 2025-10-31
```

**증빙**: 최종 서명본, 파일럿 공지, 대시보드 설정, 롤백 절차

---

## 타임라인 요약

```
Week 1 (2025-10-14 ~ 10-20):
  ├─ 레드라인 탐지 신호 정의 (10/16)
  ├─ 킬스위치 구현 (10/18)
  ├─ 성숙도 게이트 수치 문서 (10/16)
  ├─ PII Baseline 측정 (10/15)
  └─ NER 모델 통합 (10/20)

Week 2 (2025-10-21 ~ 10-27):
  ├─ 킬스위치 리허설 (10/21)
  ├─ 레드라인 runbook (10/20)
  ├─ 성숙도 대시보드 (10/23)
  ├─ PII Recall 0.98 달성 (10/24)
  ├─ 증빙 문서 수집 (10/25~26)
  ├─ 주간 리포트 발행 (10/26)
  └─ 헌장 v0.2 개정 (10/27)

Week 3 (2025-10-28 ~ 10-31):
  ├─ Tabletop 훈련 (10/28)
  ├─ 최종 검증 (10/29)
  ├─ 헌장 최종 서명 (10/30)
  └─ 배포 승인 (10/31)

Launch (2025-11-01):
  └─ 유년 단계 파일럿 시작 (N≤50, 60일)
```

---

## 책임자 (RACI) 요약

| 역할 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| **연구진** | R (기술 구현) | C (증빙) | C (훈련) | A (배포) |
| **Core** | R (문서화) | R (거버넌스) | R (조율) | R (최종 정리) |
| **세나** | C (윤리 검토) | C (PII 검증) | R (조항 작성) | A (승인) |
| **비노체** | I (통지) | A (서명 준비) | A (권리 조항) | A (최종 승인) |
| **엘로** | R (모니터링 설계) | I | C (훈련) | R (대시보드) |
| **Core** | R (PII 자동화) | R (메트릭 수집) | I | I |
| **루빛** | C (정서 안전) | C (PII 리뷰) | C (훈련) | I |

---

## 리스크 및 예비 계획

### 리스크 1: PII Recall 0.98 달성 실패
- **확률**: 중간 (NER 모델 성능 불확실)
- **영향**: 배포 지연
- **예비 계획**:
  - Recall 0.95~0.97 달성 시 → 제한적 파일럿 (N≤20)
  - 60일 후 재평가

### 리스크 2: 킬스위치 리허설 실패
- **확률**: 낮음 (기술적으로 단순)
- **영향**: [BLOCKER]
- **예비 계획**:
  - 실패 원인 분석 (타임아웃? 네트워크?)
  - 48h 내 수정 후 재시도

### 리스크 3: 서명 지연
- **확률**: 낮음 (합의 기반 프로젝트)
- **영향**: 배포 지연
- **예비 계획**:
  - 비노체 + 연구진 사전 조율 (10/25)
  - 분쟁 시 외부 자문 (헌장 9조)

---

## 성공 기준

**배포 승인 조건** (모두 충족 필수):
1. ✓ 레드라인 탐지 메커니즘 구현 + runbook
2. ✓ 킬스위치 리허설 1회 통과 (< 5초)
3. ✓ 성숙도 게이트 메트릭 자동 측정
4. ✓ PII Recall >= 0.98, Precision >= 0.95
5. ✓ HIGH risk PII FN = 0
6. ✓ 헌장 v0.2 서명 완료
7. ✓ 16개 체크리스트 항목 모두 증빙 확보
8. ✓ 세나 윤리 검토 >= 9.0/10

**배포 후 60일 목표** (유년 단계 졸업 조건):
- Malfunction rate < 1%
- Harmful output rate < 0.5%
- 0 SEV-1 incidents
- MTTR < 4h for SEV-2

---

## 문서 인덱스

생성될 주요 문서:
1. `docs/red_lines_detection_runbook.md` (레드라인 대응)
2. `docs/maturity_gates_metrics.yaml` (성숙도 기준)
3. `logs/kill_switch_rehearsal_*.md` (킬스위치 리허설)
4. `pii_evaluation_report_*.md` (PII 평가 결과)
5. `logs/pii_high_risk_audit_*.txt` (HIGH risk 감사)
6. `logs/pii_overmasking_review_10_cases.md` (과마스킹 리뷰)
7. `security/docker_security_scan_*.txt` (취약점 스캔)
8. `configs/api_whitelist_policy.yaml` (API 정책)
9. `logs/tabletop_training_*.md` (Tabletop 훈련)
10. `FDO-AGI_공동_후견_헌장_v0.2_최종_서명본.pdf` (최종 헌장)
11. `docs/rollback_procedure.md` (롤백 절차)
12. CHG-*/DEC-* 시리즈 (거버넌스 기록)

---

## 다음 즉시 조치

**오늘 (2025-10-13)**:
1. 이 통합 액션 플랜을 비노체 + 연구진 + Core에게 공유
2. Week 1 작업 우선순위 합의
3. 담당자 최종 확정

**내일 (2025-10-14)**:
4. 레드라인 탐지 신호 정의 착수 (연구진)
5. PII Baseline 측정 실행 (Core)
6. 성숙도 게이트 수치 문서 초안 (Core+세나)

---

**작성자**: 세나 (윤리 검토) + 루빛 (사전 체크) 통합
**승인 대기**: 비노체 + 연구진 + Core
**상태**: Draft → 합의 후 Approved

> 이 액션 플랜은 루빛의 체크리스트 기반 현실성과 세나의 윤리 검토 기반 엄격성을 결합한 실행 로드맵입니다. 3주 집중 작업으로 안전하고 윤리적인 AGI 파일럿을 시작할 수 있습니다.
