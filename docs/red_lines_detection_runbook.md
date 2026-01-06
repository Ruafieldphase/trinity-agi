# Red Lines Detection Runbook (stub v0.1)

이 문서는 문서 참조 복구용 스텁입니다.  
실제 “레드라인 탐지/대응” 자동화는 아직 활성화되어 있지 않습니다.

## 목표

- 레드라인 정책 파일의 존재와 위치를 고정
- 리허설(비파괴) 결과를 파일로 남겨 관측 가능하게 유지

## 정책 파일

- `policy/red_line_monitor.yaml`

## 리허설(비파괴)

- PowerShell: `scripts/red_line_rehearsal.ps1`
- 출력: `outputs/safety/red_line_rehearsal_latest.json`

## 탐지기(스텁)

- Python: `safety/red_line_monitor.py`
- 출력: `outputs/safety/red_line_monitor_latest.json`

## 주의

- 이 단계에서는 **차단/킬스위치 동작이 없다** (관측/기록만)
- 실제 강제 조치는 운영 승인/안전 설계 확정 후 추가

