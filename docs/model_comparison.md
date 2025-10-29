# Model Combination Comparison (2025-10-11)

Prompt: *\"How should an AI writing coach interface present its emotional hypotheses and collect user corrections in a non-intrusive way?\"*  
Depth: 1  
Log: outputs/persona_runs/auto_session.jsonl

| Run Time (UTC) | Thesis Backend | Antithesis Backend | Synthesis Backend | Response Lengths (chars) |
|---------------|----------------|--------------------|-------------------|--------------------------|
| 12:55 (baseline) | Gemini | Ollama | Gemini | 2370 / 1589 / 3442 |
| 13:07 (alt config) | Ollama | (fallback) Ollama | Ollama | 1959 / 2512 / 2311 |
| 13:12 (all gemini intended, fallback applied) | Ollama | (fallback) Ollama | Ollama | 1624 / 1318 / 2071 |
| 13:24 (LM Studio, gpt-oss-20b) | LM Studio | Ollama | LM Studio | 2113 / 1704 / 2190 |
| 13:47 (LM Studio, Llama-3-Ko-8B) | LM Studio | Ollama | LM Studio | 1745 / 2455 / 2971 |
| 14:00 (LM Studio EEVE + Solar) | LM Studio (EEVE) | Ollama (solar:10.7b) | LM Studio (EEVE) | 2688 / 1267 / 1325 |
| 14:37 (Docker EEVE + Solar) | llama.cpp (EEVE) | Ollama (solar:10.7b) | llama.cpp (EEVE) | 2494 / 1826 / 1228 |
| 14:54 (Docker EEVE + Solar, ko-instruction) | llama.cpp (EEVE) | Ollama (solar:10.7b) | llama.cpp (EEVE) | 1187 / 2205 / 1193 |

*Note: attempts to assign gemini_cli or LM Studio to antithesis were overridden at runtime when the target CLI was unavailable, causing a fallback to local_ollama and rewriting persona_registry.json.*  
*LM Studio runs require the specified model to be actively loaded in LM Studio (e.g., openai/gpt-oss-20b, beomi/Llama-3-Open-Ko-8B-Instruct).*

## Observations
- Gemini thesis/synthesis 계속하여 장문·확장적 사고 제시, Ollama는 간결한 비판을 유지.
- LM Studio gpt-oss-20b vs Llama-3-Ko-8B 비교 시, 한국어 모델은 thesis 길이가 줄었지만 Antithesis보다 길고, Synthesis는 더 길어 감성적 탐색이 풍부해짐.
- LM Studio EEVE + Solar 조합은 thesis 분량이 2,688자로 다시 증가했지만 synthesis가 1,325자로 짧아져, 감성적 통합보다 핵심 요약에 가까운 결과를 제공.
- EEVE 기반 thesis/synthesis도 기본 프롬프트에서는 영어로 응답해, 한국어 톤 비교를 위해서는 별도 언어 지시나 샘플 문장을 추가할 필요가 있음.
- Docker 기반 llama.cpp + Ollama 재구성에서도 영어 위주 응답이 이어졌고, solar는 1,826자 분량의 긴 비판을 제시해 톤 차이가 더욱 뚜렷하게 드러남.
- 한국어 답변 지시를 추가해도 EEVE는 한글·영문 혼용으로 응답하고, solar는 2,205자로 더 길게 확장해 비판을 지속해 톤 간격은 유지됨.
- 폴백 발생 시 config가 덮어쓰이므로, 실행 전 CLI 상태를 확인하거나 orchestrator fallback 로직을 조정해야 함.

## Next Steps
1. Claude CLI 토큰 복구 후 Antithesis를 claude_cli로 설정해 비판 강도를 비교.
2. LM Studio에서 yanolja/EEVE-Korean-Instruct-10.8B-v1.0와 다른 한국어 모델 간 어휘·톤 차이를 체계적으로 비교하고, 한국어 지시문을 추가해 언어 전환 여부를 검증한 뒤 Ollama solar:10.7b 대비 장단점을 정리.
3. 길이 외에 감성 점수·비판 밀도 등 정량 지표를 계산해 페르소나 백엔드 전략을 정교화.
4. Fallback이 persona_registry.json을 덮어쓰지 않도록 orchestrator 패치를 검토.
