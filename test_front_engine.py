"""프론트엔진 디버깅 테스트"""
import requests
import json

BASE_URL = "http://127.0.0.1:8104"

def test_front_engine():
    print("=" * 60)
    print("통합 프론트엔진 디버깅 테스트")
    print("=" * 60)
    
    # 1. 상태 확인
    print("\n[1] 상태 확인")
    resp = requests.get(f"{BASE_URL}/front-engine/status")
    status = resp.json()
    print(f"  상태: {status['status']}")
    print(f"  시스템: {status['state']}")
    print(f"  레이어: {status['layers']}")
    print(f"  현재 모델: {status['current_model']}")
    
    # 2. 처리 테스트
    print("\n[2] 처리 테스트")
    test_cases = [
        {"input": "프론트엔진 구현해줘", "expected_rhythm": "normal", "expected_meaning": "CREATE"},
        {"input": "빨리 에러 고쳐줘!", "expected_rhythm": "urgent", "expected_meaning": "MODIFY"},
        {"input": "시스템 상태 어때?", "expected_rhythm": "normal", "expected_meaning": "QUERY"},
        {"input": "천천히 설명해줄래?", "expected_rhythm": "calm", "expected_meaning": "EXPLAIN"},
        {"input": "테스트 실행해줘", "expected_rhythm": "normal", "expected_meaning": "VERIFY"},
        {"input": "고마워, 잘 됐어", "expected_rhythm": "normal", "expected_meaning": "RESPOND"},
    ]
    
    passed = 0
    failed = 0
    
    for tc in test_cases:
        resp = requests.post(
            f"{BASE_URL}/front-engine/process",
            json={"input": tc["input"]},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        result = resp.json()
        
        rhythm_ok = result["rhythm"] == tc["expected_rhythm"]
        meaning_ok = result["meaning"] == tc["expected_meaning"]
        
        if rhythm_ok and meaning_ok:
            print(f"  [PASS] {tc['input']}")
            print(f"         rhythm={result['rhythm']}, meaning={result['meaning']}, model={result['action'].get('selected_model', 'N/A')}")
            passed += 1
        else:
            print(f"  [FAIL] {tc['input']}")
            print(f"         Expected: rhythm={tc['expected_rhythm']}, meaning={tc['expected_meaning']}")
            print(f"         Got:      rhythm={result['rhythm']}, meaning={result['meaning']}")
            failed += 1
    
    print(f"\n[결과] {passed} passed, {failed} failed")
    
    # 3. 분기 확인
    print("\n[3] 유동성 분기 확인")
    urgent_test = requests.post(
        f"{BASE_URL}/front-engine/process",
        json={"input": "빨리 에러 고쳐줘!"}
    ).json()
    print(f"  입력: 빨리 에러 고쳐줘!")
    print(f"  분기: {' → '.join(urgent_test['branch_history'])}")
    print(f"  역할 수행:")
    for layer, roles in urgent_test['roles_performed'].items():
        print(f"    {layer}: {roles}")
    
    # 4. 접힘/펼침 테스트
    print("\n[4] 접힘/펼침 상태 테스트")
    # 접힘
    resp = requests.post(f"{BASE_URL}/front-engine/fold")
    print(f"  fold → state: {resp.json()['state']}")
    
    # 펼침
    resp = requests.post(f"{BASE_URL}/front-engine/unfold")
    print(f"  unfold → state: {resp.json()['state']}")
    
    print("\n" + "=" * 60)
    print("디버깅 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    test_front_engine()
