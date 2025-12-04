# AGI 프롬프트 압축 최적화 - 변경 사항 요약

## 변경된 파일

### 1. personas/synthesis.py

**변경 내용**: 기본 압축 임계값 1200 → 900

```python
# 변경 전
section_max = int(os.environ.get("SYNTHESIS_SECTION_MAX_CHARS", "1200"))

# 변경 후  
section_max = int(os.environ.get("SYNTHESIS_SECTION_MAX_CHARS", "900"))
```

**근거**: 3점 스윕 실험 결과, 900에서 합성 성공률 2배 향상(0.5→1.0), 추론시간 19% 단축

---

### 2. docs/AGI_USER_GUIDE.md

**변경 내용**: 프롬프트 압축 섹션에 실험 데이터 및 권장값 추가

**추가된 내용**:

- 실험 결과(2025-10-26) 섹션
  - synthesis 성공률: 0.5 → 1.0 (100%, 2배 향상)
  - 평균 추론 시간: 21.4s → 17.3s (19% 단축)
  - 평균 프롬프트 크기: 1569자 → 1175자 (25% 축소)
- 권장값: **900** (최적 균형점)
- 극단 압축 시 800까지 테스트 가능하다는 가이드라인

---

## 검증 완료

✅ **엣지 케이스 테스트**: ALL PASSED  
✅ **단일 프로파일 실행**: wall_clock 70.85s, synthesis_success_rate 1.0  
✅ **문서 업데이트**: 실험 근거 명시

---

## 영향 범위

- **기존 동작**: 환경변수 미설정 시 900 적용 (이전 1200)
- **명시적 설정**: `SYNTHESIS_SECTION_MAX_CHARS=1200` 등으로 여전히 override 가능
- **성능**: 기본값 사용 시 합성 성공률 및 속도 개선

---

## 배포 권장사항

1. 프로덕션 배포 전 스테이징 환경에서 24시간 모니터링
2. 합성 성공률 메트릭 추적 (목표: 0.9+)
3. 평균 추론 시간 추적 (목표: 20s 이하)
4. 이슈 발생 시 `SYNTHESIS_SECTION_MAX_CHARS=1200`로 롤백 가능

---

**작성자**: 깃코  
**작성일**: 2025-10-26 03:15

---

## 추가 개선 (2025-10-26)

- 동적 압축(Dynamic Compaction) 도입: `SYNTHESIS_DYNAMIC_COMPACTION=1` 기본 활성, `SYNTHESIS_USER_PROMPT_TARGET_CHARS` 기준으로 섹션별 최대 길이 자동 스케일링
- 재시도/백오프 추가: `SYNTHESIS_RETRY_MAX`(기본 1), `SYNTHESIS_RETRY_BACKOFF_SEC`(기본 2.0), `SYNTHESIS_RETRY_COMPACTION_STEP`(기본 200)
- 타임아웃 설정 지원: `SYNTHESIS_TIMEOUT_SEC`(기본 30) → LLM HTTP 호출에 전달
- Ledger 스키마 확장: persona_llm_start/end 이벤트에 `attempt` 필드 추가(재시도 가시성)
