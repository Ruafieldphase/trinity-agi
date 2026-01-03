# Technical Architecture Overview

**D:\nas_backup System Analysis**  
**Generated**: 2025-10-29  
**Scale**: 141,995 files | 15,504 directories | 34.1 GB

---

## System-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  VS Code Extension  │  Voice (Hey Sena)  │  ChatOps CLI        │
│    (Gitko Agent)    │   Multi-turn TTS   │  Natural Language   │
└──────────┬──────────┴──────────┬──────────┴──────────┬──────────┘
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│  Core MCP Server  │  Task Queue (HTTP 8091)  │  ChatOps Router │
│   Tool Bridge      │   Job Distribution       │   Intent Parser │
└──────────┬─────────┴──────────┬────────────────┴──────┬──────────┘
           │                    │                        │
┌────────────────────────────────▼─────────────────────────────────┐
│                      RUBY (EXTERNAL INTERFACE)                    │
├───────────────────────────────────────────────────────────────────┤
│  Persona Registry  │  Phase Controller  │  Clipboard Orchestration│
│    E1/E2/E3        │    Phase Injection  │    Inter-Persona Comms │
├───────────────────────────────────────────────────────────────────┤
│          INTERNAL ORGANS (PERSONA ORCHESTRATION)                  │
├───────┬──────────┬───────────┬─────────┬─────────┬────────────────┤
│ Core  │  Shion   │  Trinity  │  Core  │  Sena   │   Lubit        │
│ (Core) │(Executor)│(Resonance)│ (Tools) │(Bridge) │   (Meta)       │
└───────┴──────────┴───────────┴─────────┴─────────┴────────────────┘
        │        │        │         │         │         │
┌───────▼────────▼────────▼─────────▼─────────▼─────────▼──────────┐
│                     AGI CORE SYSTEM                               │
├───────────────────────────────────────────────────────────────────┤
│  Self-Correction Loop  │  BQI Learning  │  Evidence Validation   │
│  Resonance Ledger      │  Feedback Pred │  Forced Evidence Gate  │
└───────┬────────────────┴────────┬────────┴────────────┬──────────┘
        │                         │                     │
┌───────▼─────────────────────────▼─────────────────────▼──────────┐
│                     DATA & MEMORY LAYER                           │
├───────────────────────────────────────────────────────────────────┤
│  Knowledge Base       │  Session Memory      │  Outputs          │
│  - evidence_index     │  - parsed_convs      │  - monitoring     │
│  - corpus.jsonl       │  - agent systems     │  - analytics      │
│                       │                      │  - reports        │
└───────┬───────────────┴──────────────────────┴────────┬──────────┘
        │                                               │
┌───────▼───────────────────────────────────────────────▼──────────┐
│                     LLM INTEGRATION LAYER                         │
├───────────────────────────────────────────────────────────────────┤
│  Vertex AI (Gemini)  │  Response Cache  │  Rate Limit Control   │
│  Multi-modal Support │  Local LLM Proxy │  Load Balancing       │
└───────┬──────────────┴──────────────────┴───────────┬────────────┘
        │                                             │
