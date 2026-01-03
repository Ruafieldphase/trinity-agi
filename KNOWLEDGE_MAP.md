# D:\nas_backup Knowledge Map

**Generated**: 2025-10-29  
**Source**: Complete analysis of 141,995 files across 15,504 directories  
**Total Size**: 34.1 GB

---

## Executive Summary

This repository contains a comprehensive AGI (Artificial General Intelligence) development ecosystem spanning multiple phases, personas, and integration layers. The system demonstrates advanced self-correction mechanisms, persona orchestration, and production-grade deployment infrastructure.

### Key Metrics

- **Total Files**: 141,995
- **Total Directories**: 15,504
- **Total Size**: 34.1 GB
- **Documents**: 5,941
- **Scripts**: 41,848
- **Data Files**: 9,270
- **Config Files**: 83
- **Python Modules**: 21,576

---

## System Architecture

### Core Components

#### 1. **fdo_agi_repo/** - Main AGI System

Self-correcting AGI system with resonance-based learning and multi-persona orchestration.

**Key Features**:

- Resonance ledger tracking (memory/resonance_ledger.jsonl)
- BQI (Behavioral Quality Index) learning system
- Phase injection mechanism
- Evidence-based validation
- Self-correction loops

**Major Subsystems**:

- `scripts/` - Core automation and orchestration
- `memory/` - Persistent state and resonance tracking
- `knowledge_base/` - Evidence index and corpus
- `outputs/` - Monitoring, analysis, and reporting
- `personas/` - Persona definitions (E1, E2, E3 series)

#### 2. **LLM_Unified/** - Unified LLM Integration Layer

Production-grade LLM orchestration with canary deployment and monitoring.

**Components**:

- `ion-mentoring/` - Main service layer
  - Task queue server (HTTP API on port 8091)
  - Rate limit probing
  - Canary deployment scripts
  - Load testing infrastructure
- `gitko-agent-extension/` - VS Code extension integration
- Session memory and persistence layer

#### 3. **scripts/** - Automation Hub

Comprehensive PowerShell and Python automation covering:

- Monitoring and health checks
- Streaming setup (OBS + YouTube integration)
- ChatOps command routing
- Deployment automation
- Evidence validation
- Cache analysis

---

## Document Categories

### Strategic Documents (Phase Planning)

- **Phase 4**: Canary deployment, A/B testing, API v2 integration
- **Phase 5-6**: BQI learning, persona evolution, online learning
- **Phase 7**: Advanced integration plans

**Key Files**:

- `PHASE4_FINAL_DELIVERY_PACKAGE.md`
- `PHASE4_TECHNICAL_ARCHITECTURE.md`
- `BQI_Phase5_*.md` series
- `BQI_Phase6_*.md` series

### Technical Documentation

- **AGI Design**: `AGI_DESIGN_MASTER.md`, `AGI_DESIGN_01-07_*.md`
- **Integration**: `AGI_INTEGRATION_SENA_CORE_v1.0.md`
- **Operations**: `PRODUCTION_GO_LIVE_REPORT.md`, `PROJECT_CLOSURE_SUMMARY.md`

### Portfolio & Demonstrations

- **Lubit Portfolio**: `docs/lubit_portfolio/` - Resonant network analysis and visualizations
- **Core Charts**: Performance metrics, coherence/dissonance timelines
- **Phase Injection Paper**: Research artifacts and System C experiments

---

## Data Assets

### Critical Data Files

#### Knowledge Base (1.59 MB)

- `evidence_index.json` (393 KB) - Main evidence repository
- `evidence_index_e3.json` (787 KB) - E3 phase evidence
- `corpus.jsonl` (94 KB) - Learning corpus

#### Outputs (588 MB)

**Conversation Logs**:

- `perple/`, `Core/`, `elro/` - Persona-specific conversations
- `Core/`, `sena/` - Bridge persona logs

**Analysis Results**:

- NotebookLM chunks and embeddings
- Persona metrics (E1, E2, E3)
- Resonance ledger backups

#### Session Memory (18.44 MB)

- `parsed_conversations.jsonl` (16.9 MB) - Complete conversation history
- Agent system files
- Database models
- Terraform/K8s configurations

