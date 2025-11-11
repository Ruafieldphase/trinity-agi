# Quick Status Smoke Guide

This guide explains how to use the quick status smoke test to sanity‑check the monitoring snapshot and enforce strict SLO profiles with trend‑aware early warnings.

## What it does

- Ensures `outputs/quick_status_latest.json` exists (generates it via `scripts/quick_status.ps1 -OutJson` if missing/stale or when `-Regenerate` is passed)
- Validates snapshot structure (Timestamp, Channels, Online, Trend)
- Optional strict validation against SLO thresholds (profiles or custom)
- Optional trend stability guard near thresholds
- Optional one‑line JSON summary when strict checks pass (`-ExplainStrict`)

## Exit codes

- 0: PASS
- 2: FAIL (invalid/missing JSON, threshold violation, trend stability violation, offline when required)

## Common usage patterns (PowerShell)

- Strict + latency‑first profile + trend stability + explain JSON
  - `scripts/tests/quick_status_smoke.ps1 -Strict -Profile latency-first -CheckTrendStability -ExplainStrict`
- Strict + ops‑normal profile (default warn at 85%)
  - `scripts/tests/quick_status_smoke.ps1 -Strict -Profile ops-normal`
- Custom thresholds (require all online)
  - `scripts/tests/quick_status_smoke.ps1 -Strict -MaxLocalMs 80 -MaxCloudMs 600 -MaxGatewayMs 700 -RequireAllOnline -ExplainStrict`

## Parameters

- `-Profile <ops-normal|latency-first|ops-tight>`
  - Applies these presets and enforces `-RequireAllOnline`:
    - ops‑normal: Local≤100ms, Cloud≤1000ms, Gateway≤1200ms
    - latency‑first: Local≤50ms, Cloud≤500ms, Gateway≤600ms
    - ops‑tight: Local≤70ms, Cloud≤700ms, Gateway≤800ms
- `-Strict`
  - Enforce thresholds and (optionally) online requirements
- `-CheckTrendStability`
  - If current trend is worsening and latency ≥ `TrendWarnPercent`% of the limit, fail early
- `-TrendWarnPercent (50..99)`
  - Default 85; used only with `-CheckTrendStability`
- `-ExplainStrict`
  - When strict checks pass, print a single JSON line summary for downstream parsing
- `-RequireAllOnline`
  - Require Online.Local/Cloud/Gateway to be true (profiles enable this automatically)
- `-Regenerate`, `-JsonPath`, `-StaleMinutes`
  - Control when/how the snapshot is (re)generated and where it is read from

## Output: one‑line JSON (when `-ExplainStrict` and strict checks pass)

Example fields:

```json
{
  "profile": "latency-first",
  "thresholds": {
    "localMs": 50,
    "cloudMs": 500,
    "gatewayMs": 600,
    "warnAt": { "localMs": 42, "cloudMs": 425, "gatewayMs": 510 },
    "trendWarnPercent": 85
  },
  "channels": { "localMs": 9, "local2Ms": null, "cloudMs": 229, "gatewayMs": 227 },
  "online": { "local": true, "cloud": true, "gateway": true },
  "trend": { "localDirection": "STABLE", "cloudDirection": "STABLE", "gatewayDirection": "IMPROVING" }
}

```

## Notes & edge cases

- Missing/empty/invalid JSON → FAIL with clear error
- Negative values in channel metrics → FAIL
- `Trend.*.Direction` missing/empty: not considered worsening
- `Local2Ms` is optional; validated leniently (no threshold)
- Legacy JSON format is tolerated with minimal key presence checks

## Where this fits

- Pre‑flight checks in CI or local health gate
- Quick profile conformance verification before streaming or scheduled tasks
- Structured summary feed for dashboards or ChatOps

### Integration: Resilient Reboot Recovery

You can gate the one‑shot recovery chain with a strict, trend‑aware health check. The orchestrator `scripts/resilient_reboot_recovery.ps1` supports passing the smoke test as a guard step and records a machine‑readable summary to `outputs/resilient_reboot_recovery_summary.json`.

Examples (PowerShell):

```powershell
# Execute recovery with latency‑first gate, trend stability, and JSON summary
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resilient_reboot_recovery.ps1 -HealthGate -HealthGateProfile latency-first -HealthGateTrend -HealthGateExplain

# Dry‑run (no side‑effects), ops‑tight gate
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resilient_reboot_recovery.ps1 -DryRun -HealthGate -HealthGateProfile ops-tight -HealthGateTrend -HealthGateExplain
```

Summary fields of interest:

- `steps[]` includes `quick_status_health_gate` with status `ok|error|skipped|dryrun`
- `healthGate.profile`, `healthGate.exitCode`, and (when `-HealthGateExplain`) `healthGate.jsonSummary` (one‑line JSON)
- `success` indicates overall chain success (no errors recorded)