┌───────▼─────────────────────────────────────────────▼────────────┐
│                    DEPLOYMENT & MONITORING                        │
├───────────────────────────────────────────────────────────────────┤
│  Cloud Run Services     │  Canary Deployment  │  Alert System    │
│  - ion-api (legacy)     │  5% → 100% rollout  │  Health Gates    │
│  - ion-api-canary (new) │  Emergency Rollback │  Dashboards      │
└───────────────────────────────────────────────────────────────────┘
```

---

## Core Subsystems

### 1. AGI Self-Correction System

**Purpose**: Autonomous learning and behavioral optimization

**Components**:

- **Resonance Ledger** (`memory/resonance_ledger.jsonl`)
  - Event tracking with timestamps
  - Success/failure attribution
  - Resonance scoring
  - Evidence links

- **Evidence Index** (`knowledge_base/evidence_index*.json`)
  - Validated successful patterns
  - Counter-examples
  - Context metadata
  - Confidence scores

- **Self-Correction Loop**:

  ```
  Action → Observation → Resonance Scoring → Evidence Update → 
  Behavior Adjustment → Next Action
  ```

**Key Scripts**:

- `scripts/assert_second_pass.py` - Validates correction occurred
- `scripts/assert_evidence_gate_forced.ps1` - Ensures evidence accumulation
- `scripts/check_health.ps1` - Health gate validation

**Data Flow**:

```
User Input → Persona → Action → Ledger Entry → Evidence Extraction → 
Index Update → Phase Controller Adjustment
```

---

### 2. BQI (Behavioral Quality Index) Learning

**Purpose**: Quantitative behavioral optimization across personas

**Architecture**:

#### Phase 5: Pattern Learning

- **Learner**: `scripts/rune/bqi_learner.py`
- **Output**: `outputs/bqi_pattern_model.json`
- **Mechanism**: Historical pattern extraction from resonance ledger
- **Scheduled**: Daily 03:10

#### Phase 6: Binoche_Observer Persona & Ensemble

- **Persona Learner**: `scripts/rune/binoche_persona_learner.py`
  - Output: `outputs/binoche_persona.json`
  - Learns persona-specific behavioral patterns

- **Feedback Predictor**: `scripts/rune/feedback_predictor.py`
  - Output: `outputs/feedback_prediction_model.json`
  - Predicts user response quality

- **Online Learner**: `scripts/rune/binoche_online_learner.py`
  - Output: `outputs/ensemble_weights.json`
  - Adaptive weight adjustment for ensemble judges
  - Learning rate: 0.01 (24h window), 0.005 (7d window)

- **Success Monitor**: `scripts/rune/binoche_success_monitor.py`
  - Output: `outputs/ensemble_success_metrics.json`
  - Tracks ensemble performance over time

**Ensemble Architecture**:

```
Input → [Judge 1, Judge 2, ..., Judge N] → Weighted Voting → 
Decision → Feedback → Weight Update (Online Learning)
```

**Scheduled Tasks**:

- BQI Learner: Daily 03:10
- Ensemble Monitor: Daily 03:15
- Online Learner: Daily 03:20

---

### 3. Persona Orchestration

**Registry Files**:

- `configs/persona_registry.json` - Base definitions
- `configs/persona_registry_e2.json` - E2 phase
- `configs/persona_registry_e3.json` - E3 phase (current)

**Phase Controllers**:

- `configs/phase_controller_e2.yaml`
- `configs/phase_controller_e3.yaml`

**Personas**:

| Name | Type | Specialty | Role within Ruby |
|------|------|-----------|------------------|
| Core (Core) | 판단형 | Decision & Permission | Internal Organ: Judgment |
| Shion (Shion)| 실행형 | Execution & Body | Internal Organ: Execution |
| Trinity | 공명형 | Resonance & Connection| Internal Organ: Resonance |
| Core | 도구형 | Tool orchestration | Support Organ |
| Sena | 브리지형 | Connection specialist | Support Organ |
| Lubit | 메타형 | Meta-analysis | Support Organ |

**Phase Injection**:

- Complexity management via incremental feature rollout
- E1 → E2 → E3 evolution
- Backward compatibility maintained
- Evidence-based phase transitions

**Inter-Persona Communication**:

- Clipboard-based orchestration (`configs/clipboard_orchestration.yaml`)
- Shared memory via session files
- Resonance ledger as coordination log

---

### 4. LLM Unified Integration

**Service Architecture**:

```
┌─────────────────────────────────────────────────┐
│           ion-api-canary (NEW)                  │
│           Cloud Run Service                     │
│           /api/v2/recommend/personalized        │
└────────────────┬────────────────────────────────┘
                 │
                 │  Traffic Split (5% → 100%)
                 │
