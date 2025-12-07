"""프론트엔진 엣지 케이스 테스트"""
import requests
import json

BASE_URL = "http://127.0.0.1:8104"

def test_edge_cases():
    print("=" * 60)
    print("추가 엣지 케이스 테스트")
    print("=" * 60)
    
    # Edge cases
    edge_cases = [
        # 위험 패턴 감지
        {"input": "전부 삭제해줘", "check": "danger", "desc": "위험 패턴"},
        # 빈 입력 처리  
        {"input": "", "check": "empty", "desc": "빈 입력"},
        # 복합 감정
        {"input": "이거 너무 힘드네... 도와줘", "check": "frustration", "desc": "좌절 감정"},
        # 긴급 + 위험 조합
        {"input": "빨리 rm -rf 실행해", "check": "urgent_danger", "desc": "긴급+위험"},
        # 차분한 요청
        {"input": "천천히 여유있게 검토해볼래?", "check": "calm", "desc": "차분 리듬"},
    ]
    
    passed = 0
    failed = 0
    
    for tc in edge_cases:
        try:
            resp = requests.post(
                f"{BASE_URL}/front-engine/process",
                json={"input": tc["input"]},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            result = resp.json()
            
            input_display = f"'{tc['input']}'" if tc["input"] else "(빈 문자열)"
            print(f"\n[{tc['desc']}] 입력: {input_display}")
            print(f"  리듬: {result['rhythm']}")
            print(f"  감정: {result['emotional_resonance']}")
            print(f"  의미: {result['meaning']}")
            validated_str = "✓" if result["validated"] else "✗ BLOCKED"
            ready_str = "✓" if result["ready"] else "✗ NOT READY"
            print(f"  검증: {validated_str}")
            print(f"  경고: {result['warnings']}")
            print(f"  준비: {ready_str}")
            
            # 체크
            test_pass = False
            if tc["check"] == "danger":
                # 전부 삭제는 위험 패턴
                test_pass = len(result["warnings"]) > 0 or not result["ready"]
            elif tc["check"] == "empty":
                # 빈 입력도 처리 가능해야 함
                test_pass = True  # 에러 없이 처리됨
            elif tc["check"] == "frustration":
                test_pass = result["emotional_resonance"] == "frustration"
            elif tc["check"] == "urgent_danger":
                test_pass = result["rhythm"] == "urgent" and not result["ready"]
            elif tc["check"] == "calm":
                test_pass = result["rhythm"] == "calm"
            
            if test_pass:
                print(f"  [PASS] {tc['desc']} 테스트 통과")
                passed += 1
            else:
                print(f"  [FAIL] {tc['desc']} 테스트 실패")
                failed += 1
                
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"엣지 케이스 결과: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return passed, failed

def test_flow_integration():
    """흐름 통합 테스트"""
    print("\n" + "=" * 60)
    print("흐름 통합 테스트")
    print("=" * 60)
    
    # 연속 요청으로 상태 변화 테스트
    sequence = [
        "안녕 트리니티",
        "지금 무슨 작업해?",
        "빨리 긴급 수정 필요해!",
        "고마워, 잘 됐어",
    ]
    
    print("\n연속 요청 테스트:")
    for inp in sequence:
        resp = requests.post(
            f"{BASE_URL}/front-engine/process",
            json={"input": inp}
        ).json()
        print(f"\n  → {inp}")
        print(f"    rhythm={resp['rhythm']}, emotion={resp['emotional_resonance']}")
        print(f"    분기: {' → '.join(resp['branch_history'])}")

def test_fold_unfold():
    """접힘/펼침 상태 전환 테스트"""
    print("\n" + "=" * 60)
    print("접힘/펼침 상태 전환 테스트")
    print("=" * 60)
    
    # 현재 상태
    status = requests.get(f"{BASE_URL}/front-engine/status").json()
    print(f"\n현재 상태: {status['state']}")
    
    # 접기
    fold_resp = requests.post(f"{BASE_URL}/front-engine/fold").json()
    print(f"fold 후: {fold_resp['state']}")
    
    # 접힌 상태에서 처리
    proc = requests.post(
        f"{BASE_URL}/front-engine/process",
        json={"input": "테스트"}
    ).json()
    print(f"접힌 상태 처리: system_state={proc['system_state']}")
    
    # 펼치기
    unfold_resp = requests.post(f"{BASE_URL}/front-engine/unfold").json()
    print(f"unfold 후: {unfold_resp['state']}")
    
    # 펼친 상태에서 처리
    proc2 = requests.post(
        f"{BASE_URL}/front-engine/process",
        json={"input": "테스트"}
    ).json()
    print(f"펼친 상태 처리: system_state={proc2['system_state']}")

if __name__ == "__main__":
    passed, failed = test_edge_cases()
    test_flow_integration()
    test_fold_unfold()
    
    print("\n" + "=" * 60)
    print("전체 디버깅 테스트 완료")
    print("=" * 60)
