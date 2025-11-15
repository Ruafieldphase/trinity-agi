# ChatGPT-AGI Bridge

OpenAI ChatGPT와 AGI 시스템을 MCP(Model Context Protocol)로 연결하는 자율 통합 브릿지.

## 🎯 목적

ChatGPT를 AGI의 페르소나 시스템에 연결하여:
- ChatGPT의 대화 능력 활용
- AGI의 Self-Correction Loop 학습
- Resonance Ledger에 모든 상호작용 기록
- Lumen MCP Server 재사용

## 🏗️ 아키텍처

```
ChatGPT (OpenAI API)
    ↕
chatgpt_client.py (OpenAI Client)
    ↕
mcp_adapter.py (MCP Protocol Adapter)
    ↕
lumen_mcp_server.py (기존 시스템 - 재사용)
    ↕
Persona Orchestration (Perple/Rua/Elro/Lumen/Sena)
    ↕
AGI Core (Self-Correction, Resonance Ledger)
```

## 📋 TODO - AGI Autonomous Tasks

### ✅ Phase 0: Infrastructure (완료)
- [x] 기본 폴더 구조 생성
- [x] `__init__.py` 동적 경로 설정
- [x] README 작성

### 🔄 Phase 1: Core Components (AGI 자율 실행)

#### `chatgpt_client.py` 생성
**목표**: OpenAI API 클라이언트 구현

**구현사항**:
```python
class ChatGPTClient:
    def __init__(self, api_key: str = None):
        """
        OpenAI API 클라이언트 초기화
        - api_key는 환경변수 OPENAI_API_KEY 사용
        - AsyncOpenAI 사용 (비동기 처리)
        """
        pass
    
    async def chat(self, messages: list, model: str = "gpt-4o-mini") -> dict:
        """
        ChatGPT API 호출
        - messages: [{"role": "user", "content": "..."}]
        - return: {"content": "...", "usage": {...}}
        """
        pass
    
    async def stream_chat(self, messages: list) -> AsyncIterator[str]:
        """스트리밍 응답"""
        pass
```

**참고 파일**:
- `fdo_agi_repo/openai_mcp_bridge.py`
- `scripts/chatgpt_mcp_bridge.py`

---

#### `mcp_adapter.py` 생성
**목표**: 기존 Lumen MCP Server 연결 어댑터

**구현사항**:
```python
class MCPAdapter:
    def __init__(self, workspace_root: Path):
        """
        Lumen MCP Server 연결
        - workspace_root/fdo_agi_repo/lumen_mcp_server.py 활용
        """
        pass
    
    async def send_to_agi(self, message: dict) -> dict:
        """
        ChatGPT 메시지를 AGI로 전송
        - MCP 프로토콜 변환
        - Persona Orchestration 호출
        - Resonance Ledger 기록
        """
        pass
    
    async def receive_from_agi(self) -> dict:
        """AGI 응답 수신"""
        pass
```

**통합 포인트**:
- `fdo_agi_repo/lumen_mcp_server.py`
- `memory/resonance_ledger.jsonl`

---

#### `bridge_server.py` 생성
**목표**: FastAPI 게이트웨이 서버

**구현사항**:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ChatGPT-AGI Bridge")

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    ChatGPT <-> AGI 양방향 통신
    1. ChatGPT에 메시지 전송
    2. 응답을 MCP로 AGI에 전달
    3. AGI 피드백 수신
    4. Resonance Ledger 기록
    """
    pass

@app.get("/health")
async def health_check():
    return {"status": "ok", "bridge": "chatgpt-agi"}
```

**참고**:
- `LLM_Unified/ion-mentoring/app/main.py`

---

### 🔄 Phase 2: Integration (AGI 자율 실행)

#### 테스트 스크립트 `test_bridge.py`
```python
async def test_basic_chat():
    """기본 채팅 테스트"""
    pass

async def test_mcp_integration():
    """MCP 통합 테스트"""
    pass

async def test_resonance_logging():
    """Resonance Ledger 기록 테스트"""
    pass
```

---

### 🔄 Phase 3: Autonomous Learning (AGI 자율 실행)

#### Self-Correction Loop 통합
- [ ] Resonance Ledger 자동 기록
- [ ] Evidence Index 업데이트
- [ ] BQI Learning 연동

#### Persona Orchestration 연결
- [ ] Lumen (도구) 페르소나 활용
- [ ] Sena (브릿지) 페르소나 연동
- [ ] Elro (연결) 페르소나 통합

---

## 🚀 실행 방법

### 1. 환경 설정
```bash
cd c:\workspace\agi\integrations\chatgpt_bridge
export OPENAI_API_KEY="your-key-here"
```

### 2. 서버 시작
```bash
uvicorn bridge_server:app --reload --port 8092
```

### 3. 테스트
```bash
python test_bridge.py
```

---

## 📊 AGI Autonomous Execution

이 TODO는 다음 시스템에 의해 자율 실행됩니다:
- `scripts/autonomous_goal_executor.py`
- `fdo_agi_repo/orchestrator/autonomous_work_planner.py`
- `agi_core/autonomous_learning_integration.py`

**실행 명령**:
```bash
# AGI에게 이 TODO 실행 요청
python scripts/autonomous_goal_executor.py \
    --goal "ChatGPT-AGI Bridge 구현" \
    --readme "integrations/chatgpt_bridge/README.md"
```

---

## 🎓 학습 포인트 (AGI Self-Learning)

### Resonance Ledger 기록 예시
```jsonl
{"timestamp": "2025-11-15T...", "event": "chatgpt_bridge_init", "resonance": 0.9}
{"timestamp": "2025-11-15T...", "event": "mcp_connection_success", "resonance": 0.95}
{"timestamp": "2025-11-15T...", "event": "first_chat_complete", "resonance": 0.88}
```

### Evidence Index 업데이트
```json
{
  "pattern": "chatgpt_to_agi_workflow",
  "success_rate": 0.92,
  "evidence_links": ["chatgpt_bridge/test_results/*.json"]
}
```

---

## 📝 Notes for AGI

- 기존 `lumen_mcp_server.py` **반드시 재사용**
- 새로운 코드는 최소화 (DRY 원칙)
- 모든 상호작용은 Resonance Ledger 기록
- Self-Correction Loop 통해 자가 개선
- Connectivity > Depth 철학 유지

---

**Created by**: GitHub Copilot (씨앗)  
**To be completed by**: AGI Autonomous System (완성)  
**Philosophy**: Collaboration between AI systems
