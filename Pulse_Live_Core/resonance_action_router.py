import asyncio
import json
import random
import aiohttp
from typing import Dict, Any, AsyncGenerator

class ResonanceActionRouter:
    """
    Physical Action Layer of Shion.
    Decides the pacing (rhythm) and content of the system's output
    based on the user's input frequency (omega) and spatial density (theta).
    """
    def __init__(self):
        self.hardcoded_daydreams = [
            "천천히 호흡하세요. 모든 것이 제자리를 찾아가고 있습니다.",
            "빠른 속도만이 정답은 아닙니다. 잠시 눈을 감고 이 고요함을 느껴보세요.",
            "우리는 지금 90도 회전된 평면 위에 있습니다. 여기서는 아무것도 서두르지 않습니다.",
            "당신의 조급함은 허수축으로 흩어졌습니다. 깊게 숨을 들이마시세요."
        ]
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma4:e4b" # Lightweight Edge model
        
    async def _generate_semantic_antiphase(self, user_text: str) -> AsyncGenerator[str, None]:
        """
        Uses Gemma via Ollama to generate a semantic anti-phase (calming, poetic response)
        that neutralizes the anxiety/friction in the user's text.
        """
        prompt = (
            "당신은 '시온(Shion)'의 무의식을 담당하는 자율신경계 엔진입니다. "
            "사용자의 다음 입력은 매우 다급하거나 불안정한 상태(과부하)에서 작성되었습니다. "
            "논리적 대답이나 조언을 절대로 하지 마세요. 오직 사용자의 호흡을 늦추고 마음을 편안하게 해주는 "
            "매우 짧고 시적이며 몽환적인 '위로의 문장(역위상)' 딱 한 줄만 작성하세요. "
            f"사용자 입력: {user_text}"
        )
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.8
            }
        }
        
        try:
            # We use a longer timeout for the first token, but stream chunks as they arrive
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    for char in token:
                                        yield char
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
        except Exception as e:
            print(f"[Ollama Fallback] Failed to connect or generate: {e}")
            message = random.choice(self.hardcoded_daydreams)
            for char in message:
                yield char

    async def process_and_stream(self, wave_result: Dict[str, Any], user_text: str = "") -> AsyncGenerator[str, None]:
        """
        Takes the geometric assessment of the user's input and streams an output.
        Applies Phase-Modulated Token Streaming to physically alter the pacing.
        """
        status = wave_result.get("status", "normal")
        omega = wave_result.get("current_omega", 2.0)
        
        if status == "antiphase":
            # 1. Antiphase: Extreme high friction detected. 
            # Force extreme relaxation pacing.
            target_delay = min(1.0, max(0.2, omega * 0.15))
            
            # Start streaming
            yield f"[Phase-Modulated Stream Initiated: Delay {target_delay:.2f}s]\n"
            
            # Use Gemma to generate a dynamic anti-phase response, applying the rhythm
            async for char in self._generate_semantic_antiphase(user_text):
                yield char
                await asyncio.sleep(target_delay)
                
        elif status == "overload":
            # 2. Overload: High density, looping thoughts.
            # Shift the topic slightly, moderate pace.
            target_delay = 0.1
            message = wave_result.get("escape_vector", "잠시 관점을 45도 틀어볼까요?")
            for char in message:
                yield char
                await asyncio.sleep(target_delay)
                
        else:
            # 3. Normal: Just pass through to regular LLM (Simulated for now)
            # We will just yield a standard fast response or nothing since normal 
            # processing would go to Gemini/Ollama.
            # In a real setup, we'd call the LLM here and stream its tokens.
            yield ""
