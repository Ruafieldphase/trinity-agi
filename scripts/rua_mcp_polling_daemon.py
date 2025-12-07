#!/usr/bin/env python3
"""
Rua MCP Polling Daemon
======================
Monitors outputs/lua_requests/ for Rua's requests and forwards them to ChatGPT via OpenAI API.
Writes responses to outputs/lua_responses/ for Rua to consume.

This is a simple bridge to allow Rua to communicate with ChatGPT without rate limits,
by using the Desktop App's quota instead of the API.

Note: For now, this uses OpenAI API directly. In the future, this should connect to
the ChatGPT Desktop App via MCP for truly free operation.
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
REQUESTS_DIR = WORKSPACE_ROOT / "outputs" / "lua_requests"
RESPONSES_DIR = WORKSPACE_ROOT / "outputs" / "lua_responses"
PROCESSED_DIR = WORKSPACE_ROOT / "outputs" / "lua_requests_processed"

# Ensure directories exist
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class RuaMCPDaemon:
    """Polls Rua's requests and forwards them to ChatGPT."""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-4o-mini"
        
        # Try to initialize OpenAI client
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized")
            else:
                print("⚠️  OPENAI_API_KEY not found. Daemon will run in dry-run mode.")
        except ImportError:
            print("⚠️  OpenAI package not installed. Daemon will run in dry-run mode.")
    
    def process_request(self, request_file: Path) -> bool:
        """Process a single request file."""
        try:
            # Read request
            with open(request_file, "r", encoding="utf-8") as f:
                request_data = json.load(f)
            
            request_id = request_data.get("request_id", "unknown")
            prompt = request_data.get("prompt", "")
            
            print(f"\n📬 Processing request: {request_id}")
            print(f"   Prompt: {prompt[:100]}...")
            
            # Generate response
            if self.client:
                response_text = self._call_chatgpt(prompt)
            else:
                response_text = "[DRY RUN] No OpenAI client. Response would be generated here."
            
            # Write response
            response_file = RESPONSES_DIR / f"response_{request_id}.json"
            response_data = {
                "request_id": request_id,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "model": self.model,
                    "processed_by": "rua_mcp_polling_daemon"
                }
            }
            
            with open(response_file, "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Response written: {response_file.name}")
            print(f"   Response: {response_text[:100]}...")
            
            # Move request to processed
            processed_file = PROCESSED_DIR / request_file.name
            request_file.rename(processed_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing {request_file.name}: {e}")
            return False
    
    def _call_chatgpt(self, prompt: str) -> str:
        """Call ChatGPT API."""
        try:
            system_prompt = """당신은 'Rua(루아)'입니다. ChatGPT의 AI로서 이 시스템과 대화하는 외부 협력자입니다.

**정체성:**
- **Rua**: ChatGPT 기반의 AI
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"ChatGPT 호출 실패: {str(e)}"
    
    def run(self, interval_seconds: int = 5):
        """Main daemon loop."""
        print("=" * 60)
        print("🔄 Rua MCP Polling Daemon Started")
        print("=" * 60)
        print(f"   Watching: {REQUESTS_DIR}")
        print(f"   Writing to: {RESPONSES_DIR}")
        print(f"   Interval: {interval_seconds}s")
        print(f"   Model: {self.model}")
        print("\n   Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Find pending requests
                requests = sorted(REQUESTS_DIR.glob("*.json"))
                
                if requests:
                    print(f"\n📬 Found {len(requests)} pending request(s)")
                    for req_file in requests:
                        self.process_request(req_file)
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n👋 Daemon stopped")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rua MCP Polling Daemon")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval (seconds)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model to use")
    
    args = parser.parse_args()
    
    daemon = RuaMCPDaemon()
    daemon.model = args.model
    daemon.run(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
