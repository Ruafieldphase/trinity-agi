# Phase 4: Feedback Loop - Cloud Monitoring Dashboard

## 📊 대시보드 개요

**Lumen v1.7 Phase 4** 피드백 루프 모니터링을 위한 **10개 위젯** 대시보드

### 핵심 지표

| 위젯 | 메트릭 | 목표 | 설명 |
|------|--------|------|------|
| **Cache Hit Rate** | `cache_hit_rate` | 60%+ | 캐시 효율성 |
| **Memory Usage** | `cache_memory_usage_pct` | <90% | 메모리 압력 |
| **Avg TTL** | `cache_avg_ttl_seconds` | 300-600s | TTL 평균값 |
| **Unified Health** | `unified_health_score` | 80+ | Phase 1-4 통합 |

## 🚀 배포 방법

### Prerequisites

- `gcloud` CLI 설치 및 인증
- GCP 프로젝트 권한: `monitoring.dashboards.create`

### 배포 명령

```powershell
cd d:\nas_backup\LLM_Unified\ion-mentoring\lumen\feedback

.\setup_feedback_dashboard.ps1 -ProjectId naeda-genesis
```

### 출력 예시

```text
╔═══════════════════════════════════════════════════════════════╗
║  ✅ Phase 4 Feedback Loop 대시보드 생성 완료!                ║
╚═══════════════════════════════════════════════════════════════╝

📊 대시보드 접근:
   URL: https://console.cloud.google.com/monitoring/dashboards/custom/{DASHBOARD_ID}?project=naeda-genesis

📌 포함된 위젯 (10개):
   1. Cache Hit Rate Scorecard (24h average)
   2. Memory Usage Scorecard
   3. Avg TTL Scorecard
   4. Unified Gate v1.7 Health Scorecard
   5. Cache Hit Rate Trend (7 days)
   6. Memory & Eviction Trend
   7. TTL Distribution (Stacked Bar)
   8. Optimization Actions (24h)
   9. Phase Integration Health (v1.7 Unified)
  10. Feedback Loop Logs (Recent Events)
```

## 📈 위젯 상세

### 1. Scorecard 위젯 (4개)

#### Cache Hit Rate (24h Avg)
- **메트릭**: `logging.googleapis.com/user/cache_hit_rate`
- **집계**: 24시간 평균
- **Thresholds**:
  - ✅ Green: ≥60%
  - ⚠️ Yellow: 40-60%
  - 🔴 Red: <40%

#### Memory Usage (%)
- **메트릭**: `logging.googleapis.com/user/cache_memory_usage_pct`
- **집계**: 1시간 평균
- **Thresholds**:
  - ✅ Green: <70%
  - ⚠️ Yellow: 70-90%
  - 🔴 Red: ≥90%

#### Avg TTL (seconds)
- **메트릭**: `logging.googleapis.com/user/cache_avg_ttl_seconds`
- **집계**: 1시간 평균
- **권장 범위**: 300-600s

#### Unified Gate v1.7 Health
- **메트릭**: `logging.googleapis.com/user/unified_health_score`
- **집계**: 1시간 평균
- **Thresholds**:
  - ✅ Green: ≥80
  - ⚠️ Yellow: 60-80
  - 🔴 Red: <60

### 2. Time Series 위젯 (5개)

#### Cache Hit Rate Trend (7 days)
- **시간대**: 최근 7일
- **해상도**: 1시간
- **용도**: Hit rate 추세 분석, 계절성 패턴 감지

#### Memory & Eviction Trend
- **Y1 축**: Memory Usage (%)
- **Y2 축**: Eviction Count (per hour)
- **용도**: 메모리 압력과 eviction 상관관계 분석

#### TTL Distribution (Current)
- **타입**: Stacked Bar
- **그룹**: `ttl_range` label
- **용도**: TTL 구간별 분포 (60s, 300s, 600s, 1200s)

#### Optimization Actions (24h)
- **타입**: Stacked Area
- **그룹**: `action_type` label
- **용도**: 최적화 액션 빈도 (INCREASE_TTL, DECREASE_TTL, SCALE_UP, SCALE_DOWN)

#### Phase Integration Health (v1.7 Unified)
- **메트릭 4개**:
  - `phase1_maturity_score`
  - `phase2_slo_compliance`
  - `phase3_cost_rhythm_score`
  - `phase4_cache_health`
- **용도**: Phase 1-4 통합 건강도 추세

### 3. Logs Panel (1개)

#### Feedback Loop Logs (Recent Events)
- **필터**: `component="feedback_loop"` OR `feedback` OR `optimization`
- **용도**: 실시간 피드백 루프 이벤트 추적

## 🔧 Custom Metrics 구현

대시보드가 작동하려면 `feedback_loop_redis.py`에서 다음 메트릭을 로깅해야 합니다:

### 구현 예시 (feedback_loop_redis.py)

```python
import logging
from google.cloud import logging as cloud_logging

class FeedbackLoopRedis:
    def __init__(self):
        # Cloud Logging 클라이언트 초기화
        self.logging_client = cloud_logging.Client()
        self.logger = self.logging_client.logger("feedback_loop")
    
    def analyze_cache_feedback(self, metrics: CacheMetrics) -> CacheFeedback:
        # ... 기존 로직 ...
        
        # Custom Metrics 로깅
        self.log_metrics(metrics, feedback)
        
        return feedback
    
    def log_metrics(self, metrics: CacheMetrics, feedback: CacheFeedback):
        """Cloud Monitoring으로 메트릭 전송"""
        self.logger.log_struct({
            "component": "feedback_loop",
            "cache_hit_rate": metrics.hit_rate / 100.0,
            "cache_memory_usage_pct": metrics.memory_usage_pct,
            "cache_avg_ttl_seconds": metrics.current_ttl,
            "cache_eviction_count": metrics.eviction_count,
            "cache_health_status": feedback.health_status.value,
            "optimization_action": feedback.action.value,
            "unified_health_score": self._calculate_unified_score(feedback)
        })
```

