# Self-Managing Agent Report

**Timestamp**: 2025-11-10T23:04:30.265483+00:00
**Auto-Fix**: Enabled

## Dependencies Status

### 🔴 task_queue_server
- Process Running: ❌
- Health Check: ✅
- Auto-Fixed: ✅

### 🔴 rpa_worker
- Process Running: ❌
- Health Check: ❌
- Auto-Fixed: ✅

### 🔴 watchdog
- Process Running: ❌
- Health Check: ❌

### 🔴 task_watchdog
- Process Running: ❌
- Health Check: ❌

### 🔴 meta_observer
- Process Running: ❌
- Health Check: ❌

### 🔴 master_orchestrator
- Process Running: ❌
- Health Check: ❌
- Auto-Fixed: ✅

### 🟡 monitoring_collector
- Process Running: ❌
- Scheduled Task: ✅ (Ready)
- Health Check: ❌

## Actions Taken
- register_scheduled_task: task_queue_server (✅)
- start_dependency: task_queue_server (✅)
- start_dependency: rpa_worker (✅)
- register_scheduled_task: master_orchestrator (✅)

## Errors
- Failed to register watchdog: 
- Failed to register task_watchdog: 
- Failed to register meta_observer: 