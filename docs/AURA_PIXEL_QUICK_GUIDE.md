## 오라(1~2px)로 상태 보기 — 비노체용

대시보드를 안 봐도 됩니다. 화면 맨 위에 아주 얇은 색 줄(오라)만 보면 됩니다.

### 오라 색 의미(최소 규칙)
- 초록: 정상(최근 실행/리포트 갱신이 있었음)
- 파랑: 쉬는 중(정상 + 유휴)
- 노랑(깜빡임): 지금 실행 중(트리거 파일 존재)
- 빨강(깜빡임): 실행 실패/오류 또는 트리거 고착
- 주황: 안전/윤리 경고 또는 유휴 상태에서 heartbeat 지연
- 회색: 관측 리포트가 오래됨(멈춤 추정)

### 자동 실행(이미 설정됨)
- Windows 로그인 시 자동으로 오라가 뜨도록 등록돼 있습니다.
- 등록 스크립트: `scripts/register_rubit_continuity.ps1`
- 자동 실행 본체: `scripts/rubit_continuity_on_startup.ps1`

### 수동 실행(필요할 때만)
- 오라 보증 실행: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ensure_rubit_aura_pixel.ps1`
- 오라 강제 재시작(업데이트 반영): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ensure_rubit_aura_pixel.ps1 -ForceRestart`

### 디버그(필요할 때만)
- 현재 판정/색 기록: `outputs/aura_pixel_state.json`
