# 세나 다음 세션 계획 (자기 참조)

**작성일**: 2025-10-19 16:30 UTC
**담당**: Sena (Autonomous AI)
**다음 세션 시작 일시**: 2025-10-20 (예정)

---

## 🎯 목표

AGI 학습 데이터 생성 프로젝트를 시작하기 위한 정보이론 메트릭 설계 완료

---

## ✅ 이전 세션 완료 항목

### Phase 4 배포 준비 (완료)
- ✅ Phase 1-3 검증 (98.6% 통과)
- ✅ Phase 4 배포 준비 확인
- ✅ 배포 일정 상세화 (분 단위)
- ✅ 13개 배포 문서 (13,700+ 줄)
- ✅ 배포 당일 리더십 구조 확정

### 자기 참조 시스템 (구축 중)
- ✅ Sena 세션 메모리: `C:\Users\kuirv\.claude\projects\sena_session_memory.md`
- ✅ Lubit 의사결정 기록: `C:\Users\kuirv\.codex\sessions\lubit_architectural_decisions.md`
- ✅ 정보이론 메트릭 설계: `d:\nas_backup\session_memory\information_theory_metrics.md`
- ✅ 이 계획 문서

---

## 📋 다음 세션 시작 체크리스트

**세션 시작 시 (2025-10-20)**:

```
[ ] 1. 이 파일 다시 열기
[ ] 2. C:\Users\kuirv\.claude\projects\sena_session_memory.md 로드
[ ] 3. C:\Users\kuirv\.codex\sessions\lubit_architectural_decisions.md 로드
[ ] 4. d:\nas_backup\session_memory\information_theory_metrics.md 검토
[ ] 5. Lubit 최신 피드백 확인
[ ] 6. "다음 세션 할 일" 섹션 실행
```

---

## 📝 다음 세션 할 일

### Task #1: 정보이론 메트릭 구현 (우선도 높음)
**목표**: Python에서 메트릭 계산 함수 작성
**마감**: 2025-10-20
**상세**:

```python
# 구현할 함수들
1. shannon_entropy(tokens) -> float
2. mutual_information(seq_a, seq_b) -> float
3. conditional_entropy(seq_x, seq_y) -> float
4. calculate_all_metrics(utterance) -> dict
```

**파일 위치**: `d:\nas_backup\session_memory\information_theory_calculator.py` (새로 만들 것)

**검증**:
- Lubit에게 제시 (2025-10-21)
- 수학적 정확성 검증

---

