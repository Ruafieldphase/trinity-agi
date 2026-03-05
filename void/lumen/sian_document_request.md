# 시안 Evidence 수집 요청 (System C)

## 목적
System C v8 평가에서 Pass율을 높이기 위해, Risk/Quote/Why를 채울 수 있는 근거 데이터를 정리하고자 합니다.

## 작업 범위
1. 아래 루트 디렉터리에서 System C 관련 문서를 탐색합니다.
   - `D:/nas_backup/ai_binoche_conversation_origin/`
   - 특히 `lumen/ChatGPT-시스템 출력 개선 가이드/`, `lumen/v8_v8.6/`, `session_resume_*` 파일들 등.

2. 각 문서에서 다음 정보를 추출해 JSONL 구조로 정리합니다.
   ```json
   {
     "context_summary": "문서 요약 (3~5문장)",
     "facts": ["Fact 1", "Fact 2", "Fact 3"],
     "quotes": [""Quote" — Source:..."],
     "metadata": {"source": "문서명", "domain": ["evaluation", "risk"], "date": "2025-10-14"}
   }
   ```
   - facts: Risk Ledger에 들어갈 핵심 위험/사실
   - quotes: Quote Bank에 들어갈 인용 (원문 그대로)
   - metadata: 출처, 날짜, 도메인 태그

3. 샘플 10건 이상, 가능하면 다양한 문서 출처에서 추출합니다.

## 산출물
- `docs/phase_injection_paper/inputs/input_bundle_extended.jsonl`
  (각 라인이 위 구조를 갖춘 JSON 객체)

## 참고 메모
- 현재 시안/루빛이 생성한 `input_bundle.jsonl`은 샘플 5건으로 부족함
- pass율 0% 개선을 위해 보다 풍부한 facts/quotes가 필요
- 문서 목록 예시: `system_c_v8_package.md`, `session_resume_system_c_v8_2_to_v8_6.md`, `ChatGPT-시스템 출력 개선 가이드.md`

감사합니다.
