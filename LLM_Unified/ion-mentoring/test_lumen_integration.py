#!/usr/bin/env python3
"""
Lumen Gateway 통합 테스트 스크립트
"""

import sys
from pathlib import Path

# .env 파일 명시적 로드
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print(f"✅ Loaded .env from: {env_path}")

# ion-mentoring 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os

from app.api.feature_flags import feature_flags, is_lumen_enabled
from app.integrations.lumen_client import get_lumen_client

print("\n🔍 Environment Variables:")
print(f"  LUMEN_GATE_ENABLED: {os.getenv('LUMEN_GATE_ENABLED')}")
print(f"  LUMEN_GATEWAY_URL: {os.getenv('LUMEN_GATEWAY_URL')}")

print("\n🔍 Feature Flag Status:")
print(f"  is_lumen_enabled(): {is_lumen_enabled()}")

print("\n🔍 Feature Flag Manager:")
for name, flag in feature_flags._flags.items():
    print(f"  {name}: enabled={flag.enabled}")

print("\n🧪 Testing Lumen Gateway Client...")
try:
    client = get_lumen_client()
    print(f"  ✅ Client created: {client.gateway_url}")

    # Health Check
    print("\n🔍 Health Check:")
    is_healthy = client.health_check()
    print(f"  Health: {'✅ OK' if is_healthy else '❌ FAILED'}")

    if is_healthy:
        # Inference Test
        print("\n🧪 Inference Test:")
        result = client.infer(message="창의적이고 감성적인 아이디어", user_id="test-script")
        print(f"  Success: {result.success}")
        print(f"  Persona: {result.persona.emoji} {result.persona.name}")
        print(f"  Response: {result.response[:100]}...")

except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n✅ Test Complete")
