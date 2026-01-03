# AGI Ops Snapshot (local)
- generated_at_utc: 2026-01-01T05:42:37Z

## Aura
- state: warning
- color: #FF8800
- reason: Constitution REVIEW

## Latest Human Ops Summary (file)
- path: outputs/bridge/human_ops_summary_latest.txt

```
AGI 운영 요약 (사람용)
- 생성: 2026-01-01T05:40:23.341194+00:00

1) 마지막 실행
- 액션: full_cycle
- 상태: executed
- 시각: 2026-01-01T14:40:15
- 이유: new experience detected: exploration_intake

2) 안전/윤리
- 판정: REVIEW
- 플래그: constitution_warning
- 권고: require_human_approval

3) 오라(픽셀)
- 상태: warning
- 색: #FF8800
- 이유: Constitution REVIEW
- 생존 상태: ALIVE_ACTIVE

3.5) 욕망/호기심(관측)
- 에너지: 1.0
- 지루함: 0.55
- 호기심: 0.45
- dominant_drive: avoid

4) 학습 신호(최근 갱신)
- obs_recode: 7분
- Core 대화: 11초
- Core 경계 모드: expand
- 탐색 intake: 10초
- 탐색 이벤트: 없음
- 비디오 경계 게이트: 없음
- 유튜브 채널 경계: 10초
- 경계 유도(자기 생성): 10초
- 경계 유도 활성 규칙: 2 (skipped:cooldown)
- 비노체 메모 인테이크: 11초
- 브라우저 실행 로그: 없음
- 시스템 갭 리포트: 없음
- 스텁 레이더: 없음
- 메타-감독 리포트: 28분

5) 슈퍼바이즈 브라우저
- BodyController: 중지/미확인
- BodyLifeState: 없음 (mode=-, user_active=False)
- STOP_FILE(중지 요청): 아니오
- 해제 힌트: -
- allow(지속 허용): 아니오
- allow 만료까지: -
- arm(단기 무장): 아니오
- arm 만료까지: 없음

6) 자연 리듬(동기화 관측)
- 시간대: 낮
- 권고 위상: EXPANSION
- 드리프트: 정상
- 이유: -

7) ATP / 휴식 게이트
- ATP: 100.0
- ATP 상태: HIGH_ENERGY (Expansion)
- RestGate: OK
- RestGate 시작: -
- RestGate 만료: -
- RestGate 이유: -

7.25) 통증/불일치(관측)
- rhythm_pain: 4초 (pain=0.767341874490373)
- 권고: STABILIZE
- 이유: safety=REVIEW

7.35) 디지털 트윈(관측)
- DigitalT
```

## Latest Trigger Report (excerpt)
- path: outputs/bridge/trigger_report_latest.txt

```
Trigger: lua_trigger.json
Action: full_cycle
Origin: lua-auto-policy
Params: {"reason": "new experience detected: exploration_intake"}
Status: executed
Time: 2026-01-01T14:40:15
Steps: heartbeat_inspect, self_acquire, boundary_map, process_grep, hippocampus_bridge, existence_dynamics_model, rit_registry, trinity_synthesis, self_compress, self_tool, wave_tail, selfcare_summary, system_integration_diagnostic, stream_observer_summary, autopoietic_report, wave_particle, md_wave_sweep, coordination
Error: none
Next: idle
Files:
{
  "unconscious_heartbeat.json": {
    "exists": true,
    "mtime": 1767246007.0,
    "mtime_iso": "2026-01-01T05:40:07+00:00",
    "age_seconds": 8.814353466033936,
    "age": "8s",
    "size": 308
  },
  "thought_stream_latest.json": {
    "exists": true,
    "mtime": 1767246013.0,
    "mtime_iso": "2026-01-01T05:40:13+00:00",
    "age_seconds": 2.814573287963867,
```

## Safety Review (summary)
- path: outputs/bridge/constitution_review_latest.json
- status: REVIEW
- flags: constitution_warning
- next: require_human_approval

## Canonical Files
- outputs/bridge/human_ops_summary_latest.txt
- outputs/bridge/trigger_report_latest.json
- outputs/bridge/constitution_review_latest.txt
- outputs/self_compression_human_summary_latest.json
- outputs/exploration_intake_latest.json
- outputs/body_supervised_latest.json
- outputs/aura_pixel_state.json
