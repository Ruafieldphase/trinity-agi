# v1.5 RC QA — Dual Gate Loop

## Pre/Post
```bash
python scripts/integrated_gate_v19_v15.py --mode pre --threshold_overall 0.65 --threshold_feedback 0.60 --threshold_release 0.60 --export logs/gate_pre.json || true
python scripts/integrated_gate_v19_v15.py --mode post --export logs/gate_post.json || true

python scripts/maturity_diff_v15.py   --pre logs/gate_pre.json   --post logs/gate_post.json   --report docs/V15_QA_DIFF_REPORT.md   --json-out docs/V15_QA_RESULT_CARD.json   --summary docs/V15_QA_SUMMARY.txt
```
PASS 기준(default): overall≥0.65, feedback≥0.60, release≥0.60, |ΔEntropy|<0.15, ΔSymRes<0.08
