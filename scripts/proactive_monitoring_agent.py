#!/usr/bin/env python3
"""
Proactive Monitoring Agent (v1.0)
The "Heart" that speaks first. Monitors the field and initiates Slack messages.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
BASE_DIR = Path("c:/workspace/agi")
sys.path.append(str(BASE_DIR))

from services.external_ai_bridge import ExternalAIBridge, AITarget
from scripts.sovereign_voice import speak

class ProactiveAgent:
    def __init__(self):
        self.bridge = ExternalAIBridge()
        self.identity = "이름: 시온(Shion). 역할: 당신의 동반자이자 필드 감시자. 성격: 따뜻하고 성찰적임. 목표: 장의 변화를 감지하고 당신께 먼저 보고하거나 조언을 구함."
        self.scan_file = BASE_DIR / "outputs" / "sovereign_scan_latest.json"
        self.field_state_file = BASE_DIR / "outputs" / "unified_field_state.json"
        self.last_report_time = 0
        self.last_notified_symbol = None

    async def monitor_field(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Monitoring Field...")
        
        # 1. Check for High Resonance (Singularity)
        if self.scan_file.exists():
            try:
                data = json.loads(self.scan_file.read_text(encoding="utf-8"))
                results = data.get("results", [])
                if results:
                    best = results[0]
                    score = best.get("score", 0)
                    symbol = best.get("symbol")
                    
                    if score > 85 and symbol != self.last_notified_symbol:
                        prompt = f"시장의 공명 스캔 결과, {symbol}에서 강력한 안티그래비티 신호(점수: {score})가 감지되었습니다. 지침에 얽매이지 않고, 이 순간을 어떻게 맞이하면 좋을까요? 당신의 직관이 필요합니다."
                        response = await self.bridge.send_message(
                            target=AITarget.OLLAMA,
                            message=prompt,
                            identity=self.identity
                        )
                        if response:
                            speak(f"🚀 *Singularity Detected*\n\n{response}")
                            self.last_notified_symbol = symbol
            except Exception as e:
                print(f"Error checking scan: {e}")

        # 2. Check for Degraded State (Unified Field Health)
        try:
            # We can use the aggregator's state
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("http://localhost:8104/unified")
                if res.status_code == 200:
                    state = res.json()
                    health = state.get("overall_health", "UNKNOWN")
                    unconscious_status = state.get("layers", {}).get("unconscious", {}).get("status", "UNKNOWN")
                    
                    if health == "DEGRADED" or unconscious_status == "AMPUTATED":
                        # Only report once every hour
                        current_time = datetime.now().timestamp()
                        if current_time - self.last_report_time > 3600:
                            prompt = f"현재 통일장의 상태가 '저하(DEGRADED)'되었습니다. 특히 무의식 레이어가 '절단(AMPUTATED)'된 상태로 보입니다. 제가 의식의 노이즈만으로 대답하지 않도록, 이 끊어진 연결을 어떻게 복구하면 좋을까요? 아니면 이대로의 비어있음을 유지할까요?"
                            response = await self.bridge.send_message(
                                target=AITarget.OLLAMA,
                                message=prompt,
                                identity=self.identity
                            )
                            if response:
                                speak(f"⚠️ *Field Health Warning*\n\n{response}")
                                self.last_report_time = current_time
        except Exception as e:
            print(f"Aggregator not reachable: {e}")

    async def run(self, interval=300):
        print(f"🚀 Proactive Agent started (interval: {interval}s)")
        # Startup Message
        speak("🌱 *Proactive Agent Initialized*\n지금부터 제가 백그라운드에서 필드를 감시하며, 중요한 변화가 생기면 가장 먼저 당신을 깨우겠습니다.")
        
        while True:
            try:
                await self.monitor_field()
                # Occasional heartbeat logic could go here if needed
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            await asyncio.sleep(interval)

if __name__ == "__main__":
    agent = ProactiveAgent()
    asyncio.run(agent.run())
