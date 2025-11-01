# Ledger-Based Async vs Sequential Analysis

Generated: 2025-11-02 08:46:49
Total tasks analyzed: 452

## Executive Summary

- **Latency Reduction**: 3.24s (10.7%)
- **Recommendation**: ✅ Enable Async Thesis

## SEQUENTIAL Mode

- Sample Size: 438
- Thesis: 7.54s (±3.49) [0.00-35.44]
- Antithesis: 8.82s (±3.35) [0.00-26.88]
- Synthesis: 13.73s (±4.92) [0.00-29.76]
- **Total: 30.10s (±10.25) [0.00-64.18]**
- Second Pass Rate: 0.0%

## ASYNC Mode

- Sample Size: 14
- Thesis: 5.53s (±1.75) [3.47-9.55]
- Antithesis: 8.54s (±1.68) [6.21-12.74]
- Synthesis: 12.79s (±2.61) [9.40-18.71]
- **Total: 26.86s (±3.96) [20.73-33.88]**
- Second Pass Rate: 0.0%

## Sample Data

- [SEQ] 00a7e408-c8a4-40bd-b353-593d354c5a73: 35.48s (T:5.90 A:9.65 S:19.93)
- [SEQ] 03ece4e6-8b8d-4a65-809b-5aa07264b88f: 54.27s (T:17.69 A:15.96 S:20.62)
- [SEQ] 0511aad7-e844-457c-8e1a-3501136395b5: 43.64s (T:8.25 A:10.06 S:25.33)
- [SEQ] 05a6d245-4454-471b-8d68-3db043a068b2: 36.16s (T:9.04 A:12.50 S:14.61)
- [SEQ] 05c18e0d-35e5-4d39-98d8-8484205cdd74: 27.04s (T:10.02 A:8.16 S:8.86)
- [SEQ] 05f8228d-5388-44bd-88fe-e8c647909614: 33.48s (T:5.91 A:14.70 S:12.87)
- [SEQ] 06374678-353d-469e-be41-dc8e3a0e2421: 4.11s (T:2.34 A:0.90 S:0.86)
- [SEQ] 0706057c-73b8-4d66-876d-e88999e425dd: 28.73s (T:5.71 A:9.54 S:13.48)
- [SEQ] 07277681-fbd6-41fd-8a00-8ef7de68f74c: 31.65s (T:6.60 A:9.40 S:15.64)
- [SEQ] 072c1c81-b031-4f7a-9293-f487d67dbaa1: 3.60s (T:2.36 A:0.88 S:0.35)
- ... (442 more tasks)
