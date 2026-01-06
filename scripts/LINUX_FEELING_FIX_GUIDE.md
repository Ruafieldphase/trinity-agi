# Rhythm Feeling 저장 기능 추가 가이드

## 문제 발견
- `rhythm_think.py`가 Feeling을 계산하지만 파일로 저장하지 않았음
- 3일간 `feeling_latest.json`이 업데이트되지 않은 원인

## 해결책
`rhythm_think.py`의 `main()` 함수에 Feeling 저장 로직 추가

## 리눅스 적용 방법

### 1. SSH로 Linux VM 접속
```bash
ssh bino@192.168.119.128
```

### 2. 백업 생성
```bash
cp /home/bino/agi/scripts/rhythm_think.py /home/bino/agi/scripts/rhythm_think.py.backup
```

### 3. 파일 편집
```bash
nano /home/bino/agi/scripts/rhythm_think.py
```

### 4. 코드 추가
`main()` 함수에서 다음 부분을 찾으세요 (약 426줄):
```python
    print(f"✅ Dashboard update: {THOUGHT_STREAM_FILE}")
    
    # Save to Ledger (Permanent)
    save_to_ledger(narrative, current_state, delivery, decision)
```

이 사이에 다음 코드를 추가:
```python
    print(f"✅ Dashboard update: {THOUGHT_STREAM_FILE}")
    
    # Save Latest Feeling for Dashboard
    FEELING_FILE = OUTPUTS_DIR / "feeling_latest.json"
    feeling_output = {
        'feeling_vector': current_state.get('body_signals', {}) and [
            current_state['body_signals'].get('cpu_usage', 0) / 100.0,
            current_state['body_signals'].get('memory_usage', 0) / 100.0,
            min(current_state['body_signals'].get('queue_depth', 0) / 100.0, 1.0),
            current_state.get('fear_level', 0.0),
            0.5
        ] or [0.5, 0.5, 0.0, 0.0, 0.0],
        'feeling_entropy': abs(delivery['resonance']),
        'timestamp': datetime.now().isoformat(),
        'components': {
            'E': current_state.get('body_signals', {}).get('cpu_usage', 50) / 100.0,
            'Q': current_state.get('body_signals', {}).get('memory_usage', 50) / 100.0,
            'O': min(current_state.get('body_signals', {}).get('queue_depth', 0) / 100.0, 1.0),
            'V': current_state.get('fear_level', 0.0),
            'A': 0.5
        }
    }
    with open(FEELING_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeling_output, f, ensure_ascii=False, indent=2)
    print(f"✅ Feeling update: {FEELING_FILE}")
    
    # Save to Ledger (Permanent)
    save_to_ledger(narrative, current_state, delivery, decision)
```

### 5. 저장 및 종료
- `Ctrl+O`로 저장
- `Ctrl+X`로 종료

### 6. Rhythm 서비스 재시작
```bash
systemctl --user restart agi-rhythm
```

### 7. 확인
```bash
# 로그 확인 (Feeling update 메시지가 보여야 함)
tail -f /home/bino/agi/logs/rhythm.log

# 파일 생성 확인
cat /home/bino/agi/outputs/feeling_latest.json
```

## 예상 결과
다음 Rhythm Cycle부터:
- ✅ `feeling_latest.json`이 매 사이클마다 업데이트됨
- ✅ 로그에 "✅ Feeling update:" 메시지 출력
- ✅ Windows와의 동기화 정상 작동

## 참고
- 윈도우 버전은 이미 수정 완료
- 리눅스 수정 후 60초 이내 동기화 시작
- `sync_health_monitor.py`로 동기화 상태 실시간 확인 가능
