# AGI Quick Commands Reference

빠른 운영을 위한 명령어 모음입니다.

---

## 📊 일일 모니터링

### 모든 대시보드 열기
```powershell
.\scripts\open_monitoring_dashboard.ps1
```

### 특정 대시보드만 열기
```powershell
# Visual HTML Dashboard (브라우저)
.\scripts\open_monitoring_dashboard.ps1 -Dashboard Visual -Browser

# Performance Dashboard
.\scripts\open_monitoring_dashboard.ps1 -Dashboard Performance

# 24h Monitoring Report
.\scripts\open_monitoring_dashboard.ps1 -Dashboard Monitoring

# Latency Analysis
.\scripts\open_monitoring_dashboard.ps1 -Dashboard Latency
```

### 대시보드 갱신 후 열기
```powershell
.\scripts\open_monitoring_dashboard.ps1 -Refresh
```

---

## 🏥 헬스 체크

### 빠른 헬스 체크
```powershell
python fdo_agi_repo\scripts\check_health.py --fast --json-only
```

### 상세 헬스 체크
```powershell
python fdo_agi_repo\scripts\check_health.py
```

### AGI 시스템 상태
```powershell
.\scripts\chatops_router.ps1 -Intent "agi 상태"
```

---

## 🧪 테스트 & 검증

### E2E 통합 테스트 (YouTube 스킵)
```powershell
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube
```

### Orchestration 단독 테스트
```powershell
.\scripts\run_orchestration.ps1 -Topic "테스트 주제"
```

### Resonance Loop 테스트
```powershell
.\scripts\run_resonance_lumen_integration.ps1
```

---

## 📈 성능 분석

### Local LLM 성능 벤치마크
```powershell
.\scripts\check_llm_perf.ps1 -Benchmark
```

### 레이턴시 급증 분석
```powershell
.\scripts\analyze_latency_spikes.ps1 -ExportReport
```

### Replan 패턴 분석
```powershell
python fdo_agi_repo\analysis\analyze_replan_patterns.py
```

### 성능 트렌드 분석
```powershell
.\scripts\analyze_performance_trends.ps1 -WindowHours 24 -OpenMd
```

---

## 🔧 최적화 & 조정

### Routing Policy 최적화
```powershell
.\scripts\adaptive_routing_optimizer.ps1 -Verbose
```

### Circuit Breaker 상태 확인
```powershell
python scripts\circuit_breaker_router.py --status
```

### Circuit Breaker 테스트
```powershell
python scripts\circuit_breaker_router.py "테스트 메시지"
```

---

## 🤖 자동화 & 모니터링

### Local LLM 자동 모니터링 시작
```powershell
# 모니터링만 (권장)
.\scripts\auto_restart_local_llm.ps1 -Continuous

# 자동 재시작 활성화 (주의!)
.\scripts\auto_restart_local_llm.ps1 -AutoRestart -Continuous

# 백그라운드 실행
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File C:\workspace\agi\scripts\auto_restart_local_llm.ps1 -Continuous"
```

### 성능 벤치마크 저장
```powershell
.\scripts\save_performance_benchmark.ps1 -Warmup -Iterations 5 -Append
```

### 전체 모니터링 체인 실행
```powershell
.\scripts\save_performance_benchmark.ps1 -Warmup -Iterations 5 -Append -RunAnalysis -OptimizePolicy
```

---

## 📋 리포트 생성

### 성능 대시보드 갱신
```powershell
.\scripts\generate_performance_dashboard.ps1 -WriteLatest
```

### 24시간 모니터링 리포트
```powershell
.\scripts\generate_monitoring_report.ps1 -OpenReport
```

### Daily Briefing 생성
```powershell
.\scripts\generate_daily_briefing.ps1 -OpenReport
```

---

## 🔍 로그 & 디버깅

### 최근 벤치마크 로그 확인
```powershell
.\scripts\check_benchmark_log.ps1
```

### GPU 사용량 확인
```powershell
.\scripts\check_gpu_usage.ps1
```

### 시스템 헬스 체크
```powershell
.\scripts\system_health_check.ps1
```

---

## 🎯 빠른 진단

### Lumen vs LM Studio 비교
```powershell
.\scripts\compare_performance.ps1 -Warmup -Iterations 5
```

