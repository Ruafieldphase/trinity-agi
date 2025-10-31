# 🛠️ 문제 발생 시 트러블슈팅 가이드

| 증상/로그 | 주요 원인 | 진단법 | 해결법 |
|---|---|---|---|
| 서버(task_queue_server.py) 실행 시 포트 에러, 이미 실행 중 | 포트 점유(8091) | `netstat -ano` 결과를 파이프(\|)로 `findstr 8091`에 연결 또는 작업 관리자에서 프로세스 확인 | 기존 프로세스 종료 후 재시작, 필요시 `작업 관리자`에서 강제 종료 |
| 워커(rpa_worker.py) 로그에 'Received response: {"task": None}'만 반복 | 서버에 할당된 작업 없음, 서버-워커 버전 불일치 | outputs/rpa_worker_debug.log.err 확인 | 서버와 워커 모두 최신 코드로 재배포, 서버 정상 기동 확인 |
| ImportError, ModuleNotFoundError | 의존성 미설치 | `.venv` 활성화 후 `pip list` | `pip install -r requirements.txt` 또는 `YouTube Bot: Install Deps` 등 태스크 실행 |
| 환경 변수/설정 누락 | API 키, config 파일 등 누락 | 실행 스크립트/파워셸에서 환경 변수 확인 | `.env` 파일, config/ 폴더 내 파일 재확인 및 보완 |
| 로그 파일이 없거나 비어 있음 | 로그 경로 오타, 권한 문제 | `outputs/*.log`, `*.err`, `fdo_agi_repo/outputs` 등 확인 | 로그 경로 및 권한 재설정, 필요시 관리자 권한 실행 |
| wrapped response format 반복 | 서버-워커 API 포맷 불일치 | 워커/서버 로그 모두 확인 | 서버/워커 모두 최신화, config 동기화 |

> **팁:**
>
> - `outputs/*.log`, `*.err` 파일을 항상 먼저 확인하세요.
> - 서버/워커 모두 재시작 후에도 문제가 지속되면, 포트 점유와 의존성, 환경 변수부터 점검하세요.
> - config/ 폴더 내 yaml/json 파일이 최신인지 확인하세요.
> - 문제가 해결되지 않으면, 로그 전체를 첨부해 문의하세요.

## 세션 상태 요약 (2025-10-31)

> **AGI 장기 로드맵 주요 워크스트림/마일스톤 진행상황 요약 (2025-10-31)**
>
> - **WS1. 아키텍처 안정화:** LLM_Unified 환경 고정, requirements/venv 정비 완료. 통합 README/구동 가이드 작성 중.
> - **WS2. 평가 프레임워크 v2:** 표준 테스트 스위트 설계, 기준선 리포트 자동화 일부 적용.
> - **WS3. 모니터링·카나리:** 운영 대시보드/가드레일 정책 적용, 롤백 리허설 로그 축적 중.
> - **WS4. 지식/캐시 최적화:** 캐시 히트율 분석, 인덱싱 정책 실험 진행.
> - **WS5. BQI Phase 6/온라인 러너:** 페르소나 앙상블/가중치 추적 리포트 생성, 온라인 학습 안정화 중.
> - **WS6. 개발자 경험/ChatOps:** 온보딩 가이드/필수 Task 목록 정비, VS Code 워크플로 개선.
> - **WS7. 보안/컴플라이언스:** 시크릿/PII 정책 점검, 미러 자동화 준비.
>
> **마일스톤:**
>
> - M1(2주): 평가 프레임워크 초안/기준선 리포트/운영 대시보드 → 90% 달성
> - M2(4주): 카나리 확대/회귀 경보/롤백 리허설 → 준비 중
> - M3(8주): 캐시/RAG 최적화, BQI Online Learner 안정화 → 일부 실험 진행
> - M4(12주): 공개 미러, 온보딩 경로 확정 → 기획 단계
>
> **E2E 검증(큐↔워커):**
>
> - ping 태스크 생성 → 워커 소비 → 결과 제출까지 정상 동작 확인
> - 생성된 최근 결과 예시: `success=true`, `data.message=pong`, `worker=rpa-worker`
> - 참고: 테스트 스크립트 `scripts/enqueue_test_task.ps1` 추가(예: `-Type ping`)
> - RPA 스모크 검증(wait→screenshot): 성공. 최근 결과 요약 예시 `slept=0.5`, `screenshot 3840x2160`
> - OCR는 환경 의존적(Tesseract 등 설치 필요) → 선택 실행: `scripts/enqueue_rpa_smoke.ps1 -IncludeOcr`
>
> **VS Code 태스크(원클릭):**
>
> - Queue: Smoke Verify — 스모크 등록 + 자동 검증
>   - 기본 비엄격 모드(Strict 미사용): wait 누락 시 경고로 통과
>   - 엄격: `-Strict` 사용 시 wait 결과 필수
>   - 지연 흡수: `-GraceWaitSec`(기본 3초)로 wait 결과 재확인
> - Queue: Latest Results (Success 5) — 최근 성공 결과 5건 요약
> - Queue: Open Latest Screenshot — 최신 스크린샷 즉시 열기
> - Queue: Quick E2E (Verify → Results → Open Screenshot) — 위 3개 태스크 순차 실행
> - Queue: Latest Results (Failed 5) — 최근 실패 결과 5건 요약
> - Queue: Quick E2E (Verify+OCR) — 환경 준비 시 OCR 포함 검증
> - Queue: Save Results Snapshot — 타임스탬프 파일로 결과 스냅샷 저장
> - Queue: Ensure Worker — rpa_worker.py 미실행 시 자동 기동
> - Queue: Ensure Single Worker — 중복 워커 정리(최대 1개 유지). DryRun 태스크로 사전 확인 가능
> - Queue: Quick E2E (Ensure Server) — 서버 보장 후 E2E 실행
> - Queue: Quick E2E (Ensure Server+Worker) — 서버+워커 보장 후 E2E 실행
> - Queue: Results → JSONL Append (Success 5) — 최근 성공 5건을 JSONL로 누적
> - Queue: Open Results Log (JSONL)
\n## 2025-10-31 Updates\n\n- Autopoietic loop report regenerated (24h window) with fresh metrics; zero incomplete loops.\n- Worker monitor daemon restarted (PID 43120) and cache validation monitor rescheduled with CIM-based status checks.\n- Task queue ping smoke test succeeded (task 771c90c8... -> pong).\n- Cache validation monitor scripts patched for UTF-8-safe logging and CIM detection; active schedule stored in outputs/cache_validation_schedule.json.\n- Ran resonance-focused pytest suites (test_resonance*, test_resonance_integration) OK; orchestrator runtime suite blocked by UnicodeDecodeError in scripts/rune/bqi_adapter.py.\n- ChatOps docs updated to call out English natural-language commands (session/bot/stream).
