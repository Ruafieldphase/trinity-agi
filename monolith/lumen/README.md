# PII Masker + Scorer (Demo Toolkit)

## Files
- `pii_masker_demo.py` — regex/Luhn/heuristic 기반 간단 감지·마스킹
- `scorer.py` — span IoU(≥0.5) 매칭 기반 채점기
- 샘플 골드: `../pii_label_synthetic_1000.jsonl` (별도 제공)

## Quickstart
```bash
# 1) 예측/마스킹 (1000 합성 샘플 중 앞 100개만 사용 예)
python pii_masker_demo.py --in ../pii_label_synthetic_1000.jsonl --pred pred.jsonl --masked masked.jsonl

# 2) 채점
python scorer.py --gold ../pii_label_synthetic_1000.jsonl --pred pred.jsonl --report report.txt --limit 100
```

## Notes
- 주소/이름/기관 등은 휴리스틱이므로 FP 가능성이 높습니다 → NER/사전 보강 권장
- 높은 위험 타입(`JUMIN_LIKE`,`CARD`,`ACCOUNT`,`ADDRESS`,`HEALTH_DATA`)은 전면 마스킹 처리
- 목표 지표(게이트): Recall ≥ 0.98 / Precision ≥ 0.95 / 유틸리티 손실 ≤ 5%
