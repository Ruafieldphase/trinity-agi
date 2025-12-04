#!/usr/bin/env python3
"""
ChatGPT + OpenAI API + MCP Integration Bridge
==============================================

이 스크립트는 ChatGPT와 OpenAI API를 MCP(Model Context Protocol)와 통합하여
자동화된 AI 워크플로우를 제공합니다.

주요 기능:
1. ChatGPT 대화를 MCP 도구로 변환
2. OpenAI API를 통한 자동 응답 생성
3. Lua 스크립트와의 브릿지 연결
4. VS Code 액션 자동 실행

Author: Ruafieldphase
Date: 2025-11-14
Philosophy: Connectivity > Depth
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# OpenAI API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not installed. Run: pip install openai")


class ChatGPTMCPBridge:
    """ChatGPT + OpenAI API + MCP 통합 브릿지"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.outputs_dir = workspace_root / "outputs" / "chatgpt_mcp"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일
        self.conversation_log = self.outputs_dir / "conversations.jsonl"
        self.mcp_actions_log = self.outputs_dir / "mcp_actions.jsonl"
        
        # OpenAI 클라이언트 초기화
        self.client = None
        if OPENAI_AVAILABLE:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                print("✅ OpenAI API initialized")
            else:
                print("⚠️  OPENAI_API_KEY not found in environment")
        
        # MCP 도구 매핑
        self.mcp_tools = {
            "create_file": self._mcp_create_file,
            "read_file": self._mcp_read_file,
            "edit_file": self._mcp_edit_file,
            "run_command": self._mcp_run_command,
            "search_code": self._mcp_search_code,
            "open_browser": self._mcp_open_browser,
        }
    
    def chat_with_gpt(self, prompt: str, model: str = "gpt-4o-mini") -> Optional[str]:
        """OpenAI ChatGPT API 호출"""
        if not self.client:
            print("❌ OpenAI client not initialized")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant integrated with VS Code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # 로그 저장
            self._log_conversation(prompt, answer, model)
            
            return answer
        
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None
    
    def extract_mcp_actions(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 MCP 액션 추출"""
        actions = []
        
        # 파일 생성 패턴
        create_file_pattern = r"create.*?file.*?[`'\"]([^`'\"]+)[`'\"]"
        for match in re.finditer(create_file_pattern, text, re.IGNORECASE):
            actions.append({
                "type": "create_file",
                "file_path": match.group(1),
                "content": ""  # 내용은 별도 추출 필요
            })
        
        # 파일 편집 패턴
        edit_pattern = r"edit.*?[`'\"]([^`'\"]+)[`'\"]"
        for match in re.finditer(edit_pattern, text, re.IGNORECASE):
            actions.append({
                "type": "edit_file",
                "file_path": match.group(1)
            })
        
        # 명령 실행 패턴
        run_pattern = r"run.*?[`'\"]([^`'\"]+)[`'\"]"
        for match in re.finditer(run_pattern, text, re.IGNORECASE):
            actions.append({
                "type": "run_command",
                "command": match.group(1)
            })
        
        return actions
    
    def execute_mcp_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 액션 실행"""
        action_type = action.get("type")
        
        if action_type not in self.mcp_tools:
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}"
            }
        
        try:
            result = self.mcp_tools[action_type](action)
            
            # 액션 로그 저장
            self._log_mcp_action(action, result)
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_conversation(self, user_input: str, auto_execute: bool = False) -> Dict[str, Any]:
        """
        대화 처리 워크플로우
        1. ChatGPT에 질문
        2. 응답에서 MCP 액션 추출
        3. (선택적) 자동 실행
        """
        print(f"\n💬 User: {user_input}")
        
        # 1. ChatGPT 응답
        gpt_response = self.chat_with_gpt(user_input)
        if not gpt_response:
            return {"success": False, "error": "Failed to get GPT response"}
        
        print(f"🤖 GPT: {gpt_response[:200]}...")
        
        # 2. MCP 액션 추출
        actions = self.extract_mcp_actions(gpt_response)
        print(f"\n🔧 Extracted {len(actions)} MCP actions")
        
        # 3. 자동 실행
        results = []
        if auto_execute and actions:
            print("\n⚡ Auto-executing actions...")
            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action['type']}: {action.get('file_path', action.get('command', ''))}")
                result = self.execute_mcp_action(action)
                results.append(result)
                
                if result.get("success"):
                    print(f"     ✅ Success")
                else:
                    print(f"     ❌ Failed: {result.get('error')}")
        
        return {
            "success": True,
            "gpt_response": gpt_response,
            "actions": actions,
            "execution_results": results if auto_execute else None
        }
    
    # MCP 도구 구현
    
    def _mcp_create_file(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """파일 생성 (MCP 도구)"""
        file_path = self.workspace / action["file_path"]
        content = action.get("content", "")
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return {"success": True, "file_path": str(file_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _mcp_read_file(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """파일 읽기 (MCP 도구)"""
        file_path = self.workspace / action["file_path"]
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _mcp_edit_file(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """파일 편집 (MCP 도구)"""
        # 간단 구현: 파일 존재 확인만
        file_path = self.workspace / action["file_path"]
        return {"success": file_path.exists(), "file_path": str(file_path)}
    
    def _mcp_run_command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """명령 실행 (MCP 도구)"""
        # 보안상 실제 실행은 하지 않고 로그만
        return {"success": True, "command": action["command"], "note": "Command logged, not executed"}
    
    def _mcp_search_code(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """코드 검색 (MCP 도구)"""
        query = action.get("query", "")
        return {"success": True, "query": query, "note": "Search logged"}
    
    def _mcp_open_browser(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """브라우저 열기 (MCP 도구)"""
        url = action.get("url", "")
        return {"success": True, "url": url, "note": "Browser action logged"}
    
    # 로깅
    
    def _log_conversation(self, prompt: str, response: str, model: str):
        """대화 로그"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "model": model
        }
        
        with open(self.conversation_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def _log_mcp_action(self, action: Dict[str, Any], result: Dict[str, Any]):
        """MCP 액션 로그"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result
        }
        
        with open(self.mcp_actions_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class LuaBridgeIntegration:
    """Lua 스크립트와의 브릿지 통합"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.lua_requests_dir = workspace_root / "outputs" / "lua_requests"
        self.lua_responses_dir = workspace_root / "outputs" / "lua_responses"
        
        self.lua_requests_dir.mkdir(parents=True, exist_ok=True)
        self.lua_responses_dir.mkdir(parents=True, exist_ok=True)
        
        self.bridge = ChatGPTMCPBridge(workspace_root)
    
    def process_lua_request(self, request_file: Path) -> Optional[Path]:
        """Lua 요청 파일 처리"""
        try:
            request_data = json.loads(request_file.read_text(encoding='utf-8'))
            
            prompt = request_data.get("prompt", "")
            request_id = request_data.get("request_id", "")
            
            # ChatGPT + MCP 처리
            result = self.bridge.process_conversation(prompt, auto_execute=False)
            
            # Lua 응답 파일 생성
            response_file = self.lua_responses_dir / f"response_{request_id}.json"
            response_data = {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "success": result.get("success", False),
                "response": result.get("gpt_response", ""),
                "actions": result.get("actions", [])
            }
            
            response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2), encoding='utf-8')
            
            print(f"✅ Lua response created: {response_file.name}")
            return response_file
        
        except Exception as e:
            print(f"❌ Error processing Lua request: {e}")
            return None
    
    def monitor_lua_requests(self, interval_seconds: int = 5):
        """Lua 요청 모니터링 (백그라운드)"""
        print(f"🔍 Monitoring Lua requests (interval: {interval_seconds}s)")
        print(f"   Watching: {self.lua_requests_dir}")
        
        processed_files = set()
        
        while True:
            try:
                for request_file in self.lua_requests_dir.glob("*.json"):
                    if request_file in processed_files:
                        continue
                    
                    print(f"\n📨 New Lua request: {request_file.name}")
                    response_file = self.process_lua_request(request_file)
                    
                    if response_file:
                        processed_files.add(request_file)
                        # 처리된 파일 이동
                        processed_dir = self.lua_requests_dir / "processed"
                        processed_dir.mkdir(exist_ok=True)
                        request_file.rename(processed_dir / request_file.name)
                
                time.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(interval_seconds)


def main():
    """메인 엔트리포인트"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT + OpenAI API + MCP Bridge")
    parser.add_argument("--workspace", type=Path, default=Path("c:/workspace/agi"),
                        help="Workspace root directory")
    parser.add_argument("--mode", choices=["chat", "monitor"], default="chat",
                        help="Operation mode")
    parser.add_argument("--prompt", type=str, help="Chat prompt (for chat mode)")
    parser.add_argument("--auto-execute", action="store_true",
                        help="Auto-execute MCP actions")
    parser.add_argument("--interval", type=int, default=5,
                        help="Monitor interval in seconds")
    
    args = parser.parse_args()
    
    if args.mode == "chat":
        # 대화 모드
        bridge = ChatGPTMCPBridge(args.workspace)
        
        if args.prompt:
            result = bridge.process_conversation(args.prompt, auto_execute=args.auto_execute)
            print(f"\n📊 Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("💬 Interactive Chat Mode")
            print("   Type 'quit' to exit\n")
            
            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ("quit", "exit", "q"):
                        break
                    
                    if not user_input:
                        continue
                    
                    result = bridge.process_conversation(user_input, auto_execute=args.auto_execute)
                
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
    
    elif args.mode == "monitor":
        # Lua 브릿지 모니터링 모드
        lua_bridge = LuaBridgeIntegration(args.workspace)
        lua_bridge.monitor_lua_requests(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
