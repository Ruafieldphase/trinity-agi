# AI System Architecture Analysis - Complete Overview

**Analysis Date:** 2025-11-03
**Working Directory:** C:\workspace\agi
**System Status:** Fully Operational and Integrated

---

## Executive Summary

This AI system is a sophisticated, multi-layered architecture implementing an advanced self-managing, autonomously orchestrated system with:

- **Core Engine:** Dialectical reasoning framework (Thesis/Antithesis/Synthesis)
- **Orchestration:** Rhythm-based (Master Scheduler + Adaptive Scheduler + Event Detector)
- **LLM Integration:** Local LM Studio + Cloud APIs (Gemini, Vertex AI, Claude)
- **Containerization:** Docker + Docker Compose infrastructure
- **Self-Management:** Autonomous recovery, dependency management, health monitoring
- **Communication:** Multi-persona system with resonance-based feedback loops

---

## 1. HIGH-LEVEL SYSTEM ARCHITECTURE

### System Layers

The system is organized into 5 primary layers:

**PRESENTATION LAYER**
- Web Dashboard (Grafana, Prometheus)
- CLI Tools (PowerShell, Python scripts)
- Health Reports (JSON, Markdown)

**ORCHESTRATION LAYER**
- Master Scheduler (Consolidated Task Manager)
- Adaptive Scheduler (Dynamic Load Optimization)
- Event Detector (Anomaly & Self-Healing)
- Rhythm System (Central Control Hub)
- Self-Managing Agent (Autonomous Recovery)

**CORE REASONING ENGINE**
- Pipeline (Central Execution)
- Thesis Persona (Opportunity Explorer)
- Antithesis Persona (Risk Challenger)
- Synthesis Persona (Integration & Conclusions)
- Meta-Cognition System (Reflective Analysis)
- Self-Correction System (Quality Assurance)
- Evidence & Learning Systems (Knowledge Base)

**LLM INTEGRATION LAYER**
- LM Studio Local (Default: EEVE-Korean-10.8B)
- Google Gemini (Backup/Cloud)
- Google Vertex AI (Enterprise)
- Claude (Optional integration)
- LLM Client (Provider-agnostic wrapper)

**INFRASTRUCTURE LAYER**
- Docker Containers (Postgres, Redis, API Server)
- Database (PostgreSQL for persistence)
- Cache (Redis for performance)
- Task Queue (HTTP-based job distribution)
- Monitoring (Prometheus, Grafana, Health Checks)


---

## 2. SYSTEM COMPONENTS & ORGANIZATION

### 2.1 Main Directory Structure

```
C:\workspace\agi/
├── fdo_agi_repo/              # PRIMARY EXECUTION ENVIRONMENT
│   ├── orchestrator/          # Core reasoning engine & pipeline
│   ├── personas/              # Thesis, Antithesis, Synthesis
│   ├── monitor/               # Health monitoring & metrics
│   ├── tools/                 # Tool registry & execution
│   ├── agents/                # Agent implementations (LLM-based)
│   ├── configs/               # Configuration files (YAML)
│   └── requirements.txt       # Python dependencies
│
├── scripts/                    # ORCHESTRATION & AUTOMATION
│   ├── adaptive_master_scheduler.ps1    # Phase 2: Dynamic optimization
│   ├── ai_ops_manager.ps1              # Operations manager
│   ├── ai_agent_scheduler.ps1          # Task scheduler
│   ├── auto_resume_on_startup.ps1      # Auto-recovery on reboot
│   ├── ai_performance_agent.ps1        # Performance analysis
│   └── rune/                  # Rune/Learning system
│
├── LLM_Unified/               # Core GATEWAY & API INTEGRATIONS
│   └── ion-mentoring/         # Multi-persona API server
│       ├── Dockerfile        # Container image for cloud deployment
│       ├── .env              # Feature flags & configuration
│       ├── app/              # FastAPI application
│       └── persona_system/   # Persona implementations
│
├── session_memory/            # PERSISTENCE LAYER
│   ├── docker-compose.yml    # PostgreSQL + Redis + monitoring
│   └── Dockerfile           # Custom API server image
│
├── configs/                   # SYSTEM-WIDE CONFIGURATIONS
│   ├── resonance_config.json      # Quality policies & thresholds
│   ├── persona_registry.json      # Persona definitions & backends
│   └── phase_controller_e*.yaml   # Phase configurations
│
├── knowledge_base/            # EPISODIC MEMORY & EVIDENCE
│   └── evidence_index.json    # Evidence database
│
└── outputs/                   # STATE & MONITORING OUTPUTS
    ├── active_context.json        # Current execution context
    ├── health_snapshots/          # System health history
    ├── performance_metrics_*.json  # Performance data
    ├── monitoring_events_*.csv     # Event log
    └── *.jsonl                     # Structured event logs
```

