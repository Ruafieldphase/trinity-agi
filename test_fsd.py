"""FSD 자율 실행 테스트"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8104"

def test_fsd_execute():
    print("=" * 60)
    print("FSD 자율 실행 테스트")
    print("=" * 60)
    
    # 자율 실행 시작
    goal = "윈도우 시작 메뉴를 열어주세요"
    
    print(f"\n🎯 Goal: {goal}")
    print("실행 시작...")
    
    try:
        r = requests.post(f"{BASE_URL}/fsd/execute", json={"goal": goal})
        result = r.json()
        print(f"실행 ID: {result.get('execution_id')}")
        
        # 상태 폴링
        execution_id = result.get('execution_id')
        for i in range(30):  # 최대 30초 대기
            time.sleep(1)
            status_r = requests.get(f"{BASE_URL}/fsd/status/{execution_id}")
            status = status_r.json()
            print(f"  [{i+1}s] Status: {status.get('status')}")
            
            if status.get('status') in ['completed', 'failed', 'not_found']:
                print(f"\n결과: {json.dumps(status.get('result', {}), indent=2, ensure_ascii=False)}")
                break
                
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_fsd_execute()