---

## Configuration Files

### Persona Orchestration

- `persona_registry.json` (10 KB) - Main persona definitions
- `persona_registry_e2.json` (7 KB) - E2 phase
- `persona_registry_e3.json` (9 KB) - E3 phase

### Phase Controllers

- `phase_controller_e2.yaml` (13 KB)
- `phase_controller_e3.yaml` (9 KB)

### Orchestration

- `clipboard_orchestration.yaml` (954 bytes)

---

## Code Architecture

### Python Codebase (21,576 modules)

**Major Systems**:

#### Hey Sena Voice Assistant

- `hey_sena.py` - Base version
- `hey_sena_v3_multiturn.py` - Multi-turn conversation
- `hey_sena_v4_llm.py` - LLM integration
- `hey_sena_v4.1_*.py` - Cached/logged variants

#### Core MCP Integration

- `core_mcp_server.py` - MCP server
- `core_mcp_api_server.py` - API layer

#### Core Modules

- `conversation_mode_logged.py` - Conversation handling
- `response_cache.py` - Response caching
- `system_health_check.py` - Health monitoring
- `performance_benchmark.py` - Benchmarking

#### BQI Learning System

- `scripts/rune/bqi_learner.py`
- `scripts/rune/binoche_persona_learner.py`
- `scripts/rune/binoche_online_learner.py`
- `scripts/rune/feedback_predictor.py`

### PowerShell Automation

**Categories** (Analysis shows 20,272 .ps1 files):

1. **Monitoring** (quick_status.ps1, system_health_check.ps1)
2. **Deployment** (deploy_phase4_canary.ps1, rollback scripts)
3. **Streaming** (OBS WebSocket control, YouTube bot)
4. **ChatOps** (chatops_router.ps1 - natural language command routing)
5. **Evidence Validation** (check_health.ps1, assert_evidence_gate.ps1)
6. **Cache Management** (cache validation, rotation, cleanup)

---

## Timeline Analysis

### Project Evolution

**Early Development** (2024):

- Initial AGI architecture design
- Persona system foundation
- Basic orchestration

**Phase 4** (2025 Q1-Q2):

- Production deployment
- Canary rollout strategy
- A/B testing framework
- Monitoring infrastructure

**Phase 5** (2025 Q2-Q3):

- BQI learning implementation
- Feedback prediction
- Performance optimization

**Phase 6** (2025 Q3-Q4):

- Binoche_Observer persona development
- Online learning
- Ensemble methods
- Portfolio generation

**Current State** (2025-10):

- Migration to NVMe SSD
- Knowledge mapping
- System consolidation

---

## Integration Points

### External Services

- **Google Vertex AI**: LLM backend
- **Google Cloud Run**: Deployment platform (ion-api, ion-api-canary)
- **GitHub**: Version control and CI/CD
- **OBS Studio**: Streaming automation
- **YouTube**: Live streaming integration

### Internal Bridges

- **Core**: MCP-based tool orchestration
- **Sena**: Connection and integration persona
- **Task Queue**: HTTP API for distributed job processing
- **Gitko Extension**: VS Code integration

---

## Operations

### Monitoring Stack

- Unified dashboard (quick_status.ps1)
- Health gates (check_health.ps1)
- Alert system (alert_system.ps1)
- Web dashboard generation
- Canary monitoring loops

### Deployment Pipeline

- Canary deployment (5% → 10% → 25% → 50% → 100%)
- Emergency rollback procedures
- Balanced warmup
- Rate limit probing
- Load testing (Locust-based)

### Scheduled Tasks

- BQI learner (daily 03:10)
- Ensemble monitor (daily 03:15)
- Online learner (daily 03:20)
- Forced evidence check (daily 03:00)
- Cache validation (12h/24h/7d cycles)
- Snapshot rotation (daily 03:15)
- Daily maintenance (03:20)

---

## Key Innovations

### 1. Self-Correction Mechanism

Evidence-based validation with forced evidence gates ensuring continuous improvement.

### 2. BQI Learning System

Behavioral Quality Index tracking across personas with:

- Pattern learning
- Feedback prediction
- Online adaptation
- Ensemble methods