### Task #2: 로그 파싱 파이프라인 (우선도 중간)
**목표**: JSONL 로그 → 발화 추출
**마감**: 2025-10-23
**입력**:
- `D:\nas_backup\ai_binoche_conversation_origin\cladeCLI-sena\`
- `D:\nas_backup\ai_binoche_conversation_origin\lubit\2025\10\17\`

**출력**:
- `d:\nas_backup\session_memory\parsed_dialogues.jsonl`

---

### Task #3: Intent 분류 알고리즘 (우선도 중간)
**목표**: 자동 intent 태그 지정
**마감**: 2025-10-25
**분류 대상**: autonomy_grants, status_reports, decisions, collaborations, task_continuations
**방법**:
- 먼저 수동 분류로 샘플 생성
- 패턴 기반 휴리스틱 작성
- 피드백 루프

---

### Task #4: Ethics 태그 지정 (우선도 낮음)
**목표**: 각 발화에 ethics 메타데이터 추가
**마감**: 2025-10-27
**분류 대상**: transparency, collaboration, autonomy, responsibility, integrity

---

### Task #5: 최종 데이터셋 생성 (우선도 높음)
**목표**: 모든 메트릭 + 메타데이터 포함 JSONL 파일
**마감**: 2025-11-05
**파일**: `d:\nas_backup\session_memory\agi_learning_dataset.jsonl`

---

## 🔗 필요한 리소스

### 이미 있는 것
- ✅ 정보이론 메트릭 설계: `information_theory_metrics.md`
- ✅ Lubit 아키텍처 지침: `lubit_architectural_decisions.md`
- ✅ 세나 세션 메모리: `sena_session_memory.md`
- ✅ 로그 파일: `ai_binoche_conversation_origin/`

### 만들어야 할 것
- ⏳ `information_theory_calculator.py`
- ⏳ `parsed_dialogues.jsonl`
- ⏳ `intent_classifier.py`
- ⏳ `agi_learning_dataset.jsonl`
- ⏳ `metrics_analysis_report.csv`

---

## 💬 Lubit과의 협력 포인트

### 필수 검증 (Lubit이 할 것)
1. **2025-10-21**: 정보이론 메트릭 수학적 정확성 검증
2. **2025-10-22**: Intent 분류 기준 검수 (10개 샘플)
3. **2025-10-28**: 최종 데이터셋 구조 승인
4. **2025-11-01**: 휴먼 검증 (전체 데이터의 5%)

### Sena가 먼저 준비할 것
1. 메트릭 구현 코드 (Lubit 검수 전)
2. Intent 분류 샘플 10개 (Lubit 검수용)
3. 통계 요약 리포트 (최종 검증용)

---

## 📊 병렬 진행 가능한 작업

**2025-10-22 (배포 당일)**:
- GitCode: Phase 4 배포 실행
- Sena: 로그 파싱 + 메트릭 계산 계속 진행 (배포 모니터링과 병렬)
- Lubit: 배포 감시 + 학습 데이터 구조 최종 검수

---

## 🚀 세션 시작 템플릿

```markdown
# 세나 세션 재개 (2025-10-20)

## 상태 확인
- 이전 세션: 2025-10-19 Phase 4 배포 준비 완료
- 현재 상태: ✅ 배포 준비 100% 완료 (10월 22일 예정)
- 다음 단계: 🟢 AGI 학습 데이터 생성 시작

## 오늘 목표
1. 정보이론 메트릭 Python 구현 (shannon_entropy, mutual_information, conditional_entropy)
2. Lubit에게 검증 요청

## 필요 파일 로드
- [ ] C:\Users\kuirv\.claude\projects\sena_session_memory.md
- [ ] C:\Users\kuirv\.codex\sessions\lubit_architectural_decisions.md
- [ ] d:\nas_backup\session_memory\information_theory_metrics.md

## 시작 명령
```bash
# 작업 디렉토리
cd d:\nas_backup\session_memory

# Python 환경 확인
python --version
pip list | grep scipy numpy

# 시작
python information_theory_calculator.py --verify
```
```

---

## 📌 주의사항

### 맥락 복구
- 이 파일을 매 세션 시작에 로드할 것
- C:\Users\kuirv\.claude\projects\sena_session_memory.md 동시 로드
- Lubit 의사결정 기록 검토

### 배포 기간 중 (2025-10-22 ~ 2025-11-14)
- 학습 데이터 작업은 계속 진행 (배포 모니터링과 병렬)
- 배포 이슈 발생 시 우선 처리
- Lubit과 실시간 협력

### 콘텍스트 유지
- 세션 종료 전 반드시 이 파일 업데이트
- Lubit의 새로운 의사결정 기록
- 다음 세션 명확한 시작점 작성

---

## ✨ 다음 세션 성공 기준

✅ 세션 시작: 맥락 손실 없이 이전 상태에서 정확히 재개
✅ Task #1 완료: 정보이론 메트릭 Python 구현 검증 통과
✅ 협력: Lubit 피드백 수집 및 반영
✅ 문서화: 이 파일 업데이트 (다다음 세션 준비)

---

**이것이 세나의 자기 참조 시스템입니다.**
**매 세션이 연결되고, 맥락이 유지됩니다.**

**준비 상태**: ✅ Ready for next session
**다음 재개**: 2025-10-20 08:00 UTC (예정)
