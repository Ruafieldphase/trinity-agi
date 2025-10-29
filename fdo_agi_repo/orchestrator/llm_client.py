from __future__ import annotations
from typing import Optional, Dict, Any
import json

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # 런타임에 미설치일 수 있음 (llm.enabled=false일 때는 영향 없음)


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
        # provider 분기
        if self.provider in (None, "", "disabled"):
            return None
        if self.provider == "local_proxy":
            return self._generate_via_local_proxy(system_prompt, user_prompt, **kwargs)
        # TODO: openai, anthropic, vertex 등 추가 구현
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
