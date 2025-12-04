# Automated Daily Health Check Setup

## Overview
This guide explains how to set up automated daily health checks for the AGI system on Windows using Task Scheduler.

## Files Created
- `scripts/run_daily_health_check.bat` - Batch script that runs the health check
- `logs/health_check.log` - Log file for daily runs
- `outputs/health_check_YYYYMMDD.json` - Daily health reports

## Windows Task Scheduler Setup

### Option 1: PowerShell Command (Recommended)

Run this in PowerShell as Administrator:

```powershell
$action = New-ScheduledTaskAction -Execute "D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

Register-ScheduledTask -TaskName "AGI_Daily_Health_Check" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily health check for AGI system - monitors corrections, replan rate, and quality metrics"
```

### Option 2: Task Scheduler GUI

1. Open Task Scheduler (taskschd.msc)
2. Click "Create Basic Task"
3. Name: `AGI_Daily_Health_Check`
4. Description: `Daily health check for AGI system`
5. Trigger: Daily at 9:00 AM
6. Action: Start a program
7. Program: `D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat`
8. Finish

### Option 3: Command Line (schtasks)

```cmd
schtasks /create /tn "AGI_Daily_Health_Check" /tr "D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat" /sc daily /st 09:00 /f
```

## Verification

Test the task manually:
```powershell
Start-ScheduledTask -TaskName "AGI_Daily_Health_Check"
```

Check the last run:
```powershell
Get-ScheduledTaskInfo -TaskName "AGI_Daily_Health_Check"
```

View logs:
```cmd
type D:\nas_backup\fdo_agi_repo\logs\health_check.log
```

## Health Score Interpretation

- **90-100 points**: HEALTHY - System is working as expected
- **70-89 points**: WARNING - Some metrics need attention
- **0-69 points**: CRITICAL - Immediate investigation required

### Key Metrics Tracked
1. **Corrections enabled rate** (target: ≥95%) - 25 points
2. **Replan rate** (target: ≤10%) - 25 points
3. **Average quality** (target: ≥0.7) - 25 points
4. **Evidence OK rate** (target: ≥90%) - 25 points

## Expected Timeline

After P2.2 fix (absolute path .env loading):
- **Day 0-1**: Health score will be low (old data still in 24h window)
- **Day 2-3**: Health score improving as old data ages out
- **Day 4+**: Health score should be 90+ (HEALTHY)

## Monitoring Best Practices

1. **First week**: Check daily to ensure fix is stable
2. **After first week**: Check weekly unless alerts trigger
3. **If CRITICAL status**: Investigate immediately
   - Check `memory/resonance_ledger.jsonl` for recent failures
   - Verify `CORRECTIONS_ENABLED=1` in `.env`
   - Confirm `config.py` is using absolute path for .env

## Manual Health Check

To run health check manually:
```bash
cd D:\nas_backup\fdo_agi_repo
python scripts\daily_health_check.py
```

## Troubleshooting

### Task not running
1. Check Task Scheduler event log
2. Verify batch file path is correct
3. Ensure Python is in PATH for the user running the task

### Health check failing
1. Check logs: `logs/health_check.log`
2. Verify ledger exists: `memory/resonance_ledger.jsonl`
3. Run manually to see error messages

### Python not found
Add Python to PATH or use full path in batch file:
```batch
C:\Python39\python.exe scripts\daily_health_check.py
```

## Alerts (Future Enhancement)

Consider adding email alerts for CRITICAL status:
- Send email if health score < 70
- Attach JSON report
- Include recommended actions

## Related Files
- Health check script: `scripts/daily_health_check.py`
- Quick validation: `scripts/quick_validation.py`
- Full test suite: `scripts/production_test_suite.py`