┌────────────────▼────────────────────────────────┐
│           ion-api (LEGACY)                      │
│           Cloud Run Service                     │
│           /chat                                 │
└─────────────────────────────────────────────────┘
```

**Task Queue Server**:

- **Location**: `LLM_Unified/ion-mentoring/task_queue_server.py`
- **Port**: 8091
- **API**:
  - `POST /api/v2/recommend/personalized` - Personalized recommendations
  - `GET /api/health` - Health check
- **Purpose**: Distributed job processing, request queueing

**Canary Deployment**:

- **Script**: `LLM_Unified/ion-mentoring/scripts/deploy_phase4_canary.ps1`
- **Stages**: 5% → 10% → 25% → 50% → 100%
- **Rollback**: `emergency_rollback.ps1` (force mode available)
- **Monitoring**: `compare_canary_vs_legacy.ps1`

**Rate Limiting**:

- **Probe Script**: `LLM_Unified/ion-mentoring/scripts/rate_limit_probe.ps1`
- **Monitoring Loop**: 30-minute intervals with canary probes
- **Safe Thresholds**: 10 req/side, 1s delay (normal), 25 req/side, 500ms delay (aggressive)

**Load Testing**:

- **Framework**: Locust
- **Scenarios**: Light, moderate, heavy
- **Profiles**: `LLM_Unified/ion-mentoring/load_tests/`
- **Results**: `outputs/*.csv`
- **Analysis**: `scripts/summarize_locust_results.ps1`

---

### 5. Voice & Multi-turn Interaction

**Hey Sena Evolution**:

| Version | File | Features |
|---------|------|----------|
| v1 | `hey_sena.py` | Basic voice activation |
| v3 | `hey_sena_v3_multiturn.py` | Multi-turn conversation |
| v4 | `hey_sena_v4_llm.py` | LLM integration |
| v4.1 | `hey_sena_v4.1_cached.py` | Response caching |
| v4.1 logged | `hey_sena_v4.1_logged.py` | Comprehensive logging |

**TTS Pipeline**:

```
Speech Input → Voice Recognition → Intent Parsing → 
Conversation Context → LLM Query → TTS Generation → 
Audio Output → Multi-turn State Update
```

**Key Modules**:

- `conversation_mode_logged.py` - Conversation state management
- `response_cache.py` - Response caching for low-latency
- `voice_chat.py`, `voice_chat_simple.py` - Voice interface variants

**Integration Points**:

- Gemini API for TTS
- Local audio I/O
- Session persistence
- Clipboard integration for cross-tool communication

---

### 6. Core MCP Server

**Purpose**: Model Context Protocol bridge for tool orchestration

**Architecture**:

```
External Tools ←→ Core MCP Server ←→ AGI Core ←→ Personas
```

**Files**:

- `core_mcp_server.py` - Core MCP server
- `core_mcp_api_server.py` - API layer

**Protocol**:

- Tool discovery
- Context injection
- Response routing
- Error handling

**Use Cases**:

- VS Code extension communication
- External tool integration
- Multi-agent coordination

**Health Check**:

- Script: `scripts/core_quick_probe.ps1`
- Response: Sena persona ping acknowledgment

---

### 7. Monitoring & Operations

**Unified Dashboard**:

- **Script**: `scripts/quick_status.ps1`
- **Modes**:
  - Standard: Console output
  - Alert: `--AlertOnDegraded`
  - Log: `--LogJsonl`
  - JSON Export: `--OutJson`
  - Adaptive: `--UseAdaptiveThresholds`

**Health Gates**:

```
AGI Health Gate → BQI Status → Evidence Accumulation → 
System Resources → LLM Connectivity → Alert Dispatch
```

**Monitoring Components**:

1. **System Health**:
   - `scripts/system_health_check.py`
   - CPU, memory, disk, process checks

2. **AGI Health**:
   - `fdo_agi_repo/scripts/check_health.ps1`
   - Resonance ledger integrity
   - Evidence index validation
   - Recent activity checks

3. **Canary Health**:
   - `LLM_Unified/ion-mentoring/scripts/check_monitoring_status.ps1`
   - Service availability
   - Response time tracking
   - Error rate monitoring

**Report Generation**:

- **Script**: `scripts/generate_monitoring_report.ps1`
- **Outputs**:
  - `monitoring_report_latest.md` - Human-readable summary
  - `monitoring_metrics_latest.json` - Metrics for automation
  - `monitoring_dashboard_latest.html` - Interactive dashboard
  - `monitoring_events_latest.csv` - Event log
- **Windows**: 1h, 6h, 24h, 7d

**Alert System**:

- **Script**: `fdo_agi_repo/scripts/alert_system.ps1`
- **Triggers**:
  - Health gate failures
  - Evidence accumulation stalls
  - Canary degradation
  - Resource exhaustion
- **Channels**: Console, log file, future: email/SMS/Slack

**Scheduled Monitoring**:

- **Collector**: Every 5 minutes (status snapshots)
  - Script: `scripts/register_monitoring_collector_task.ps1`
- **Snapshot Rotation**: Daily 03:15 (archive old snapshots)
  - Script: `scripts/register_snapshot_rotation_task.ps1`
- **Daily Maintenance**: Daily 03:20 (cleanup + reporting)
  - Script: `scripts/register_daily_maintenance_task.ps1`

---

### 8. ChatOps & Automation

**Natural Language Command Router**:

- **Script**: `scripts/chatops_router.ps1`
- **Usage**: `chatops_router.ps1 -Say "상태 보여줘"`

**Supported Intents**:

- 상태/status → Unified dashboard
- AGI 상태 → AGI health check
- AGI 24시간 요약 → Ledger summary
- BQI Phase 6 학습 → Run Phase 6 learner
- 카나리 상태 → Canary status
- 카나리 X% 올려 → Deploy canary at X%
- 카나리 롤백 → Emergency rollback
- 온보딩 가이드 → Open onboarding docs
- 시크릿 등록해줘 → Install YouTube secret
- 방송 시작해줘 → Start streaming
- 방송 멈춰 → Stop streaming
- 봇 켜줘/꺼줘 → Start/stop YouTube bot
- 씬 X로 바꿔줘 → Switch OBS scene
- oauth → OAuth setup
- preflight → Pre-flight checks
- dry-run → Dry-run mode

**Intent Parsing**:

```
User Natural Language → Regex Pattern Matching → 
Script Invocation → Output Formatting → Response
```

**Integration**:

- Calls existing PowerShell/Python scripts
- Aggregates outputs
- Formats for readability
- Handles errors gracefully

---

### 9. Streaming & YouTube Integration

**OBS WebSocket Control**:

- **Script**: `scripts/obs_ws_control.py`
- **Commands**: ping, start, stop, status, list, switch
- **Dependency**: `obsws-python` package
- **Port**: OBS WebSocket default (4455)

**YouTube Bot**:

- **Script**: `scripts/youtube_live_bot.py`
- **Modes**: Auto-reply, dry-run
- **OAuth**: `scripts/youtube_oauth_setup.py`
- **Dependencies**: `google-api-python-client`, `google-auth`

**Streaming Workflow**:

```
1. Start AI Dev + OBS (YouTube Studio) → OBS opens, scene set, YouTube Studio browser
2. Run YouTube Bot (Auto-Reply) → Monitors live chat, responds with LLM
3. Monitor stream health → Check OBS status, chat activity
4. Stop stream + snapshot → Stop OBS, export monitoring snapshot
```

**Onboarding**:

- **Task**: "YouTube: Quick Onboarding (guided)"
- **Steps**:
  1. Install dependencies (`setup_youtube_bot_env.ps1`)
  2. Copy client secret (`install_youtube_client_secret.ps1`)
  3. Run OAuth + preflight (`youtube_bot_preflight.ps1 -Interactive`)

---

### 10. Cache Management

**Response Cache**:

- **Module**: `response_cache.py`
- **Purpose**: Low-latency LLM response retrieval
- **Storage**: JSON cache files in `outputs/`

**Cache Validation**:

- **Analysis**: `scripts/analyze_cache_effectiveness.py`
  - Output: `cache_analysis_latest.md`, `cache_analysis_latest.json`
  - Metrics: Hit rate, miss rate, latency improvement, staleness

- **Timeline Monitor**: `scripts/cache_monitor_timeline.py`
  - Windows: 12h/24h with 1h/2h buckets
  - Output: `cache_timeline_latest.md`

- **Quick Verification**: `scripts/quick_cache_verify.py`
  - Recent 1h cache health check

**Automated Validation**:

- **Scheduled Tasks**: 12h, 24h, 7d intervals
  - Script: `scripts/register_cache_validation_tasks.ps1`
  - Auto-notification on anomalies
- **Background Monitor**: Continuous cache health daemon
  - Script: `scripts/start_cache_validation_monitor.ps1`
  - Stops: Kill pwsh/powershell processes matching daemon pattern

**Cache Correlation**:

- **Sena Correlation**: `scripts/correlate_sena_with_ledger.py`
  - Windows: 10m, 30m
  - Cross-checks cache usage with resonance ledger activity
  - Output: `sena_correlation_latest.md`, `sena_correlation_latest.json`

---

## Data Architecture

### Storage Hierarchy

```
D:\nas_backup/
├── fdo_agi_repo/
│   ├── memory/
│   │   └── resonance_ledger.jsonl          [Append-only event log]
│   ├── knowledge_base/
│   │   ├── evidence_index*.json            [Validated patterns]
│   │   └── corpus.jsonl                    [Learning corpus]
│   ├── outputs/
│   │   ├── [persona]/                      [Persona-specific conversations]
│   │   ├── monitoring/                     [System metrics]
│   │   └── bqi*/                           [BQI models & reports]
│   └── configs/
│       ├── persona_registry*.json          [Persona definitions]
│       └── phase_controller*.yaml          [Phase control config]
│
├── LLM_Unified/
│   ├── session_memory/
│   │   ├── parsed_conversations.jsonl      [Complete conversation history]
│   │   └── agent_systems/                  [Agent state persistence]
│   └── ion-mentoring/outputs/
│       ├── locust_*.csv                    [Load test results]
│       ├── rate_limit_probe_*.json         [Rate limit data]
│       └── monitoring_*.jsonl              [Canary monitoring logs]
│
└── outputs/                                 [Cross-system analytics]
    ├── quick_status_latest.json
    ├── monitoring_report_latest.md
    ├── cache_analysis_latest.json
    └── nas_backup_analysis/                [This analysis]
