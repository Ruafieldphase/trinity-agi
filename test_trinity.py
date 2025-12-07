"""
Trinity Comprehensive Test Suite
Tests all aspects of Trinity v1.0 unified chat system
"""
import requests
import json
from typing import Dict, Any

def test_service_health(port: int, service_name: str) -> bool:
    """Test if a service is healthy"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=3)
        if response.status_code == 200:
            print(f"✅ {service_name} (port {port}): HEALTHY")
            return True
        else:
            print(f"❌ {service_name} (port {port}): UNHEALTHY (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {service_name} (port {port}): UNREACHABLE ({str(e)})")
        return False

def test_trinity_chat(question: str, mode: str = "normal") -> Dict[str, Any]:
    """Test Trinity chat with a question"""
    try:
        response = requests.post(
            "http://localhost:8104/chat",
            json={"message": question, "mode": mode},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", ""),
                "mode": data.get("mode", ""),
                "layer": data.get("layer", "")
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print("Trinity System Validation Suite")
    print("=" * 60)
    print()
    
    # Test 1: Service Health Checks
    print("TEST 1: Service Health Checks")
    print("-" * 60)
    services = [
        (8100, "Consciousness API"),
        (8101, "Unconscious Stream"),
        (8102, "Background Self API"),
        (8104, "Unified Aggregator")
    ]
    
    healthy_count = 0
    for port, name in services:
        if test_service_health(port, name):
            healthy_count += 1
    
    print(f"\nResult: {healthy_count}/{len(services)} services healthy")
    print()
    
    if healthy_count < len(services):
        print("⚠️ Not all services are healthy. Cannot proceed with chat tests.")
        return
    
    # Test 2: Trinity Normal Mode Conversations
    print("TEST 2: Trinity Normal Mode (Unified Persona)")
    print("-" * 60)
    
    test_questions = [
        "안녕",
        "지금 기분이 어때?",
        "시스템 상태는?",
        "너는 누구야?",
        "무엇을 하고 있어?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}] 질문: {question}")
        result = test_trinity_chat(question, mode="normal")
        
        if result["success"]:
            print(f"✅ 응답 받음 (mode: {result['mode']}, layer: {result['layer']})")
            print(f"Trinity: {result['response'][:200]}...")
        else:
            print(f"❌ 실패: {result['error']}")
    
    print()
    
    # Test 3: Debug Mode
    print("TEST 3: Debug Mode (3-Layer Breakdown)")
    print("-" * 60)
    
    result = test_trinity_chat("테스트", mode="debug")
    if result["success"]:
        print(f"✅ Debug mode 응답 받음")
        print(f"응답: {result['response'][:300]}...")
    else:
        print(f"❌ Debug mode 실패: {result['error']}")
    
    print()
    print("=" * 60)
    print("Validation Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
