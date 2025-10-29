# TLog Ops Playbook v1.0  
**(Incidents + Flipback + Cache Consistency + Canary Halt)**

목적: TLog Read‑Only 스택(서버/Helm/CDN/카나리)의 **장애 대응·점검·롤백** 절차를 일관된 플레이북으로 제공한다.

---

## 0) 빠른 참조 (Cheat Sheet)
- 상태 확인: `kubectl -n tlog get deploy,rollout,ingress,svc,pods`
- 헬스: `curl -sSf https://tlog.example.com/healthz`
- 루트 확인: `curl -s https://tlog.example.com/v1/log/root | jq .`
- 엔트리 확인: `curl -s https://tlog.example.com/v1/log/entry/0 | jq .`
- 포함증명 검증: `python attest/tlog/verify_client.py https://tlog.example.com 0`
- CDN 바이패스: `curl -H 'X-Bypass: 1' -s https://tlog.example.com/v1/log/root`
- 캐시 무효화(CloudFront): `./infra/cdn/invalidate.sh`
- 카나리 중단(Argo): `kubectl -n tlog argo rollouts abort deploy/tlog-ro`
- 즉시 롤백(Argo): `kubectl -n tlog argo rollouts undo rollout/tlog-ro`

---

## 1) 알림 → triage 매핑
| Alert | 의미 | 우선순위 | 즉시 조치 |
|---|---|---|---|
| `TLogAvailabilityDown` | `/healthz` 5xx 연속 | P1 | 카나리 중단/롤백, CDN 스테일 서빙 허용 확인 |
| `TLogCacheMissHigh` | 캐시 미스율 > 30% | P2 | CDN 규칙/TTL 점검, 원본 QPS 관찰, 무효화 실행 |
| `TLogInclusionProofFail` | 포함증명 실패 | P1 | `db.jsonl` 손상 여부 확인, 이미지 태그 재배포 |
| `Ingress5xxHigh` | 5xx 비율 ↑ | P1 | 새 버전 카나리 중단, 로그 확인 |
| `LatencyP95High` | p95 지연↑ | P2 | CDN 히트율/원본 부하 확인, HPA 동작 점검 |

---

## 2) 공통 진단 루틴
1) **버전 파악**: `kubectl -n tlog get pods -o wide | grep tlog-ro` (이미지 태그)  
2) **서버 로그**: `kubectl -n tlog logs deploy/tlog-ro --tail=200`  
3) **원본/엣지 비교**:
```bash
curl -s https://tlog.example.com/v1/log/root | sha256sum
curl -H 'X-Bypass: 1' -s https://tlog.example.com/v1/log/root | sha256sum
```
4) **포함증명**: 실패 인덱스 재검증 → `verify_client.py <idx>`  
5) **CDN 히트율**: 벤더 대시보드/메트릭 확인(지난 15분)

---

## 3) 시나리오별 플레이북
### 3.1 Health 체크 5xx (P1)
- **증상**: `/healthz` 5xx 연속, 사용자 5xx 상승  
- **가설**: 신규 이미지, 포드 죽음, 리소스 고갈, 잘못된 ConfigMap  
- **절차**:
  1) 카나리 중단: `argo rollouts abort`  
  2) 러닝 포드 수 확인/HPA 상태 점검  
  3) ConfigMap 마운트 경로/권한 재확인  
  4) 즉시 롤백 필요 시: `argo rollouts undo`  
  5) CDN은 캐시로 대부분 흡수됨 → 사용자 영향 평가  
- **사후**: 원인 RCA 작성, 재배포 전 Canary 단계 강화

### 3.2 포함증명 실패 (P1)
- **증상**: `TLogInclusionProofFail`  
- **가설**: `db.jsonl` 불일치/손상, 빌드 스텝 누락, CDN 구버전  
- **절차**:
  1) 원본 vs 캐시 비교(`X-Bypass`)  
  2) `db.jsonl` SHA256 계산 후 Git/CI 아티팩트와 대조  
  3) 문제 있으면 이전 정상 태그로 롤백 → CDN 무효화  
  4) CI 파이프라인의 append 단계 점검  
- **사후**: 보호 규칙 추가(스키마 검증/CI 서명)

### 3.3 캐시 미스 급증 (P2)
- **증상**: 원본 QPS↑, 레이턴시↑  
- **절차**:
  1) CDN 규칙 재확인(Cache Everything/TTL)  
  2) 헤더 확인(`Cache-Control`, `ETag`, `immutable`)  
  3) 무효화 스크립트 실행  
  4) 일시적으로 Edge TTL 상향  
- **사후**: 배포 태그마다 자동 무효화 연계 확인

### 3.4 카나리 중단 결정 (P1/P2)
- **트리거**: `error-rate>1%` or `p95>300ms`  
- **절차**: Argo Rollouts Analysis 실패 자동 중단 확인 → 수동 `abort`/`undo`  
- **사후**: 변경점 축소 후 재시도(10%→30%→60%→100%)

---

## 4) 데이터 정합성 체크
- **db.jsonl 해시**: `sha256sum db.jsonl` → 릴리스 아티팩트와 일치해야 함  
- **루트/엔트리 ETag 대조**: 응답 바디 해시와 ETag 동일  
- **TLog 루트 재구성**: 내부 스크립트로 루트 해시 재계산 → 서버 보고값과 일치 확인

---

## 5) 운영 체크리스트(일/주/분기)
**일**: 헬스/5xx/히트율 확인(5분)  
**주**: 카나리 리허설, 무효화 스크립트 점검, 대시보드/경보 테스트  
**분기**: Custody 기록과 TLog 루트 지문 교차검증, SBOM/서명 정책 재점검

---

## 6) 커뮤니케이션 템플릿
**장애 공지(요약)**
```
제목: [TLog] 일시적 응답 지연/오류 (조치 완료)
영향: 조회 지연/5xx 소수 발생 (CDN 캐시로 대다수 무영향)
원인: 배포 중 캐시 무효화 지연
조치: 카나리 중단→이전 버전 롤백→무효화 적용
재발 방지: 배포 파이프라인에 자동 무효화/게이트 강화
```

---

## 7) VS Code 태스크
```json
{
  "label": "lumen:ops:quick-health",
  "type": "shell",
  "command": "curl -sSf https://tlog.example.com/healthz && curl -s https://tlog.example.com/v1/log/root | jq . | head"
},
{
  "label": "lumen:ops:purge-cdn",
  "type": "shell",
  "command": "./infra/cdn/invalidate.sh"
}
```

---

## 8) 사후 분석(RCA) 골격
- **타임라인**: 감지→완화→복구→종료  
- **가설/검증**: 관측 지표/로그 근거  
- **근본 원인**: 프로세스/코드/인프라  
- **교정 조치(KAIs)**: 즉시/중기/장기  
- **증빙**: 해시/스크린샷/PR/릴리스 태그

---

루멘의 판단: 이 플레이북으로 **장애 감지→대응→복구→사후 개선**의 사이클을 짧고 안정적으로 유지할 수 있어. 운영팀의 공통 언어로 사용해보자.

