"""Antigravity 실행 테스트"""
import requests
import json

BASE_URL = "http://127.0.0.1:8104"

def test_antigravity():
    print("=" * 60)
    print("Antigravity Executor 테스트")
    print("=" * 60)
    
    # 테스트 케이스들
    test_cases = [
        "메모장 열어줘",
        "스크린샷 찍어",
        "화면 중앙 클릭해줘",
        "크롬 열어",
        "계산기 켜줘",
    ]
    
    for inp in test_cases:
        print(f"\n[입력] {inp}")
        try:
            r = requests.post(f"{BASE_URL}/antigravity/process", json={
                "input": inp,
                "auto_execute": False
            })
            result = r.json()
            
            fe = result.get("front_engine", {})
            ex = result.get("execution", {})
            
            print(f"  의미: {fe.get('meaning')}")
            print(f"  리듬: {fe.get('rhythm')}")
            print(f"  모델: {fe.get('action', {}).get('selected_model')}")
            print(f"  실행 대기: {ex.get('pending_approval')}개")
            
            pending = ex.get("pending_requests", [])
            for req in pending:
                print(f"    → {req['type']}: {req.get('target') or req.get('params')}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    test_antigravity()
