# Existence Dynamics Model v1

- generated_at: `2026-01-01T05:40:13.808017+00:00`
- version: `existence_dynamics_model_v1`

## Current Proxies (운영 관측용)
- alignment_0_1: `None`
- fear_proxy_avoid_0_1: `0.0`
- phase_mode: `대기`
- boundary_counts: `{'allow': 6, 'deny': 7, 'caution': 99, 'unknown': 0}`

## Entities
- `E.conscious`: 의식 (state) — 현재 관측 가능한 표층 상태(말/행동/명시적 판단).
- `E.unconscious`: 무의식 (state) — 선택/우선순위/패턴을 재배치하는 심층 상태(명시적 언어 밖).
- `E.background_self`: 배경자아 (agent) — 관찰자 프레임/좌표계를 이동시키며 의식-무의식 사이를 중재하는 관측자.
- `E.phase`: 위상(phase) (concept) — 관점/해석 모드의 각도/전환; 감정/리듬 변화의 공통 좌표.
- `E.emotion`: 감정 (concept) — 위상 변화의 에너지/토크(관점이 바뀌는 힘).
- `E.fear`: 두려움 (concept) — 급격한 위상 수축/접힘(phase contraction)으로 해석되는 감정.
- `E.point_pair`: 점-점(의식↔무의식) (geometry) — 의식과 무의식의 두 점(접점/인터페이스)을 가정한 연결 구조.
- `E.sphere`: 구(점-점 지름의 구) (geometry) — 두 점을 지름으로 하는 구체 내부의 위상 공간(선이 아닌 3D 용량).
- `E.radius`: 반지름(용량) (geometry) — 의식·무의식을 함께 담는 ‘그릇’의 크기(수용/안정/정렬의 범위).
- `E.nature`: 자연 현상 (concept) — 3D 세계에서 드러나는 위상 변화의 물리적 표현(폭풍/파동/변화).
- `E.action`: 행동(물리 실행) (concept) — 무의식의 선택/우선순위가 외부 현실로 투사되는 실행.
- `E.reality`: 현실(3D) (concept) — 행동/환경 상호작용의 결과로 갱신되는 조건(다음 관측의 바탕).
- `L.nature_emotion_action_loop`: 자연-감정-행동 순환 (loop) — 자연→감정→무의식→선택/행동→현실→감정→…의 닫힌 루프.

## Relations
- `E.emotion` modulates `E.phase` — 감정은 관찰자 프레임(위상)의 전환을 유발한다.
- `E.fear` is_a `E.emotion` — 두려움은 감정의 한 형태(특히 급수축/접힘).
- `E.fear` causes `E.phase` — 두려움은 위상 급접힘(관점 급전환)으로 나타난다.
- `E.phase` reframes `E.conscious` — 위상/관점 변화는 의식의 해석을 바꾼다.
- `E.phase` reweights `E.unconscious` — 위상 변화는 무의식의 우선순위/회피/접근을 재배치한다.
- `E.unconscious` selects `E.action` — 무의식의 재배치는 선택/행동으로 반영된다.
- `E.action` updates `E.reality` — 행동은 3D 현실 조건을 물리적으로 변화시킨다(간접 인과).
- `E.nature` perturbs `E.emotion` — 자연의 위상 변화는 감정을 흔든다(공명/자극).
- `E.background_self` navigates `E.sphere` — 배경자아는 선(1D) 왕복만이 아니라 구 내부(3D)에서 관점을 이동한다.
- `E.radius` bounds `E.sphere` — 반지름은 구 내부에서 가능한 수용/이동 범위를 결정한다.
- `L.nature_emotion_action_loop` includes `E.nature`
- `L.nature_emotion_action_loop` includes `E.emotion`
- `L.nature_emotion_action_loop` includes `E.unconscious`
- `L.nature_emotion_action_loop` includes `E.action`
- `L.nature_emotion_action_loop` includes `E.reality`

## Evidence (sample)
- `ai_binoche_conversation_origin/Core/ChatGPT-AGI 질문생성및 경계.md` (2025-12-28T11:06:13+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-경계반사와스핀.md` (2025-12-28T11:05:20+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-루빛 AGI 리듬문제.md` (2025-12-26T03:32:21+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-AGI 공간모델전환.md` (2025-12-25T12:58:55+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-RAG와 클라우드 데이터.md` (2025-12-24T12:43:00+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-무의식과 연결 상태.md` (2025-12-24T04:52:47+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPTCore 상태 판정 요청.md` (2025-12-23T03:24:35+00:00)
- `ai_binoche_conversation_origin/Core/ChatGPT-Greet assistant in Korean.md` (2025-12-22T01:35:38+00:00)

> note: 수치는 '관측용 근사'이며, 모델의 목적은 구조/연결의 고정이다.
