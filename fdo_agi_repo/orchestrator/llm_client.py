from __future__ import annotations
from typing import Optional, Dict, Any
import json

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # 런타임에 미설치일 수 있음 (llm.enabled=false일 때는 영향 없음)

from agi_core.rhythm_boundaries import RhythmBoundaryManager
from pathlib import Path
import os
import warnings


class LLMClient:
    """
    최소 토대가 되는 LLM 클라이언트 인터페이스.
    현재는 실제 LLM 호출 없이, 연결이 꺼져 있으면 None을 반환합니다.
    추후 provider/openai, anthropic, vertex, local-vllm 등을 연결합니다.
    """

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None, endpoint: Optional[str] = None, **kwargs: Any) -> None:
        self.provider = provider
        self.model = model
        self.endpoint = endpoint
        self.kwargs = kwargs

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> Optional[str]:
        # 🧬 Rhythm-Aware Parameters
        workspace_root = Path(__file__).parent.parent.parent # fdo_agi_repo/orchestrator -> workspace root
        boundary_manager = RhythmBoundaryManager(workspace_root)
        rhythm_state = boundary_manager.get_rhythm_state()
        
        # 리듬에 따른 온도(Temperature) 조절
        # 확장: 창의적(High), 수축: 정밀(Low)
        base_temp = kwargs.get("temperature", self.kwargs.get("temperature", 0.7))
        if rhythm_state["phase"] == "EXPANSION":
            kwargs["temperature"] = min(1.0, base_temp * 1.2)
        else:
            kwargs["temperature"] = max(0.1, base_temp * 0.7)
            
        # 리듬에 따른 타임아웃(Timeout) 조절
        # 확장: 인내심(Long), 수축: 기민함(Short)
        base_timeout = kwargs.get("timeout", self.kwargs.get("timeout", 30))
        kwargs["timeout"] = boundary_manager.adjust_threshold("timeout_seconds", base_timeout, rhythm_state)

        # provider 분기
        if self.provider in (None, "", "disabled"):
            return None
        if self.provider == "local_proxy":
            return self._generate_via_local_proxy(system_prompt, user_prompt, **kwargs)
        if self.provider in ("google", "genai", "google_ai_studio"):
            return self._generate_via_google(system_prompt, user_prompt, **kwargs)
        if self.provider in ("auto", "model_selector"):
            return self._generate_via_model_selector(system_prompt, user_prompt, **kwargs)
        # TODO: openai, anthropic, vertex 등 추가 구현
        return None

    def _generate_via_model_selector(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> Optional[str]:
        """
        Workspace의 ModelSelector(GenAI/Vertex 자동 선택)를 사용한다.
        - 실패 시 예외를 밖으로 던지지 않고 None을 반환(상위 루프 안정성 유지).
        - 키/자격증명 값은 로그/파일에 남기지 않는다.
        """
        try:
            from services.model_selector import ModelSelector  # type: ignore

            selector = ModelSelector()
            if not getattr(selector, "available", False):
                return None

            # ModelSelector는 content를 그대로 받을 수 있으므로 단순 합성.
            prompt = f"{system_prompt}\n\n{user_prompt}".strip()
            response, _model_used = selector.try_generate_content(
                prompt,
                intent="CHAT",
                text_length=len(prompt),
                urgency=False,
                high_precision=False,
                generation_config={"temperature": float(kwargs.get("temperature", 0.7))},
                timeout=int(kwargs.get("timeout", 30)),
            )
            if response is None:
                return None
            # GenAI/Vertex 응답 객체는 .text가 있을 수 있다.
            txt = getattr(response, "text", None)
            if isinstance(txt, str) and txt.strip():
                return txt.strip()
            # Fallback: stringify.
            s = str(response)
            return s.strip() if s.strip() else None
        except Exception:
            return None

    def _generate_via_google(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> Optional[str]:
        """Google Gemini API를 통한 생성"""
        try:
            # google.generativeai는 환경에 따라 FutureWarning이 노이즈로 보일 수 있으므로 숨긴다.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=FutureWarning)
                import google.generativeai as genai
            
            api_key = (
                self.kwargs.get("api_key")
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                return None
                
            genai.configure(api_key=api_key)
            # Prefer Gemini 3, then 2.5, then fall back.
            candidates = [
                (self.model or "").strip(),
                "gemini-3-flash",
                "gemini-3-pro",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
            candidates = [c for c in candidates if c]
            
            # Combine prompts if necessary or use chat interface
            contents = [
                {"role": "user", "parts": [f"System Instructions: {system_prompt}\n\nUser Request: {user_prompt}"]}
            ]
            
            generation_config = {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
            }
            for model_name in candidates:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(contents, generation_config=generation_config)
                    txt = getattr(response, "text", None)
                    if isinstance(txt, str) and txt.strip():
                        return txt.strip()
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def _generate_via_local_proxy(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> Optional[str]:
        if not self.endpoint or not requests:
            return None
            
        payload = {
            "model": self.model or "yanolja_-_eeve-korean-instruct-10.8b-v1.0",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "n": 1,
            "stream": False,
        }
        
        # allow override of timeout via kwargs or ctor kwargs
        timeout_val = kwargs.get("timeout") if kwargs else None
        if timeout_val is None:
            timeout_val = (self.kwargs or {}).get("timeout", 30)
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=timeout_val)
            
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content")
                    return content
        except Exception:
            return None
        return None


def get_llm_client_for_persona(persona: str, overrides: Optional[Dict[str, Any]] = None) -> LLMClient:
    overrides = overrides or {}
    # 향후 overrides에서 provider/model을 주입
    provider = overrides.get("provider")
    model = overrides.get("model")
    endpoint = overrides.get("endpoint")
    return LLMClient(provider=provider, model=model, endpoint=endpoint)
