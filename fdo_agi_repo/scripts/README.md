# Scripts Quick Reference

This folder contains helper scripts for running and validating the self-correction (second pass) behavior of the pipeline.

## Files

- run_demo_self_correction.ps1
  - Runs the pipeline twice: first with corrections disabled, then enabled
  - Summarizes elapsed time and whether a `second_pass` event occurred (from `memory/resonance_ledger.jsonl`)
  - Internally sets `RAG_DISABLE=1` to force a no-citation scenario for deterministic replan testing. It restores the environment after each run.

- assert_second_pass.py
  - Programmatic assertion for CI or local checks
  - Runs twice under `RAG_DISABLE=1` and asserts:
    - Off: second_pass does NOT occur
    - On: second_pass DOES occur
  - Exits 0 on success; non-zero on failure

## Ping Quick Test (HTTP-first)

Use `send_ping.py` to verify the task queue end-to-end. It auto-detects the HTTP API on port 8091 and falls back to the file queue.

Commands:

```powershell
# Start API server (HTTP mode)
python fdo_agi_repo/scripts/task_queue_api_server.py

# Start HTTP poller (separate shell)
python fdo_agi_repo/scripts/http_task_poller.py --worker-id comet-local --interval 1.0

# Send ping (HTTP forced)
python fdo_agi_repo/scripts/send_ping.py --force http --timeout 10

# Or file-queue mode (with simple worker)
python fdo_agi_repo/scripts/comet_simple_worker.py  # separate shell
python fdo_agi_repo/scripts/send_ping.py --force file --timeout 10

# Results (both modes)
Get-Content fdo_agi_repo/outputs/task_queue/results/<TASK_ID>.json
```

For details, see `COMET_PING_빠른테스트.md` (HTTP auto-detect + file fallback ping guide).

## Usage

PowerShell demo (recommended):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\nas_backup\fdo_agi_repo\scripts\run_demo_self_correction.ps1" -Title "demo" -Goal "AGI 자기교정 루프 설명 3문장"
```

Python assertion (CI-friendly):

```powershell
"D:\nas_backup\fdo_agi_repo\.venv\Scripts\python.exe" "D:\nas_backup\fdo_agi_repo\scripts\assert_second_pass.py"
```

## Config and Environment

- App config: `D:\nas_backup\fdo_agi_repo\configs\app.yaml`
  - corrections.enabled, corrections.max_passes
  - evaluation.min_quality
- Environment overrides:
  - `CORRECTIONS_ENABLED`, `CORRECTIONS_MAX_PASSES`, `EVAL_MIN_QUALITY`
  - `RAG_DISABLE=1` (test only): forces no-citation scenario to deterministically trigger replans

## CI Smoke Test (file mode)

Validate file-queue ping end-to-end without external processes:

```powershell
python fdo_agi_repo/scripts/test_file_ping_smoke.py
```

This pushes a `ping` task to the file queue and processes it in-process via `comet_simple_worker.process_one_task`, exiting non-zero on failure.

## CI Smoke Test (HTTP mode)

Validate HTTP end-to-end loop (API server + HTTP poller + ping):

```powershell
python fdo_agi_repo/scripts/test_http_ping_smoke.py
```

Requires `Flask` and `requests` available in the Python environment.
