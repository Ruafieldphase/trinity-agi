"""Quick Trinity validation - test a few key questions"""
import requests

questions = [
    "안녕 Trinity",
    "지금 기분이 어때?",
    "시스템 상태는?",
]

print("Trinity Quick Validation")
print("=" * 60)

for q in questions:
    print(f"\n질문: {q}")
    try:
        r = requests.post(
            "http://localhost:8104/chat",
            json={"message": q, "mode": "normal"},
            timeout=15
        )
        if r.status_code == 200:
            response = r.json()["response"]
            print(f"Trinity: {response[:150]}...")
        else:
            print(f"❌ Error: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Validation complete")