### 2.2 Core Orchestration Components

| Component | File | Purpose | Language |
|-----------|------|---------|----------|
| Master Scheduler | `scripts/adaptive_master_scheduler.ps1` | Phase 1: Consolidates 42 independent tasks | PowerShell |
| Adaptive Scheduler | `scripts/adaptive_master_scheduler.ps1` | Phase 2: Dynamic interval adjustment | PowerShell |
| Event Detector | Phase 3 Ready | Anomaly detection & self-healing | Python/PS1 |
| AI Ops Manager | `scripts/ai_ops_manager.ps1` | Operations automation | PowerShell |
| Self-Managing Agent | `fdo_agi_repo/orchestrator/self_managing_agent.py` | Autonomous recovery | Python |
| Work Planner | `fdo_agi_repo/orchestrator/autonomous_work_planner.py` | Post-task queue | Python |

### 2.3 Core Reasoning Engine

| Component | File | Purpose |
|-----------|------|---------|
| Pipeline | `fdo_agi_repo/orchestrator/pipeline.py` | Main execution coordinator |
| Thesis | `fdo_agi_repo/personas/thesis.py` | Opportunity/seed exploration |
| Antithesis | `fdo_agi_repo/personas/antithesis.py` | Risk/boundary challenge |
| Synthesis | `fdo_agi_repo/personas/synthesis.py` | Integration & conclusions |
| Meta-Cognition | `fdo_agi_repo/orchestrator/meta_cognition.py` | Reflective analysis |
| Self-Correction | `fdo_agi_repo/orchestrator/self_correction.py` | Quality gate & passes |
| Response Cache | `fdo_agi_repo/orchestrator/response_cache.py` | LLM caching (Phase 2.5) |

### 2.4 Integration & Communication

| Component | File | Purpose |
|-----------|------|---------|
| LLM Client | `fdo_agi_repo/orchestrator/llm_client.py` | Provider-agnostic LLM wrapper |
| Config Manager | `fdo_agi_repo/orchestrator/config.py` | Central config management |
| Memory Bus | `fdo_agi_repo/orchestrator/memory_bus.py` | JSONL async message bus |
| Resonance Bridge | `fdo_agi_repo/orchestrator/resonance_bridge.py` | Feedback loop & evaluation |
| Event Emitter | `fdo_agi_repo/orchestrator/event_emitter.py` | Event-driven architecture |
| Tool Registry | `fdo_agi_repo/orchestrator/tool_registry.py` | Function/tool discovery |

### 2.5 Monitoring & Analysis

| Component | File | Purpose |
|-----------|------|---------|
| Metrics Collector | `fdo_agi_repo/monitor/metrics_collector.py` | Real-time performance data |
| Health Monitor | `fdo_agi_repo/monitor/health_monitor.py` | System health checking |
| Dashboard | `fdo_agi_repo/monitor/dashboard.py` | Web dashboard |
| Slack Notifier | `fdo_agi_repo/monitor/slack_notifier.py` | Alert notifications |
| AB Tester | `fdo_agi_repo/monitor/ab_tester.py` | A/B testing framework |

---

## 3. LM STUDIO INTEGRATION

### 3.1 Default Configuration

```yaml
Provider:          "local_proxy"
Model:             "yanolja_-_EEVE-Korean-Instruct-10.8B-v1.0"
Endpoint:          "http://localhost:8080/v1/chat/completions"
Timeout:           30-180 seconds (configurable)
Fallback Model:    Google Gemini (GEMINI_API_KEY required)
Enterprise:        Google Vertex AI (GOOGLE_CLOUD_PROJECT required)
```

**File:** `/c/workspace/agi/fdo_agi_repo/orchestrator/llm_client.py`

### 3.2 LM Studio Communication

Request format (OpenAI-compatible):
```json
{
    "model": "yanolja_-_eeve-korean-instruct-10.8b-v1.0",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "temperature": 0.3,
    "n": 1,
    "stream": false
}
```

### 3.3 Multiple Backend Support

**File:** `/c/workspace/agi/configs/persona_registry.json`

Supports multiple local backends:
- local_lmstudio (primary)
- local_ollama
- gemini_cli
- claude_cli
- And more (echo, perplexity, chatgpt)