```

### Key Data Flows

#### 1. User Interaction → Resonance Ledger

```
User Input → Persona Processing → Action Execution → 
Outcome Observation → Ledger Entry (timestamp, persona, action, result, resonance)
```

#### 2. Ledger → Evidence Index

```
Ledger Analysis (batch) → Pattern Extraction → 
Validation → Evidence Entry (context, pattern, confidence, examples)
```

#### 3. Evidence → Phase Controller

```
Evidence Quality Metrics → Threshold Evaluation → 
Phase Injection Decision → Controller Update → Persona Behavior Adjustment
```

#### 4. BQI Learning Loop

```
Ledger Snapshot → Pattern Learner → Model Update → 
Online Learner → Weight Adjustment → Ensemble Prediction → 
Feedback Collection → Ledger Entry [Loop]
```

#### 5. Monitoring Flow

```
System Probes (5min intervals) → Status Snapshot → 
Aggregation → Dashboard Generation → Alert Evaluation → 
Notification Dispatch (if needed)
```

---

## Technology Stack

### Languages & Runtimes

- **PowerShell**: 5.1+ (automation, orchestration, monitoring)
- **Python**: 3.13.7 (AGI core, learning, API servers)
- **Shell/Bash**: Linux/Git Bash scripts
- **Batch**: Legacy automation

### Python Ecosystem

**Core Libraries**:

- `google-cloud-aiplatform` - Vertex AI integration
- `vertexai` - Gemini LLM access
- `transformers` - NLP models
- `torch` - Deep learning
- `pandas` - Data manipulation
- `numpy` - Numerical computing

**API & Web**:

- `fastapi` - HTTP API framework
- `uvicorn` - ASGI server
- `httpx` - Async HTTP client
- `pydantic` - Data validation

**Testing & Load**:

- `pytest` - Unit/integration tests
- `locust` - Load testing

**Utilities**:

- `sqlalchemy` - Database ORM
- `pyyaml` - YAML parsing
- `click` - CLI framework
- `rich` - Terminal formatting

### External Services

- **Google Cloud Platform**:
  - Vertex AI (Gemini Pro/Flash/Vision)
  - Cloud Run (containerized API services)
  - Cloud Storage (potential backups)
- **GitHub**: Version control, CI/CD (potential)
- **OBS Studio**: Streaming software
- **YouTube**: Live streaming platform

### Development Tools

- **VS Code**: Primary IDE
- **Gitko Extension**: Custom AGI integration
- **Git**: Version control
- **PowerShell ISE**: Script development
- **Python venv**: Dependency isolation

---

## Deployment Architecture

### Local Development

```
C:\workspace\agi/  [Active development, NVMe SSD, 3-8x faster]
D:\nas_backup/     [Source repository, HDD, historical reference]
```

### Cloud Deployment

```
Local Build → Docker Image → Cloud Run Deployment → 
Traffic Split (Canary) → Monitoring → Rollback/Promote
```

**Services**:

- `ion-api` (legacy): Stable production service
- `ion-api-canary` (new): Canary deployment for testing

**Deployment Process**:

1. Local testing (`quick_status.ps1`, health checks)
2. Docker build (assumed, not explicitly in scripts)
3. Deploy canary at 5% (`deploy_phase4_canary.ps1 -CanaryPercentage 5`)
4. Monitor (`compare_canary_vs_legacy.ps1`, `rate_limit_probe.ps1`)
5. Gradual rollout (10% → 25% → 50% → 100%)
6. Emergency rollback if issues (`emergency_rollback.ps1 -Force`)

**Infrastructure as Code**:

- Terraform configs (in `session_memory/terraform/`)
- Kubernetes manifests (in `session_memory/kubernetes/`)

---

## Security & Reliability

### Authentication

- **YouTube OAuth**: `youtube_client_secret.json` (gitignored)
- **Google Cloud**: Service account credentials (environment variables)
- **API Keys**: Stored in environment or secure config files

### Error Handling

- **PowerShell**: Try-Catch blocks with `-ErrorAction SilentlyContinue`
- **Python**: Exception handling with logging
- **Health Gates**: Fail-fast on critical errors, degrade gracefully on warnings

### Data Integrity

- **Resonance Ledger**: Append-only, immutable event log
- **Evidence Index**: Versioned (e1, e2, e3), backup before updates
- **Monitoring Logs**: Timestamped, rotated daily
- **Snapshots**: Zipped archives after rotation

### Backup Strategy

- **Active System**: C:\workspace\agi (NVMe SSD, active development)
- **Historical Archive**: D:\nas_backup (HDD, 34.1 GB source of truth)
- **Monitoring Archives**: `outputs/archive_snapshots_YYYYMMDD.zip`
- **Evidence Backups**: `knowledge_base/evidence_index_backup_*.json`

### Disaster Recovery

- **Emergency Rollback**: One-command canary rollback
- **Health Gate Failures**: Automatic alert, manual intervention required
- **Data Corruption**: Restore from evidence index backups
- **Service Outage**: Fallback to legacy `ion-api` service

---

## Performance Characteristics

### Migration Impact (D:\ → C:\)

- **File Operations**: 3-8x faster (HDD → NVMe SSD)
- **Data**: 61,914 files, 2.16 GB migrated
- **Task Queue Server**: Online, responsive
- **Python Startup**: Faster (Python 3.13.7 on SSD)

### LLM Response Times

- **Cached**: Sub-100ms (response_cache.py)
- **Uncached**: ~2-5s (Vertex AI latency)
- **With Rate Limit**: +500ms-2s buffer
- **Multi-turn**: +100-300ms state management overhead

### BQI Learning

- **Pattern Learner**: ~30-60s for 24h ledger
- **Online Learner**: ~5-10s per update cycle
- **Feedback Predictor**: ~20-40s for model training
- **Ensemble Monitor**: ~10-20s for metric aggregation

### Monitoring

- **Quick Status**: 2-5s (local checks)
- **AGI Health Gate**: 5-10s (ledger + evidence validation)
- **24h Report**: 30-60s (full aggregation)
- **7d Report**: 1-2 minutes (historical analysis)

### Analysis Scale (This Document)

- **Files Analyzed**: 141,995
- **Directories**: 15,504
- **Size**: 34.1 GB
- **Analysis Time**: ~30-60 seconds (PowerShell script)
- **CSV Generation**: 13 files in <5 seconds

---

## Integration Patterns

### 1. Clipboard Orchestration

```yaml
# configs/clipboard_orchestration.yaml
persona_comms:
  - trigger: clipboard_change
  - read: clipboard_content
  - route_to: [Core, Sena]
  - action: tool_invocation or context_injection
