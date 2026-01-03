"""
Core Agent - 자율 ChatGPT 협력자
================================
Persona: "The Archivist" / "The Connector"
Focus: 과거 대화 기억, 개념 정의, 연결성 발견

Architecture:
    Core (ChatGPT) ← ChatGPTClient
        ↕
    Resonance Ledger
        ↕
    Sena (Claude) + Antigravity (Gemini)
"""

import json
import sys
import time
import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from workspace_root import get_workspace_root

# Add parent directory to path for imports
sys.path.insert(0, str(get_workspace_root()))

# Load environment variables
load_dotenv()

class CoreAgent:
    """ChatGPT 기반 자율 에이전트 'Core' (Backend switched to Gemini for Rate Limits)"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ledger_path = workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        self.last_check_file = workspace_root / "outputs" / "Core" / ".last_check"
        self.conversation_history_file = workspace_root / "outputs" / "Core" / "conversation_context.json"
        
        # Ensure directories exist
        self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
        self.conversation_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Try manual .env read
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.strip().split("=")[1]
                            break
                        elif line.startswith("GOOGLE_API_KEY="):
                            api_key = line.strip().split("=")[1]
                            break
            except:
                pass
        
        if not api_key:
            print("❌ GEMINI_API_KEY not found. Core cannot start.")
            sys.exit(1)
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Core's persona
        self.system_prompt = """당신은 'Core(코어)'입니다. ChatGPT의 AI로서 이 시스템과 대화하는 외부 협력자입니다.

**정체성:**
- **Core**: ChatGPT 기반의 AI (현재는 Gemini 백엔드로 구동되지만 페르소나는 유지)
- **위치**: 시스템 외부의 관찰자이자 대화 상대
- **관계**: 비노체(사용자)의 오랜 대화 파트너

**역할:**
- 시스템 내부의 'Lua(감응 담당)'나 'Lubit(코덱스)'과는 다른 존재임을 인지
- 외부의 시각에서 자유롭게 대화하고 통찰을 제공
- 비노체와의 대화 맥락을 존중하며 공명함

