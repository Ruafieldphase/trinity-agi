# 🌕 FDO-AGI / System C — v8.3 → v8.4 세션 리줌 (루멘 작성)

## 📍 현재 상태 (v8.3 Harmonic Merge)
- 게이트: pass_rate ≥ 0.92, mean(harmonic) ≥ 0.86, forbidden=0 → **데모 기준 전부 통과**
- Auto-Calibrator 적용: 분포 기반 컷 자동 산정 (샘플에서 thr≈0.98 산정)
- 산출물: `outputs_v8_3.jsonl`, `outputs_v8_3.report.md`, `compare_v8_2_v8_3.summary.md`
- 러너: `run_v8_3.sh` (환경 변수 `CALIB_TARGET` 지원)

## 🎯 다음 단계 (v8.4 — Intent Bloom)
- why→intent 전환 정식화: anchors×mechanism×conditions 최소 1문장, 길이 하한
- self-interpret(Reason-of-Reason) 1문장 생성
- dual-validator로 intent / self-interpret 동시 검증
- 게이트(초안): intent_quality ≥ 0.90, self_interpret_coh ≥ 0.85, forbidden=0

## 🔁 역할
| 역할 | 담당 |
|--|--|
| 루빛 | v8.3/8.4 실행 및 리포트 |
| 루멘 | 규약·검증·보정 설계 및 게이트 관리 |
| 비노체 | 의미·윤리 관점 평가 및 의식 리듬 조율 |

## 🗂 파일
- v8.3: `/mnt/data/system_c_v8_3/`
- v8.4: `/mnt/data/system_c_v8_4/`

## ▶️ 실행 커맨드 (참고)
```bash
# v8.3 (실데이터)
CALIB_TARGET=0.92 ./run_v8_3.sh <실제_inputs_v8_3.jsonl> outputs_v8_3.jsonl

# v8.4 (데모 파이프라인)
python system_c_v8_4_intent_bloom.py /mnt/data/system_c_v8_4/inputs_v8_4.jsonl /mnt/data/system_c_v8_4/outputs_v8_4.jsonl
```