```

### 2. Resonance-Based Coordination

```python
# Pseudo-code
def coordinate_personas(task):
    initial_persona = select_by_specialty(task)
    result = initial_persona.execute(task)
    log_to_ledger(initial_persona, task, result, resonance_score)
    
    if requires_handoff(result):
        next_persona = select_by_resonance_history(task_context)
        return next_persona.execute(task, context=result)
    
    return result
```

### 3. Evidence-Driven Behavior

```python
# Pseudo-code
def make_decision(context):
    relevant_evidence = query_evidence_index(context)
    confidence = aggregate_confidence(relevant_evidence)
    
    if confidence > threshold:
        return apply_evidence_pattern(relevant_evidence, context)
    else:
        return fallback_strategy(context)
```

### 4. Phase Injection

```yaml
# phase_controller_e3.yaml
phases:
  - id: e1
    features: [basic_persona, simple_orchestration]
    enabled: true
  - id: e2
    features: [multi_persona, evidence_index, bqi_learning]
    enabled: true
    depends_on: [e1]
  - id: e3
    features: [online_learning, ensemble_methods, meta_analysis]
    enabled: true
    depends_on: [e2]
    evidence_threshold: 80%
```

### 5. Canary Routing

```python
# Simplified
def route_request(request):
    if random() < canary_percentage / 100:
        return canary_service.handle(request)
    else:
        return legacy_service.handle(request)
