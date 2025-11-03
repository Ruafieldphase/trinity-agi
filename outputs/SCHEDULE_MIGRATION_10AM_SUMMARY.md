# Schedule Migration to 10 AM - Operational Summary

**Date**: 2025-11-02  
**Migration Type**: Shift from 03:xx early-morning schedules to 10:00 AM workday alignment  
**Reason**: PC will be powered off overnight; workday starts at 10:00 AM

---

## 🔄 Schedule Changes Applied

### Removed (Old 03:xx Schedule)

- ❌ Snapshot Rotation: 03:15
- ❌ Daily Maintenance: 03:20
- ❌ Autopoietic Loop Report: 03:25

### New 10:00 AM Schedule

- ✅ **Snapshot Rotation**: 10:00 daily (with zip compression)
- ✅ **Daily Maintenance**: 10:05 daily
- ✅ **Autopoietic Loop Report**: 10:10 daily
- ✅ **Monitoring Collector**: Every 5 minutes (continuous)

### At-Logon Services (Auto-Start)

- ✅ **Task Queue Server**: Starts at logon (port 8091)
- ✅ **Inbox Watcher**: Starts at logon (monitors all agents)

---

## ✅ Service Health Verification

All background services verified and operational:

| Service | Status | Check Time |
|---------|--------|------------|
| Queue Server (8091) | ✅ HEALTHY | 2025-11-02 |
| Worker Monitor | ✅ RUNNING | 2025-11-02 |
| Task Watchdog | ✅ RUNNING | 2025-11-02 |
| Lumen Probe Monitor | ✅ ACTIVE | 2025-11-02 |
| Inbox Watcher | ✅ REGISTERED | 2025-11-02 |
| Monitoring Collector (5m) | ✅ REGISTERED | 2025-11-02 |

---

## 📋 Daily Workflow (10 AM Start)

### Morning (10:00-10:15)

1. **10:00** - Snapshot Rotation runs (archives old monitoring data with zip)
2. **10:05** - Daily Maintenance runs (cleanup + report regeneration)
3. **10:10** - Autopoietic Loop Report generated (24h self-analysis)

### Continuous

- **Every 5 min** - Monitoring Collector snapshots system state
- **At logon** - Queue Server + Inbox Watcher auto-start

---

## 🔧 Manual Trigger Commands

If needed, you can manually trigger any scheduled task:

```powershell
# Trigger snapshot rotation
Start-ScheduledTask -TaskName 'MonitoringSnapshotRotationDaily'

# Trigger daily maintenance
Start-ScheduledTask -TaskName 'MonitoringDailyMaintenance'

# Trigger autopoietic report
Start-ScheduledTask -TaskName 'AutopoieticLoopDailyReport'
```

---

## 📊 Key Outputs Generated Daily

After the 10:00-10:10 automation sequence completes, these files will be updated:

- `outputs/monitoring_report_latest.md` - Human-readable monitoring summary
- `outputs/monitoring_metrics_latest.json` - Machine-readable metrics
- `outputs/monitoring_dashboard_latest.html` - Visual dashboard
- `outputs/autopoietic_loop_report_latest.md` - Self-analysis report
- `outputs/quick_status_latest.json` - Unified AGI+Lumen status
- `outputs/status_snapshots/` - Rotated historical snapshots (zipped)

---

## 🚀 Post-Restart Checklist

When starting work each morning:

1. **Power on PC at ~10:00 AM** - Let scheduled tasks run automatically
2. **Verify services** (optional):

   ```powershell
   # Run quick health check
   & C:\workspace\agi\scripts\queue_health_check.ps1
   ```

3. **Check dashboards** (optional):
   - Open `outputs/monitoring_dashboard_latest.html`
   - Review `outputs/monitoring_report_latest.md`

---

## 🔍 Optional Future Adjustments

Not implemented yet, but available if needed:

- **Forced Evidence Check**: Move from 03:00 to 10:20
- **Daily Backup**: Adjust from 03:30 to evening (e.g., 22:30)
- **Master Orchestrator**: Add 5-min delayed boot startup
- **BQI Phase 6 Learner**: Adjust from 03:05/03:10 to 10:15

To apply any of these, notify and they can be configured in ~2 minutes.

---

## 📝 Notes

- **PC Shutdown**: Safe to power off overnight; all critical tasks now run during workday
- **Wake Timer**: Snapshot rotation task has WakeToRun enabled (will attempt to wake PC if supported)
- **Resilience**: At-logon services ensure Queue + Inbox monitoring resume automatically
- **Historical Data**: Old snapshot archives are compressed and retained (cleanup after 14 days)

---

**Status**: ✅ Migration Complete  
**Next Review**: After first 10 AM automated run (verify all tasks execute successfully)
