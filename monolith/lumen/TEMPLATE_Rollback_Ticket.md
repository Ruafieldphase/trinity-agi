# Rollback Ticket — Emergency / Safety

**Requester**: ${NAME}  
**Reason**: ${SLO_BREACH|INCIDENT|NIGHT_POLICY|MANUAL}  
**Time (KST)**: ${YYYY-MM-DD HH:mm}

## Trigger
- Alerts: ${ALERTS}
- Metrics snapshot: success=${SUCCESS}, p95=${P95}ms, retry=${RETRY}

## Action
- Executed: `rollback_live_off.(ps1|sh)` → `enable_live=false`
- Guard re-applied: `Luon: Preflight Gate (force safe)`

## Follow-up
- Smoke/Eval re-run scheduled at: ${TIME}
- DR runbook invoked? ${YES|NO}
- Postmortem required? ${YES|NO}
