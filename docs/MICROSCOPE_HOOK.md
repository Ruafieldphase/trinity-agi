# Microscope hook for quick_status

This repository includes an optional micro-capture hook that snapshots key signals (CPU, memory, process deltas, quick probes, and queue health) whenever the unified monitoring detects a degradation or alert.

## How it works

- The script `scripts/quick_status.ps1` can invoke `scripts/microscope_capture.ps1` in the background when thresholds are exceeded.
- A cooldown file prevents repeated captures from spamming the output directory.
- Captures are saved to `outputs/microscope/micro_*.json` (UTF-8).

## Enable it

You can run the dashboard with the hook enabled and small window:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\quick_status.ps1 -MicroscopeOnSpark -MicroscopeWindowSeconds 2 -MicroscopeLevel minimal
```

By default, nothing is captured unless the run is not “all green” (either Issues or Warnings exist).

## Useful flags

- `-MicroscopeOnSpark` — enable the hook (off by default)
- `-MicroscopeWindowSeconds <int>` — sampling window (1–30 seconds, default 3)
- `-MicroscopeLevel <minimal|normal|full>` — number of top processes and probes to include (default minimal)
- `-MicroscopeCooldownSec <int>` — skip capture if the last one happened within this many seconds (default applied by script)

The microscope runner accepts more flags directly (when calling `scripts/microscope_capture.ps1`):

- `-OutDir` — output directory (default `outputs/microscope`)
- `-SparkLabels` — optional label(s) like `"Local LLM"`, `"Cloud AI"`, `"Lumen Gateway"`
- `-Quiet` — reduce console noise from the capture process

## Forcing a test capture

To force a spark for testing, temporarily lower thresholds, e.g.:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\quick_status.ps1 -MicroscopeOnSpark -AlertLocalMs 1 -WarnLocalMs 1 -AlertCloudMs 1 -WarnCloudMs 1 -AlertGatewayMs 1 -WarnGatewayMs 1 -MicroscopeCooldownSec 1
```

Check `outputs/microscope/` for a newly created `micro_*.json` file.

## Notes

- The capture runs in a separate PowerShell process to avoid delaying the main dashboard.
- If you don’t see new files, verify the run actually produced warnings or issues, or shorten the cooldown.
- This hook is non-intrusive: existing tasks that call `quick_status.ps1` behave exactly the same unless `-MicroscopeOnSpark` is passed.
