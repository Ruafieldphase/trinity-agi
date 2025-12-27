# Missing References Cleanup Report

## 1. Tool References Restore
- **Created Dir**: `scripts/tools/`
- **Created Stubs**: `file_read.py`, `calculator.py`, `code_executor.py`, `web_search.py`
    - All set to `offline_stub` mode (writes `ok:false` to `tool_run_latest.json`).
- **Config**: `configs/tool_registry.json` created.

## 2. Minimal Monitoring Collector
- **Created**: `monitoring/metrics_collector.py`
- **Function**: Collects mtime/size/existence of `outputs`, `memory`, `bridge` without network.
- **Output**: `outputs/monitoring_metrics_latest.json`.

## 3. Orchestrator Paths Restore
- **Repo Dir**: `fdo_agi_repo/orchestrator/` created.
- **Wrapper**: `orchestrator/full_stack_orchestrator.py` delegates to `fdo_agi_repo`.
- **Stubs**:
    - `fdo_agi_repo/orchestrator/full_stack_orchestrator.py`
    - `fdo_agi_repo/orchestrator/gateway_optimizer.py`
    - `fdo_agi_repo/orchestrator/test_full_stack_integration.py`

## 4. Verification
- Run `python scripts/self_expansion/md_wave_sweeper.py --full`
- Result: Missing references should be significantly reduced.