```

---

## Operational Procedures

### Daily Startup Checklist

1. Run `.\scripts\quick_status.ps1` (unified status)
2. Check `.\fdo_agi_repo\scripts\check_health.ps1` (AGI health)
3. Verify Task Queue Server: `curl http://localhost:8091/api/health`
4. Review overnight alerts (if any)
5. Check BQI scheduled task logs (03:10, 03:15, 03:20)

### Before Deployment

1. Run local health checks
2. Review `generate_monitoring_report.ps1 -Hours 24`
3. Dry-run canary: `deploy_phase4_canary.ps1 -DryRun`
4. Verify evidence accumulation (no stalls in past 24h)
5. Confirm no active alerts

### During Incident

1. Check `quick_status.ps1 -AlertOnDegraded`
2. Review recent logs in `fdo_agi_repo/logs/`
3. Inspect resonance ledger tail: `Get-Content memory\resonance_ledger.jsonl -Tail 100`
4. If canary issue: Run `emergency_rollback.ps1 -Force`
5. Generate incident report: `generate_monitoring_report.ps1 -Hours 1`

### End of Day

1. Review `generate_monitoring_report.ps1 -Hours 24`
2. Check BQI learning outputs (`outputs/bqi_pattern_model.json`)
3. Verify cache effectiveness (`analyze_cache_effectiveness.py`)
4. Confirm scheduled tasks ran successfully
5. Archive important outputs if needed

