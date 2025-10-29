# v1.5 Threshold Matrix (ENV)

| ENV   | m_score_min | h_eff_max | errorRatioTarget (HPA ext/KEDA) | STREAM_BUFFER_WINDOW_MS | SLO target |
|-------|-------------:|----------:|---------------------------------:|------------------------:|-----------:|
| dev   | 0.40         | 0.75      | 0.20                             | 1000                    | 0.990      |
| stage | 0.45         | 0.72      | 0.12                             | 1200                    | 0.995      |
| prod  | 0.48         | 0.70      | 0.10                             | 1500                    | 0.997      |

> 참고: prod에서 에러 비율 목표치를 더 낮게 설정(보수적). 환경에 따라 Kafka 지연/RTT 고려.
