# LUON — Production Runbook (Quick)

## 0) 준비
- `.env` 작성: [.env.example](./.env.example) 참고
- KPI 표준화 파일 준비: `autodemo/kpi_adapted.csv`
- 플래그: `tools/luon/luon_feature_flags.yaml` (초기 `enable_live=false` 권장)

## 1) 검증
```powershell
$env:WORKSPACE = (Get-Location).Path
Get-Content .env | foreach {
  if($_ -and $_ -notmatch '^#') { $k=$_.Split('=')[0]; $v=$_.Substring($k.Length+1); [Environment]::SetEnvironmentVariable($k,$v,'Process') }
}
python tools\luon\luon_validate_prod.py --tools $env:TOOLS_DIR --outdir $env:OUT_DIR
```

## 2) 라이브 시작(원클릭)
- VS Code Tasks: **Luon: One-Click Ops (LIVE)**
- 또는 PowerShell: `.un_oneclick_ops.ps1`

## 3) 야간 안전
- VS Code Tasks: **Luon: SLO Guarded Rollback**
- 야간 시간대 설정: `.env` 또는 태스크 인자에서 조정

## 4) 브릿지 명령 실전화
- `tools/luon/luon_bridge_config_prod.yaml` 의 `${...}` 부분을 .env로 채움
- 실제 커맨드(루빛/세나/시안)만 적절히 교체 → 운영 즉시 반영

## 5) 롤백
```powershell
.ollback_live_off.ps1    # enable_live=false
```

## 트러블슈팅
- KPI 컬럼 불일치 → `autodemo/kpi_schema_v1.yaml`로 어댑터 적용
- 가드가 과보수 → 히스테리시스/쿨다운/레이트리밋 재튜닝
- 알림 실패 → Slack webhook/SMTP 자격증명 확인
