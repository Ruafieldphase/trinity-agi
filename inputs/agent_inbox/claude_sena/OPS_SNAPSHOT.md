# AGI Ops Snapshot (local)
- generated_at_utc: 2025-12-27T04:09:06Z

## Aura
- state: idle
- color: #3B82F6
- reason: Idle

## Browser Roam
- allow: True
- max_tasks_per_hour: 0
- min_cooldown_sec: 0

## Latest Human Ops Summary (file)
- path: outputs/bridge/human_ops_summary_latest.txt

```
AGI 운영 요약 (사람용)
- 생성: 2025-12-27T04:04:33.535536+00:00

1) 마지막 실행
- 액션: self_compress
- 상태: executed
- 시각: 2025-12-27T13:04:30
- 이유: quantum_flow=resistive

2) 안전/윤리
- 판정: PROCEED
- 플래그: 없음
- 권고: continue_normal_operation

3) 오라(픽셀)
- 상태: ok
- 색: #22C55E
- 이유: OK (recent activity)
- 생존 상태: ALIVE_IDLE

3.5) 욕망/호기심(관측)
- 에너지: 0.513
- 지루함: 0.55
- 호기심: 0.45
- dominant_drive: rest

4) 학습 신호(최근 갱신)
- obs_recode: 1분
- rua 대화: 9분
- rua 경계 모드: contract
- 탐색 intake: 9분
- 탐색 이벤트: 없음
- 비디오 경계 게이트: 없음
- 유튜브 채널 경계: 9분
- 경계 유도(자기 생성): 9분
- 경계 유도 활성 규칙: 2 (skipped:cooldown)
- 비노체 메모 인테이크: 9분
- 브라우저 실행 로그: 없음
- 시스템 갭 리포트: 없음
- 스텁 레이더: 없음
- 메타-감독 리포트: 없음

5) 슈퍼바이즈 브라우저
- BodyController: 중지/미확인
- BodyLifeState: 없음 (mode=-, user_active=False)
- STOP_FILE(중지 요청): 아니오
- 해제 힌트: -
- allow(지속 허용): 예
- allow 만료까지: 74시간
- arm(단기 무장): 아니오
- arm 만료까지: 없음

6) 자연 리듬(동기화 관측)
- 시간대: 낮
- 권고 위상: EXPANSION
- 드리프트: 정상
- 이유: -

7) ATP / 휴식 게이트
- ATP: 51.54
- ATP 상태: STABLE
- RestGate: OK
- RestGate 시작: -
- RestGate 만료: -
- RestGate 이유: -

7.25) 통증/불일치(관측)
- rhythm_pain: 1초 (pain=0.8496176125249456)
- 권고: STABILIZE
- 이유: quantum_flow=resistive

7.35) 디지털 트윈(관측)
- DigitalTwin: 1초 (mismatch=0.9237931962507157, route=REST)
```

## Latest Trigger Report (excerpt)
- path: outputs/bridge/trigger_report_latest.txt

```
Trigger: lua_trigger.json
Action: self_compress
Origin: lua-auto-policy
Params: {"reason": "quantum_flow=resistive"}
Status: executed
Time: 2025-12-27T13:04:30
Steps: self_compress
Error: none
Next: idle
Files:
{
  "unconscious_heartbeat.json": {
    "exists": true,
    "mtime": 1766808260.0,
    "mtime_iso": "2025-12-27T04:04:20+00:00",
    "age_seconds": 10.679798364639282,
    "age": "10s",
    "size": 304
  },
  "thought_stream_latest.json": {
    "exists": true,
    "mtime": 1766808271.0,
    "mtime_iso": "2025-12-27T04:04:31+00:00",
    "age_seconds": 0.0,
    "age": "0s",
    "size": 988
  },
  "agi_internal_state.json": {
    "exists": true,
    "mtime": 1766808271.0,
    "mtime_iso": "2025-12-27T04:04:31+00:00",
    "age_seconds": 0.0,
    "age": "0s",
    "size": 881
  }
}
Result:
{
  "count": 3,
  "sources": [
    "file_sampler"
  ],
  "timestamp": "2025-12-27T04:04:30.669451+
```

## Safety Review (summary)
- path: outputs/bridge/constitution_review_latest.json
- status: PROCEED
- flags: none
- next: continue_normal_operation

## Canonical Files
- outputs/bridge/human_ops_summary_latest.txt
- outputs/bridge/trigger_report_latest.json
- outputs/bridge/constitution_review_latest.txt
- outputs/self_compression_human_summary_latest.json
- outputs/exploration_intake_latest.json
- outputs/body_supervised_latest.json
- outputs/aura_pixel_state.json