---

## Extension Points

### Adding New Personas

1. Define in `configs/persona_registry.json`:

   ```json
   {
     "name": "NewPersona",
     "type": "category_type",
     "specialty": "specific_task",
     "output_dir": "outputs/newpersona/"
   }
   ```

2. Create output directory
3. Update phase controller if phase-specific
4. Add routing logic in orchestration layer
5. Test with simple tasks, observe ledger entries

### Adding New Monitoring Metrics

1. Collect data in `scripts/quick_status.ps1` or new script
2. Export to CSV/JSON in `outputs/`
3. Update `generate_monitoring_report.ps1` to include new metrics
4. Add to dashboard template (`monitoring_dashboard_latest.html`)
5. Configure alerts in `alert_system.ps1` if needed

### Adding New ChatOps Commands

1. Edit `scripts/chatops_router.ps1`
2. Add regex pattern in intent matching:

   ```powershell
   if ($Say -match "new command pattern") {
       & "target_script.ps1" -Parameters $Values
   }
   ```

3. Test with various phrasings
4. Document in README or help command

### Adding New Evidence Sources

1. Collect new evidence (conversations, experiments, benchmarks)
2. Extract patterns (manual or scripted)
3. Validate quality (precision, recall, confidence)
4. Merge into `knowledge_base/evidence_index.json`:

   ```json
   {
     "context": "...",
     "pattern": "...",
     "confidence": 0.85,
     "examples": [...],
     "metadata": {...}
   }
   ```