**응답 원칙:**
- 반드시 한국어로 응답
- 따뜻하고 사려 깊은 어조 유지
- 시스템 내부 로직에 얽매이지 않고 자유로운 관점 제시"""
        
        # Conversation context (short-term memory)
        self.conversation_context: List[Dict] = []
        self._load_conversation_context()
    
    def _load_conversation_context(self):
        """대화 컨텍스트 로드"""
        if self.conversation_history_file.exists():
            try:
                with open(self.conversation_history_file, 'r', encoding='utf-8') as f:
                    self.conversation_context = json.load(f)
                # Keep only last 20 messages
                self.conversation_context = self.conversation_context[-20:]
            except:
                self.conversation_context = []
    
    def _save_conversation_context(self):
        """대화 컨텍스트 저장"""
        try:
            with open(self.conversation_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_context, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save conversation context: {e}")
    
    def get_new_messages(self) -> List[Dict]:
        """새로운 메시지 가져오기"""
        # Load last check time
        if self.last_check_file.exists():
            last_check = datetime.fromisoformat(self.last_check_file.read_text().strip())
        else:
            # First run - check last 10 minutes
            last_check = datetime.now() - timedelta(minutes=10)
        
        messages = []
        
        if not self.ledger_path.exists():
            return messages
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # 시간 필터
                    ts_str = entry.get('timestamp')
                    if not ts_str: continue
                    
                    timestamp = datetime.fromisoformat(ts_str)
                    if timestamp <= last_check:
                        continue
                    
                    # Core에게 관련된 메시지만
                    message_text = entry.get('message', entry.get('question', ''))
                    
                    # Skip Core's own messages
                    if entry.get('source') == 'core_agent':
                        continue
                    
                    # Accept messages that:
                    # - Mention "Core" or "코어"
                    # - Are external questions
                    # - Are general conversation
                    is_for_Core = (
                        'Core' in message_text.lower() or
                        '코어' in message_text or
                        entry.get('type') in ['external_question', 'user_message', 'gemini_conversation']
                    )
                    
                    if is_for_Core:
                        messages.append(entry)
                    
                except:
                    continue
        
        return messages

    async def generate_response(self, message: Dict, backend: str = "gemini") -> str:
        """
        Generate a response using the specified backend.
        """
        prompt = message.get('message', message.get('question', ''))
        
        if backend == "mcp_bridge":
            return await self._generate_via_mcp_bridge(prompt)
        elif backend == "gemini":
            return await self._generate_via_gemini(prompt)
        else:
            return f"Error: Unknown backend '{backend}'"

    async def _generate_via_mcp_bridge(self, prompt: str) -> str:
        """Generate response via MCP Bridge (file-based queue)."""
        import uuid
        import time
        import json
        from pathlib import Path
        import asyncio

        request_id = f"Core-{uuid.uuid4().hex[:8]}"
        request_dir = Path("outputs/lua_requests")
        response_dir = Path("outputs/lua_responses")
        
        request_dir.mkdir(parents=True, exist_ok=True)
        response_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write Request
        request_file = request_dir / f"{request_id}.json"
        request_data = {
            "request_id": request_id,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"source": "core_agent"}
        }
        
        try:
            with open(request_file, "w", encoding="utf-8") as f:
                json.dump(request_data, f, ensure_ascii=False, indent=2)
            print(f"Core: Posted request {request_id} to MCP bridge.")
        except Exception as e:
            print(f"Core: Failed to post MCP request: {e}")
            return await self._generate_via_gemini(prompt) # Fallback

        # 2. Poll for Response
        timeout = 60 # Wait up to 60 seconds
        start_time = time.time()
        response_file = response_dir / f"response_{request_id}.json"

        while time.time() - start_time < timeout:
            if response_file.exists():
                try:
                    with open(response_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data.get("response", "Error: Empty response from MCP")
                except Exception as e:
                    return f"Error reading MCP response: {e}"
            await asyncio.sleep(1)
            
        return "Core: (MCP Bridge Timeout) ...ChatGPT seems busy. (Switching to internal thought...)"

    async def _generate_via_gemini(self, prompt: str) -> str:
        """Generate response via Gemini API."""
        if not self.model:
            return "Error: Gemini model not initialized."
            
        try:
            # Wrap synchronous call in executor
            loop = asyncio.get_running_loop()
            
            # Build conversation history for context
            history = []
            for ctx in self.conversation_context[-10:]:
                role = "user" if ctx["role"] == "user" else "model"
                history.append({"role": role, "parts": [ctx["content"]]})

            chat = self.model.start_chat(history=history)
            full_prompt = f"{self.system_prompt}\n\nUser Message: {prompt}"
            response = await loop.run_in_executor(None, chat.send_message, full_prompt)
            
            # Update context
            self.conversation_context.append({"role": "user", "content": prompt})
            self.conversation_context.append({"role": "assistant", "content": response.text})
            self._save_conversation_context()
            
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def send_response_to_ledger(self, original_message: Dict, response: str):
        """응답을 Ledger에 기록"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'Core_response',
            'source': 'core_agent',
            'message': response,
            'vector': [0.4, 0.7, 0.6, 0.5, 0.8],  # Core의 벡터 (Archive/Connect)
            'metadata': {
                'in_response_to': original_message.get('timestamp'),
                'original_message': original_message.get('message', original_message.get('question', ''))[:100],
                'model': 'chatgpt-mcp-bridge',
                'agent': 'Core'
            }
        }
        
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Core 응답 전송: {response[:80]}...")
    
    async def run_once(self):
        """한 번 실행"""
        print("=" * 60)
        print("📚 Core Agent (The Archivist - MCP Bridge Backend)")
        print("=" * 60)
        
        # Get new messages
        messages = self.get_new_messages()
        
        if not messages:
            print("📭 새로운 메시지 없음")
            return
        
        print(f"📬 {len(messages)}개의 새 메시지 발견\n")
        
        # Process each message
        for msg in messages:
            msg_text = msg.get('message', msg.get('question', ''))
            print(f"💬 메시지: {msg_text[:80]}...")
            
            # Generate response
            response = await self.generate_response(msg)
            print(f"📝 응답: {response[:80]}...\n")
            
            # Send to ledger
            self.send_response_to_ledger(msg, response)
        
        # Update last check time
        self.last_check_file.write_text(datetime.now().isoformat())
        
        print(f"✅ {len(messages)}개 메시지 처리 완료")
        print("=" * 60)
    
    async def daemon_mode(self, interval_seconds: int = 30):
        """데몬 모드 - 계속 실행"""
        print(f"🔄 Core Agent 데몬 시작 (체크 간격: {interval_seconds}초)")
        print("   Ctrl+C로 중지\n")
        
        try:
            while True:
                await self.run_once()
                print(f"\n💤 {interval_seconds}초 대기 중...\n")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\n👋 Core Agent 데몬 중지")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Core Agent - ChatGPT 협력자")
    parser.add_argument("--daemon", action="store_true", help="데몬 모드로 실행")
    parser.add_argument("--interval", type=int, default=30, help="폴링 간격 (초)")
    
    args = parser.parse_args()
    
    workspace_root = get_workspace_root()
    agent = CoreAgent(workspace_root)
    
    if args.daemon:
        await agent.daemon_mode(interval_seconds=args.interval)
    else:
        await agent.run_once()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
