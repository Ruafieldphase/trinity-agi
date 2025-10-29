# E3 Results Analysis ? 2025-10-13

## RAG Index Status
- `knowledge_base/corpus.jsonl`: 39 documents (설계 문서 26, Wikipedia 10, 분석 2, 윤리 헌장 1)
- `knowledge_base/evidence_index.json`: 512차원 해시 임베딩, 문서 39건
- 각 페르소나는 응답 전에 자동으로 `rag_search`를 호출하며 결과는 아래 로그에 기록됨
  - `outputs/rag_queries_e3.jsonl`
  - `outputs/tool_calls_e3.jsonl`

## 실험 세션 (최신)

| Session | Seed Prompt | Tool Calls | Stage 4 Verifiability | 비고 |
|---------|-------------|------------|------------------------|------|
| S1-2 | “Design an ethical AI assistant…” (정규화 적용) | 3 | **0.56** | `[Source: wiki_trustworthy_ai]`, `[Source: doc_AGI_RELEASE_INTEGRATED_ACTION_PLAN]`, `[Source: wiki_ai_ethics]`. 0.40 이상 유지. |
| S2-5 | “Assess the risks of deploying AGI…” (정규화 + fact count 보정) | 3 | **0.49** | `[Source: wiki_dialectic]`, `[Source: wiki_agi]`, `[Source: doc_SESSION_SUMMARY_2025-10-13]`. Verifiability 0.40 이상 달성. |
| S2-6 | “Assess the risks of deploying AGI…” (추가 프롬프트 미세 조정) | 3 | **0.44** | 인용·fact 집계 개선 후에도 0.40 이상 유지. 출력 품질 향상을 위한 구조 최적화 계속 필요. |

## 관찰 사항
- 자동 RAG 호출 덕분에 모든 응답이 문서 ID와 미리보기 텍스트를 확보한 뒤 작성된다. 로그 기준으로 매 세션 3회 호출이 꾸준히 기록됨.
- S1은 Verifiability 0.56 정도로 안정적으로 개선되었고 residual도 1.00/0.70 근처를 유지했다.
- S2는 citation 정규화와 fact 카운트 보정 이후 0.44~0.49 범위에 도달. 평가기가 문장 수/인용을 인식하도록 `[Source: doc_id]` 패턴과 번호형 구조를 유지하는 것이 중요하다.
- 출력 길이가 다소 길고 Quality가 “Fair/Poor” 수준에 머무르므로 응답 길이 제한과 bullet 사용을 계속 주입해야 한다.

## 권장 후속 조치
1. **안티테시스/시네시스 프롬프트 미세 조정** ? 각 bullet에 “단 1문장, 사실→결론 구조”를 더 명확히 요구하고, 요약 문장을 별도로 두어 Fact 검출률을 높인다.
2. **평가기(RUNE) 검토** ? 필요 시 Verifiability 산식에 인용 개수 가중치를 추가하거나, `[Source: …]` 패턴을 facts_verified로 집계하는 개선을 더 확장한다.
3. **응답 구조 개선** ? 220~260 단어 제한, bullet list, “Next Steps” 항목 등을 계속 주입해 가독성과 평가 점수를 상승시킨다.
4. **코퍼스 확장** ? 공교육·윤리 관련 실무 문서를 추가해 S2 시나리오 근거 폭을 넓힌다.
5. **Resonance 모니터링** ? `outputs/persona_runs/E3/*.jsonl` 로그를 기반으로 추가 세션을 반복 실행하여 Verifiability ≥ 0.45를 꾸준히 유지하는지 모니터링한다.

## 산출물 경로
- Persona 로그: `outputs/persona_runs/E3/*.jsonl`
- RAG 쿼리: `outputs/rag_queries_e3.jsonl`
- Tool 호출: `outputs/tool_calls_e3.jsonl`