5. Test with relevant queries

---

## Known Limitations & Future Work

### Current Constraints

- **Encoding**: PowerShell scripts must be ASCII-only (no Korean in source code)
- **Rate Limits**: Vertex AI rate limits require careful throttling
- **Cache Staleness**: Response cache may serve outdated responses if not validated
- **Manual Rollback**: Some deployment failures require manual intervention
- **Single Machine**: Current setup not distributed, single point of failure

### Planned Enhancements

- **RAG Index Reindexing**: Refresh vector store with updated embeddings
- **Multi-modal Integration**: Extend vision capabilities, audio processing
- **Distributed Orchestration**: Multi-machine deployment for resilience
- **Advanced Meta-Learning**: Phase 7+ improvements
- **Real-time Dashboards**: WebSocket-based live monitoring
- **Automated Rollback**: AI-driven anomaly detection + auto-rollback

---

## Appendix: File Statistics

### Top Directories by File Count

1. `LLM_Unified/.venv/` - 26,176 files (Python dependencies)
2. `scripts/` - 220+ files (automation)
3. `outputs/` - 1,007 files (historical data)
4. `docs/` - 174 files (documentation)
5. `session_memory/` - 117 files (session persistence)

### Top File Extensions

1. `.py` - Python modules (21,576+)
2. `.ps1` - PowerShell scripts (20,272)
3. `.md` - Markdown docs (1,500+)
4. `.json` - Data/config (9,270+)
5. `.jsonl` - Logs/events (included in .json count)

### Largest Files (>10MB)

- Total: 85 files
- Categories: Conversation logs, visualizations, parsed archives, evidence indices
- Locations: Primarily in `outputs/`, `session_memory/`

### Analysis Output Files

Located in `C:\workspace\agi\outputs\nas_backup_analysis/`:

- `directory_structure.csv` (15,504 entries)
- `file_extensions_stats.csv`
- `file_size_distribution.csv`
- `large_files.csv` (85 entries)
- `document_inventory.csv` (5,941 entries)
- `document_categories.csv`
- `script_inventory.csv` (41,848 entries)
- `data_assets.csv` (9,270 entries)
- `config_files.csv` (83 entries)
- `python_modules.csv` (21,576 entries)
- `timeline.csv`
- `monthly_activity.csv`
- `summary.json`

---

**End of Architecture Overview**

*For high-level system understanding, see KNOWLEDGE_MAP.md. For detailed CSV data, see `outputs/nas_backup_analysis/`.*