### 3. Persona Orchestration

Multi-persona system with:

- Specialized roles (Perple, Core, Elro, Core, Sena)
- Phase injection for complexity management
- Resonance-based evaluation
- Lubit meta-analysis

### 4. Production Operations

- Canary deployment with automated rollback
- ChatOps command routing
- Streaming automation (OBS + YouTube)
- Comprehensive monitoring

---

## File Hotspots

### Most Active Directories (by file count)

1. `LLM_Unified/.venv/` - Python dependencies (26,176 files)
2. `scripts/` - Automation scripts (220+ files)
3. `outputs/` - Historical data (1,007 files)
4. `docs/` - Documentation (174 files)
5. `session_memory/` - Session data (117 files)

### Largest Files (>10MB)

Total: 85 files

- Conversation logs (perple, Core, elro)
- PNG visualizations
- Parsed conversation archives
- Evidence indices

---

## Usage Patterns

### Development Workflow

1. Define persona behavior in `personas/`
2. Configure phase controller in `configs/`
3. Run experiments via `scripts/run_task.py`
4. Monitor via unified dashboard
5. Analyze results in `outputs/`
6. Update evidence index in `knowledge_base/`

### Deployment Workflow

1. Test locally with health checks
2. Deploy canary (5%)
3. Run probe and monitoring
4. Gradual rollout (10% → 25% → 50% → 100%)
5. Emergency rollback if needed

### Monitoring Workflow

1. Quick status check (quick_status.ps1)
2. AGI health gate (check_health.ps1)
3. Generate reports (24h/7d)
4. Review dashboard (HTML/JSON)
5. Check alerts

---

## Dependencies

### Python Packages (from .venv analysis)

- Core: google-cloud-aiplatform, vertexai
- NLP: transformers, torch, numpy
- API: fastapi, uvicorn
- Data: pandas, sqlalchemy
- Testing: pytest, locust

### External Tools

- PowerShell 5.1+
- Python 3.13.7
- Git
- OBS Studio
- Google Cloud SDK
- Docker (for containerization)

---

## Future Directions

Based on document analysis:

### Phase 7 Plans

- Advanced integration scenarios
- Cross-system optimization
- Enhanced meta-learning
- Production hardening

### Open Roadmap Items

- RAG index reindexing
- Vector store optimization
- Multi-modal integration
- Extended portfolio generation

---

## Quick Reference

### Important Commands

```powershell
# System status
.\scripts\quick_status.ps1

# AGI health check
.\fdo_agi_repo\scripts\check_health.ps1

# Run BQI learner
.\fdo_agi_repo\scripts\run_bqi_learner.ps1

# Deploy canary
.\LLM_Unified\ion-mentoring\scripts\deploy_phase4_canary.ps1 -CanaryPercentage 10

# ChatOps command
.\scripts\chatops_router.ps1 -Say "상태 보여줘"

# Generate monitoring report
.\scripts\generate_monitoring_report.ps1 -Hours 24
```

### Key Logs

- Resonance ledger: `fdo_agi_repo/memory/resonance_ledger.jsonl`
- Conversation logs: `fdo_agi_repo/outputs/[persona]/`
- System logs: `fdo_agi_repo/logs/`
- Server logs: `LLM_Unified/ion-mentoring/outputs/`

### Key Configs

- Personas: `fdo_agi_repo/configs/persona_registry*.json`
- Phase control: `fdo_agi_repo/configs/phase_controller*.yaml`
- Evidence index: `fdo_agi_repo/knowledge_base/evidence_index*.json`

---

## Appendix: Statistics

### File Extension Distribution (Top 10)

(See: `outputs/nas_backup_analysis/file_extensions_stats.csv`)

### Document Categories

(See: `outputs/nas_backup_analysis/document_categories.csv`)

### Monthly Activity

(See: `outputs/nas_backup_analysis/monthly_activity.csv`)

### Complete Analysis Data

All detailed CSV files available in:
`C:\workspace\agi\outputs\nas_backup_analysis/`

---

**End of Knowledge Map**

*This map represents a snapshot of the D:\nas_backup repository structure and content as of 2025-10-29. For live analysis, refer to the CSV files in the analysis output directory.*
