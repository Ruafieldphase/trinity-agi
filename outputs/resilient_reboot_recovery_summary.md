# Resilient Reboot Recovery Summary

**Timestamp (local)**: 11/08/2025 12:12:30
**Timestamp (UTC)**: 2025-11-08T12:11:16.1631936+09:00
**Mode**: execute  
**DryRun**: False  
**Success**: True  
**Errors**: 0  
**Duration (ms)**: 74338  

### Steps
- **delay**: ok (60 s) 60000 ms
- **ensure_task_queue_server**: ok (no detail) 46 ms
- **ensure_single_worker**: ok (no detail) 545 ms
- **session_continuity_restore**: ok (no detail) 115 ms
- **post_reboot_verify**: ok (no detail) 13065 ms

### Gates
- Memory Gate: enabled=False passed=(n/a) freeMB=(n/a) min=(n/a)
- Health Gate: enabled=False exitCode=(n/a) trendCheck=(n/a) profile=(n/a)
- Cooldown: enabled=(n/a) skipped=(n/a) minutes=(n/a) lastRunMinutesAgo=(n/a)

### Errors
- (none)

### System
- Machine: BINO
- OS: Microsoft Windows 11 Pro 10.0.26200 (Build 26200)
- PSVersion: 5.1.26100.7019
- CPU Count: 12
- Memory: total=97442MB free=41623MB

### Marker
- Run Mode: execute
- Finalized Early: False