### 현재 라우팅 정책 확인
```powershell
Get-Content outputs\routing_policy.json | ConvertFrom-Json | Format-List
```

### Circuit Breaker 로그 확인
```powershell
Get-Content outputs\circuit_breaker_log.jsonl | Select-Object -Last 10
```

---

## 🚀 원클릭 작업

### 아침 루틴 (시스템 체크 + 대시보드)
```powershell
# 1. 헬스 체크
python fdo_agi_repo\scripts\check_health.py --fast --json-only

# 2. 대시보드 열기
.\scripts\open_monitoring_dashboard.ps1 -Refresh -Dashboard Visual -Browser
```

### 문제 해결 루틴
```powershell
# 1. Local LLM 성능 체크
.\scripts\check_llm_perf.ps1 -Benchmark

# 2. 레이턴시 분석
.\scripts\analyze_latency_spikes.ps1 -ExportReport

# 3. Replan 패턴 분석
python fdo_agi_repo\analysis\analyze_replan_patterns.py
```

### 주간 검증 루틴
```powershell
# 1. E2E 테스트
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube

# 2. 성능 대시보드 갱신
.\scripts\generate_performance_dashboard.ps1 -WriteLatest

# 3. 대시보드 열기
.\scripts\open_monitoring_dashboard.ps1 -Dashboard Performance
```

---

## 📱 VS Code Tasks

VS Code에서 `Ctrl+Shift+P` → **"Tasks: Run Task"** 입력 후 다음 작업 선택:

- `AGI: Quick Health Check` - 빠른 헬스 체크
- `Monitoring: Open Dashboard (auto generate)` - 대시보드 자동 생성 및 열기
- `Operations: Check System Health` - 시스템 헬스 체크
- 그 외 수많은 AGI 관련 작업들...

---

## 🔧 Scheduled Tasks (자동화)

### 등록된 자동 작업 확인
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "AGI*" }
```

### 성능 모니터 상태 확인
```powershell
.\scripts\register_performance_monitor.ps1 -Status
```

### 대시보드 자동 갱신 등록
```powershell
.\scripts\register_dashboard_autoupdate.ps1
```

---

## 💡 Pro Tips

1. **백그라운드 모니터링**
   ```powershell
   # Local LLM 모니터를 백그라운드로 실행하면 24/7 자동 관리
   Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File C:\workspace\agi\scripts\auto_restart_local_llm.ps1 -Continuous" -WindowStyle Hidden
   ```

2. **빠른 대시보드 접근**
   ```powershell
   # 브라우저에서 Visual Dashboard를 즐겨찾기에 추가
   # 파일: C:\workspace\agi\outputs\system_dashboard_latest.html
   ```

3. **알림 설정**
   ```powershell
   # 성능 저하 시 이메일/Slack 알림 (향후 구현 예정)
   ```

4. **커스텀 임계값**
   ```powershell
   # routing_policy.json에서 latency_threshold_ms 수동 조정 가능
   # 기본: 500ms, 권장: 1000ms (occasional spikes 허용)
   ```

---

## 🆘 문제 해결

### Local LLM이 응답하지 않을 때
```powershell
# 1. 성능 체크
.\scripts\check_llm_perf.ps1

# 2. 프로세스 확인
Get-Process "LM Studio"

# 3. 수동 재시작
# LM Studio 앱을 열고 Server 시작
```

### Gateway 레이턴시가 높을 때
```powershell
# 1. 레이턴시 분석
.\scripts\analyze_latency_spikes.ps1 -ExportReport

# 2. Circuit Breaker 확인
python scripts\circuit_breaker_router.py --status

# 3. 필요시 임계값 조정
# outputs\routing_policy.json 수정
```

### E2E 테스트 실패 시
```powershell
# 1. 상세 로그 확인
Get-Content outputs\e2e_test_results_*.json | Select-Object -Last 1 | ConvertFrom-Json

# 2. 개별 시스템 테스트
.\scripts\run_orchestration.ps1 -Topic "테스트"

# 3. 헬스 체크
python fdo_agi_repo\scripts\check_health.py
```

---

**마지막 업데이트:** 2025-11-02
**버전:** 2.0 - Self-Optimizing Era
