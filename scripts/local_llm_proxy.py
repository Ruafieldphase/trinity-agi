#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 LLM 프록시 서버
http://localhost:8080/v1/chat/completions 요청을 Core Gateway로 포워딩
"""

from flask import Flask, request, jsonify
import requests
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORE_GATEWAY_URL = os.getenv(
    "CORE_GATEWAY_URL",
    "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat",
)

# Optional direct Cloud AI path for short/quick queries (feature flag)
CLOUD_AI_URL = os.getenv(
    "CLOUD_AI_URL",
    "https://ion-api-64076350717.us-central1.run.app/chat",
)
FAST_ROUTE_ENABLED = os.getenv("FAST_ROUTE_ENABLED", "0") in {"1", "true", "True"}
FAST_ROUTE_SHORT_LEN = int(os.getenv("FAST_ROUTE_SHORT_LEN", "64"))

# Persistent HTTP session for connection pooling (reduces handshake overhead)
_session = requests.Session()
_session.headers.update(
    {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "User-Agent": "local-llm-proxy/1.0",
    }
)
# Conservative retries only on connection errors; avoid request duplication at app layer
_retries = Retry(total=0, backoff_factor=0)
_adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=_retries)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)
_gateway_timeout = float(os.getenv("GATEWAY_TIMEOUT", "30"))

@app.route('/', methods=['GET'])
def root():
    """기본 루트 엔드포인트"""
    return jsonify({
        "status": "ok",
        "service": "local-llm-proxy",
        "description": "Proxies Local LLM requests to Core Gateway"
    })

@app.route('/health', methods=['GET'])
def health():
    """헬스체크 엔드포인트"""
    return jsonify({
        "status": "ok",
        "service": "local-llm-proxy",
        "forwarding_to": CORE_GATEWAY_URL
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """모델 목록 (호환성용)"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "core-gateway",
                "object": "model",
                "created": 1677610602,
                "owned_by": "Core"
            }
        ]
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI 호환 /v1/chat/completions 엔드포인트
    Core Gateway로 변환 후 포워딩
    """
    try:
        data = request.get_json()
        logger.info(f"Received request: {data}")
        
        # OpenAI 형식 -> Core 형식 변환
        messages = data.get('messages', [])
        last_message = messages[-1].get('content', '') if messages else ''
        
        core_payload = {"message": last_message}
        
        # Core Gateway 호출
        # Fast-route: small prompts can go directly to Cloud AI for lower latency
        target_url = CORE_GATEWAY_URL
        if FAST_ROUTE_ENABLED and isinstance(last_message, str) and len(last_message) <= FAST_ROUTE_SHORT_LEN:
            target_url = CLOUD_AI_URL
            logger.info(
                "Fast-route enabled: using Cloud AI for short prompt (%s chars)",
                len(last_message),
            )

        logger.info(f"Forwarding to: {target_url}")
        response = _session.post(
            target_url,
            json=core_payload,
            timeout=_gateway_timeout,
        )
        
        if response.status_code == 200:
            core_data = response.json()
            
            # Core 응답 -> OpenAI 형식 변환
            import time
            openai_response = {
                "id": f"chatcmpl-proxy-{os.urandom(6).hex()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "Core-gateway",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": core_data.get('response', '')
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(last_message) // 4,
                    "completion_tokens": len(core_data.get('response', '')) // 4,
                    "total_tokens": (len(last_message) + len(core_data.get('response', ''))) // 4
                },
                "core_metadata": {
                    "persona": core_data.get('persona'),
                    "sources": core_data.get('sources'),
                    "timestamp": core_data.get('timestamp')
                }
            }
            
            logger.info(f"Success: Persona={core_data.get('persona', {}).get('name')}")
            return jsonify(openai_response)
        else:
            logger.error(f"Core Gateway error: {response.status_code}")
            return jsonify({
                "error": {
                    "message": f"Core Gateway returned {response.status_code}",
                    "type": "gateway_error",
                    "code": response.status_code
                }
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "proxy_error"
            }
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PROXY_PORT', '8080'))
    logger.info(f"Starting Local LLM Proxy on port {port}")
    logger.info(f"Forwarding to: {CORE_GATEWAY_URL}")
    app.run(host='0.0.0.0', port=port, debug=False)