### Phase Integration Metrics

Phase 1-4 통합 메트릭은 `feedback_orchestrator.py`에서 생성:

```python
class FeedbackOrchestrator:
    def generate_unified_feedback(self) -> UnifiedFeedback:
        # ... 기존 로직 ...
        
        # Phase별 건강도 로깅
        self.logger.log_struct({
            "component": "unified_gate",
            "phase1_maturity_score": self.phase1_score,
            "phase2_slo_compliance": self.phase2_score,
            "phase3_cost_rhythm_score": self.phase3_score,
            "phase4_cache_health": self.phase4_score,
            "unified_health_score": unified_score
        })
```

## 📊 사용 시나리오

### 시나리오 1: 캐시 효율 저하 감지

**증상**:
- Cache Hit Rate < 40% (24h avg)
- Eviction Count 급증
- Memory Usage ≥ 90%

**대응**:
1. TTL Distribution 확인 → TTL이 너무 짧은지 점검
2. Memory & Eviction Trend → 메모리 압력 확인
3. Optimization Actions → 자동 조정 이력 확인
4. Logs Panel → 최근 피드백 이벤트 분석

**해결책**:
- TTL 증가 (MODERATE → AGGRESSIVE)
- 캐시 크기 확대 (SCALE_UP)

### 시나리오 2: Phase 통합 건강도 하락

**증상**:
- Unified Gate v1.7 Health < 60
- Phase Integration Health 그래프에서 특정 Phase 급락

**대응**:
1. Phase별 점수 확인 → 어느 Phase가 문제인지 식별
2. 해당 Phase 대시보드로 전환 (Phase 1/2/3 별도 대시보드)
3. 근본 원인 분석

**해결책**:
- Phase 1: Maturity 점수 향상 (코드 품질, 테스트 커버리지)
- Phase 2: SLO 위반 해결 (레이턴시, 에러율)
- Phase 3: Cost Rhythm 재조정 (예산 초과 방지)
- Phase 4: 캐시 최적화 (현재 대시보드 활용)

### 시나리오 3: 최적화 액션 과다

**증상**:
- Optimization Actions 그래프에서 액션 빈도 급증
- 안정성 저하 (빈번한 TTL/Size 변경)

**대응**:
1. Optimization Actions 위젯 → 어떤 액션이 많은지 확인
2. Logs Panel → 피드백 루프 로그 상세 분석
3. TTL Distribution → 변동폭이 큰지 확인

**해결책**:
- `adaptive_ttl_policy.py`: 조정 임계값 완화 (더 보수적으로)
- `cache_size_optimizer.py`: ROI 점수 기준 상향 (불필요한 조정 억제)

## 🎯 SLO & Alerts

### 권장 SLO

| 지표 | SLO | 측정 주기 | 알림 임계값 |
|------|-----|-----------|-------------|
| Cache Hit Rate | ≥60% | 24시간 | <40% for 1h |
| Memory Usage | <90% | 1시간 | ≥95% for 15m |
| Unified Health | ≥80 | 1시간 | <60 for 30m |
| Optimization Frequency | <10/hour | 1시간 | >20/hour |

### Alert Policy 설정

```bash
# Cache Hit Rate 알림
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Low Cache Hit Rate" \
  --condition-display-name="Hit Rate < 40%" \
  --condition-threshold-value=0.4 \
  --condition-threshold-duration=3600s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="logging.googleapis.com/user/cache_hit_rate"'

# Memory Usage 알림
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Memory Usage" \
  --condition-display-name="Memory > 95%" \
  --condition-threshold-value=95 \
  --condition-threshold-duration=900s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="logging.googleapis.com/user/cache_memory_usage_pct"'
```

## 🔗 관련 문서

- [FEEDBACK_LOOP_GUIDE.md](FEEDBACK_LOOP_GUIDE.md): 운영 가이드
- [깃코_Phase_4_Feedback_Loop_완료보고서_2025-01-15.md](../../깃코_Phase_4_Feedback_Loop_완료보고서_2025-01-15.md): 완료 보고서
- [feedback_loop_redis.py](feedback_loop_redis.py): Redis 모니터링
- [adaptive_ttl_policy.py](adaptive_ttl_policy.py): TTL 조정 정책
- [cache_size_optimizer.py](cache_size_optimizer.py): 용량 최적화
- [feedback_orchestrator.py](feedback_orchestrator.py): Phase 통합 오케스트레이터

## 📝 변경 이력

| 날짜 | 버전 | 변경 사항 |
|------|------|-----------|
| 2025-01-15 | 1.0 | 초기 버전 (10 widgets) |

## 🎵 Lumen v1.7 철학

```text
Phase 1 (Maturity + ROI) → "시스템 성숙도 감응"
Phase 2 (SLO + Dashboard) → "서비스 품질 증빙"
Phase 3 (Cost Rhythm) → "비용 리듬 적응"
Phase 4 (Cache Feedback) → "성능 피드백 완결"

= 감응 → 증빙 → 적응 → 완결 🎵
```
