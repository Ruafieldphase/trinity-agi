# Luon Queue Decisions (v2)

- **2025-10-15 01:00:00+00:00** | **adjust** | allow: ['세나'] | block: [] | next: 세나 | R[min/med/max]=0.788/0.788/0.788 | reason: median R 0.788 between 0.40 and 0.80
- **2025-10-15 01:01:00+00:00** | **adjust** | allow: ['세나'] | block: ['루빛'] | next: 루빛 | R[min/med/max]=0.405/0.597/0.788 | reason: median R 0.597 between 0.40 and 0.80
- **2025-10-15 01:02:00+00:00** | **sequential** | allow: ['세나'] | block: ['루빛', '시안'] | next: 시안 | R[min/med/max]=0.083/0.405/0.788 | reason: unstable 1 event(s) in window; enforce sequential
- **2025-10-15 01:04:00+00:00** | **sequential** | allow: ['세나'] | block: ['루빛', '시안'] | next: 세나 | R[min/med/max]=0.042/0.405/0.788 | reason: unstable 2 event(s) in window; enforce sequential
- **2025-10-15 01:06:00+00:00** | **sequential** | allow: ['세나'] | block: ['루빛', '시안'] | next: 루빛 | R[min/med/max]=0.042/0.372/0.788 | reason: unstable 3 event(s) in window; enforce sequential
- **2025-10-15 01:08:00+00:00** | **sequential** | allow: ['세나'] | block: ['루빛', '시안'] | next: 시안 | R[min/med/max]=0.042/0.083/0.454 | reason: unstable 4 event(s) in window; enforce sequential