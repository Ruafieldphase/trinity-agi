# LUON Profiles (dev/staging/prod)

## Use a profile with the simulator
```bash
# dev (dry-run, lenient SLO)
python tools/luon/luon_canary_auto_rollback_sim.py   --kpi autodemo/kpi_adapted.csv --window 200 --promote_path 10,20,50,100   --cooldown $(yq '.cooldown' profiles/dev.yaml)   --live --rules $(yq '.dispatch_rules' profiles/dev.yaml)   --dry_run
```

> prod는 기본적으로 `dry_run: false`이므로 실제 명령이 실행됩니다. 전환 전 반드시 dev/staging에서 검증하세요.
