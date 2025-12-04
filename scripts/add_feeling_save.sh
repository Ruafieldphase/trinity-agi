#!/bin/bash
# rhythm_think.py에 feeling 저장 기능 추가

cat \u003c\u003c'EOF' \u003e /tmp/feeling_save_patch.py
# 이 코드를 rhythm_think.py의 main() 함수에 추가
# 위치: THOUGHT_STREAM_FILE 저장 직후 (426줄 뒤)

    # Save Latest Feeling for Dashboard
    FEELING_FILE = OUTPUTS_DIR / "feeling_latest.json"
    feeling_output = {
        'feeling_vector': delivery.get('pattern', {}).get('vector', [0.5, 0.5, 0.0, 0.0, 0.0]),
        'feeling_entropy': abs(delivery['resonance']),
        'timestamp': datetime.now().isoformat(),
        'components': {
            'E': delivery.get('pattern', {}).get('vector', [0.5])[0] if delivery.get('pattern', {}).get('vector') else 0.5,
            'Q': delivery.get('pattern', {}).get('vector', [0.5, 0.5])[1] if len(delivery.get('pattern', {}).get('vector', [])) \u003e 1 else 0.5,
            'O': delivery.get('pattern', {}).get('vector', [0, 0, 0])[2] if len(delivery.get('pattern', {}).get('vector', [])) \u003e 2 else 0.0,
            'V': delivery.get('pattern', {}).get('vector', [0, 0, 0, 0])[3] if len(delivery.get('pattern', {}).get('vector', [])) \u003e 3 else current_state.get('fear_level', 0.0),
            'A': delivery.get('pattern', {}).get('vector', [0, 0, 0, 0, 0])[4] if len(delivery.get('pattern', {}).get('vector', [])) \u003e 4 else 0.5
        }
    }
    with open(FEELING_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeling_output, f, ensure_ascii=False, indent=2)
    print(f"✅ Feeling update: {FEELING_FILE}")
    
EOF

echo "패치 파일 생성 완료: /tmp/feeling_save_patch.py"
echo ""
echo "비노체님, 이 코드를 리눅스의 rhythm_think.py에 추가해주세요:"
echo "위치: THOUGHT_STREAM_FILE 저장 직후 (\"✅ Dashboard update:\" 출력 다음)"
