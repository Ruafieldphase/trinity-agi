# Control Bus 권한/검증 초안 (v0.1)

## 배경
- `controls/commands.jsonl`에 append되는 명령은 runner가 즉시 반영되므로 조작 시 위험이 큽니다.
- 현재는 JSON 구조만 확인하며, 발신자 인증/입력 검증/감사 체계가 미비합니다.

## 목표
1. 명령 구조를 명확히 정의하고 잘못된 입력이 기록되지 않도록 사전 검증합니다.
2. 명령 발신자의 신원을 확인해 위조를 방지합니다.
3. 감사 로그로 사후 분석·재현이 가능하도록 합니다.

## 명령 스키마 검증
- 공통 필드: `ts`(float), `cmd`(enum), 선택 필드 유효성 체크
- `set_entity`: 허용된 엔터티 ID, `params` 범위(amp 0~1.5, freq 0~1.0 등) 제한
- `set_mode`: {rest, focus, create, sleep} 이외 거부
- `set_bpm`: 30~180 BPM 범위
- `set_rules`: JSON Schema 기반, 필수 키 `pairings`, 각 항목의 수치 범위 검증
- `set_safety`: 0 < delta_per_sec ≤ 1.0
- 검증 실패 시 명령 파일에 기록하지 않고 HTTP 400 반환

## 인증/권한 옵션 비교
| 옵션 | 장점 | 단점 | 비고 |
| --- | --- | --- | --- |
| API 토큰(HMAC) | 구현 단순, 파일 append 전 서명 검증 | 토큰 유출 시 위험, 회전 필요 | Control Bus API 앞단 프록시에서 검증 |
| JWT + Role | 세분화된 권한 부여, 감사 claim 포함 | 발급/만료/서명키 관리 필요 | 모드 전환/안전 조정 등 역할 매핑 |
| IP ACL | 설정 간단, 내부망에 유용 | 스푸핑 취약, 단독 사용 한계 | 다른 방식과 병행 권장 |

권장 구성: `API Gateway → 인증 프록시 → Control Bus`. 프록시는 HMAC 서명과 JWT Role을 동시에 검증하고 명령 종류별 Role을 매핑합니다.

## 감사 로깅
- append 전 `controls/audit.log`에 `{ts, user, role, cmd, status}` 기록
- Prometheus exporter 또는 Elastic Stack으로 감사 지표/로그 전달

## 배포 단계
1. 인증 프록시(FastAPI 등) PoC 작성 → 기존 웹뷰 `/api/*`가 프록시를 통해 Control Bus에 append
2. Schema validator(Pydantic 등) 추가, 실패 시 오류 응답
3. runner의 `rules_history`에 `user`, `role`, `verified` 필드 확장
4. 통합 테스트: 허용/거부, replay 공격, 만료 토큰 시나리오

## 다음 단계
- LuBit: 프록시·validator 프로토타입 구현, 단위테스트 작성
- Lumen: UI에서 토큰 관리 및 오류 메시지 처리 흐름 정의
- System C: Vault/Secret Manager 연동 정책 수립
