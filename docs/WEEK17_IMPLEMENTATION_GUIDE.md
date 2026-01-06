# Week 17 Implementation Guide
## ION Mentoring Optimization Phase - Execution Plan
**Week**: 17 (2025-10-25 - 2025-10-31)
**Status**: IMPLEMENTATION IN PROGRESS

---

## Executive Summary

Week 17 executes optimization roadmaps across cache, database, and cost. Divided into two phases (Quick Wins Days 1-5, Major Optimizations Days 6-10) with detailed daily checklists, monitoring procedures, and rollback plans.

**Expected Week 17 Results**:
- Cache hit rate: 82% → 75-78%+ (partial, completed in Week 18)
- Cost reduction: $200-300/month (50% of total target)
- Database query time: 18ms → 15ms
- Response time: 28.7ms → 27ms (small improvement)

---

## Pre-Implementation Checklist

### Monday Morning (Day 1, 9 AM)

**Go/No-Go Decision** (Complete before any changes):

**System Health Check**:
- [ ] Production availability: 99.95%+ (last 24h)
- [ ] Error rate: <0.5% (last 24h)
- [ ] Response time P95: <50ms (last 24h)
- [ ] Cache hit rate: 82%+ (baseline)
- [ ] Database lag: <100ms (all regions)

**Team Readiness**:
- [ ] All team members trained
- [ ] On-call engineer notified and ready
- [ ] Rollback procedures reviewed
- [ ] Monitoring dashboards prepared
- [ ] Communication channels active

**Documentation**:
- [ ] Optimization runbook printed/available
- [ ] Rollback procedures documented
- [ ] Success criteria defined
- [ ] Team roles assigned

**Infrastructure**:
- [ ] Staging environment ready
- [ ] Load test environment configured
- [ ] Monitoring alerts configured
- [ ] Backup created of current config

**Decision**:
- [ ] YES - Proceed with Week 17 implementation
- [ ] NO - Postpone to next week

**Approval Signature**: _________________ Date: _________

---

## PHASE 1: Quick Wins (Days 1-5)

### Day 1 (Monday): Database Query Optimization

**Objective**: Reduce query time from 18ms → 15ms

#### 1.1: Slow Query Analysis

**Time**: 9 AM - 10 AM

```bash
# Get slow query log from production
gcloud sql operations list --instance=ion-primary --project=ion-mentoring

# Analyze top slow queries
SELECT query, execution_time_ms, count(*) as frequency
FROM slow_query_log
WHERE timestamp > NOW() - INTERVAL 7 DAY
GROUP BY query
ORDER BY execution_time_ms DESC
LIMIT 20
```

**Expected Findings**:
- Persona lookup queries: ~8ms (optimize with index)
- User preference queries: ~5ms (already optimized)
- Analytics queries: ~20ms+ (can be deferred)
- Bulk operations: ~12ms (acceptable for bulk)

#### 1.2: Add Database Indexes

**Time**: 10 AM - 11 AM

```sql
-- Index 1: Persona lookup optimization
CREATE INDEX idx_persona_tone_pace_intent
ON personas(tone, pace, intent);

-- Index 2: User preference lookup
CREATE INDEX idx_user_preferences_userid
ON user_preferences(user_id, created_at DESC);

-- Index 3: Session lookup
CREATE INDEX idx_sessions_sessionid
ON sessions(session_id, created_at DESC);
```

**Verification**:
```sql
-- Check index usage
EXPLAIN SELECT * FROM personas
WHERE tone='calm' AND pace='flowing' AND intent='seek_advice';

-- Should show "Using index" in output
```

**Expected Impact**: 18ms → 15ms (-16% query time)

#### 1.3: Connection Pool Tuning

**Time**: 11 AM - 12 PM

```python
# Current config
DATABASE_POOL_SIZE = 10
DATABASE_POOL_TIMEOUT = 30

# Optimized config
DATABASE_POOL_SIZE = 15  # Handle more concurrent queries
DATABASE_POOL_MIN_OVERFLOW = 5  # Extra connections for spikes
DATABASE_POOL_RECYCLE = 3600  # Recycle connections hourly
```

**Deployment**: Canary to 10% traffic first

**Monitoring**:
- Connection pool utilization
- Query queue depth
- Connection errors

**Expected Impact**: Better query concurrency, no latency change

#### 1.4: Verification & Monitoring

**Time**: 12 PM - 1 PM

```python
# Run benchmark
def benchmark_queries():
    queries = [
        "SELECT * FROM personas WHERE ...",
        "SELECT * FROM user_prefs WHERE ...",
        # ... 20 sample queries
    ]

    times = []
    for query in queries:
        start = time.time()
        execute_query(query)
        times.append(time.time() - start)

    print(f"Average: {statistics.mean(times)*1000:.2f}ms")
    print(f"P95: {np.percentile(times, 95)*1000:.2f}ms")

    # Target: < 15ms average
    assert statistics.mean(times) < 0.015, "Query time too high"
```

**Acceptance Criteria**:
- [ ] Average query time < 15ms
- [ ] P95 query time < 25ms
- [ ] No errors in slow query log
- [ ] Connection pool utilization < 80%

**Rollback if**:
- [ ] Average query time increases
- [ ] Connection pool errors spike
- [ ] Database CPU > 70%

---

### Day 2 (Tuesday): Cost Optimization Phase 1 - Cloud Run

**Objective**: Reduce Cloud Run from $1,200 → $950/month (-$250)

#### 2.1: Reduce Minimum Instances (US Region)

**Time**: 9 AM - 10 AM

**Current Configuration**:
```yaml
# US Primary
minInstances: 3    # Always running
maxInstances: 100  # Auto-scale limit
cpuThrottling: 80%
memoryLimit: 1GB
```

**Optimized Configuration**:
```yaml
# US Primary - Reduced
minInstances: 2    # Reduce by 1 (-33%)
maxInstances: 100  # Same
cpuThrottling: 80%
memoryLimit: 1GB
```

**Deployment Steps**:

1. **Update staging first**:
```bash
gcloud run services update ion-mentoring-api \
  --min-instances=2 \
  --region=us-central1 \
  --project=ion-mentoring-staging
```

2. **Load test staging** (1 hour):
```bash
# Generate 5,000 r/s to staging
ab -n 100000 -c 500 https://staging.ion-mentoring.dev/api/v2/health
```

3. **Monitor results**:
- Response time P95: Should remain < 50ms
- Error rate: Should remain < 0.5%
- CPU utilization: Should increase slightly (now 35% → 45%)

4. **Deploy to production** (if test passes):
```bash
gcloud run services update ion-mentoring-api \
  --min-instances=2 \
  --region=us-central1 \
  --project=ion-mentoring
```

**Verification** (30 minutes post-deployment):
- [ ] All instances healthy
- [ ] No spike in error rate
- [ ] Response time maintained
- [ ] Auto-scaling working correctly

**Cost Impact**: -$100/month for US

#### 2.2: Reduce Minimum Instances (EU Region)

**Time**: 10 AM - 11 AM

**Current**: EU has 2 minimum instances (low utilization 28.3% CPU)

**Action**: Reduce to 1 minimum
```bash
gcloud run services update ion-mentoring-api \
  --min-instances=1 \
  --region=europe-west1 \
  --project=ion-mentoring
```

**Testing**: Quick smoke test (10 minutes)
- Send 100 test requests
- Verify response time < 50ms
- Check no errors

**Cost Impact**: -$80/month for EU

#### 2.3: Implement Predictive Scaling

**Time**: 11 AM - 12 PM

**Current Issue**: Auto-scaling reacts to traffic spikes (lag ~30s)

**Solution**: Predictive scaling based on time-of-day patterns

```python
# Time-based scaling rules
SCALING_RULES = {
    "8-9 AM": {"minInstances": 4, "maxInstances": 150},    # Morning spike
    "12-1 PM": {"minInstances": 4, "maxInstances": 150},   # Lunch spike
    "5-6 PM": {"minInstances": 3, "maxInstances": 120},    # Evening spike
    "Other": {"minInstances": 2, "maxInstances": 80},      # Off-peak
}

# Cron job to update scaling every hour
0 * * * * update_cloud_run_scaling.sh
```

**Deployment**:
```bash
# Deploy scaling manager service
gcloud run deploy scaling-manager \
  --source=./tools/cloud-run-scaling-manager \
  --schedule="0 * * * *"
```

**Verification**:
- [ ] Scaling rules applied correctly
- [ ] Scheduled jobs running
- [ ] Cost reduction tracked

**Cost Impact**: -$70/month (smarter scaling)

#### 2.4: Day 2 Summary

**End of Day 2**:
- Database queries optimized: -$0 (performance, not cost)
- US Cloud Run: -$100/month
- EU Cloud Run: -$80/month
- Predictive scaling: -$70/month
- **Day 2 Total**: -$250/month (38% of $615 target)

**Verification**:
- [ ] Production metrics stable
- [ ] No alerts triggered
- [ ] Error rate < 0.5%
- [ ] Response time < 50ms P95

---

### Day 3 (Wednesday): Cache Phase 1 - L1 Enhancement

**Objective**: Increase L1 hit rate from 64% → 70%

#### 3.1: Increase L1 Cache Size

**Time**: 9 AM - 10 AM

**Current Configuration**:
```python
class LocalCache:
    max_items = 1000
    ttl = 60  # seconds
```

**Optimized Configuration**:
```python
class LocalCache:
    max_items = 1500  # +50%
    ttl = 45  # seconds (refresh faster)
    memory_target = 3.5  # MB (up from 2.5MB)
```

**Deployment Steps**:

1. **Update code**:
```python
# persona_system/caching.py
LOCAL_CACHE_CONFIG = {
    "max_items": 1500,      # Increased
    "ttl": 45,              # Decreased
    "memory_mb": 3.5,       # Monitor
}

# Create new LocalCache instance
local_cache = LocalCache(
    max_items=LOCAL_CACHE_CONFIG["max_items"],
    ttl=LOCAL_CACHE_CONFIG["ttl"]
)
```

2. **Deploy to staging** (Blue-Green):
```bash
# Deploy to staging with new config
gcloud run deploy ion-mentoring-api \
  --source=./persona_system \
  --set-env-vars="CACHE_MAX_ITEMS=1500,CACHE_TTL=45" \
  --region=us-central1 \
  --project=ion-mentoring-staging
```

3. **Run cache benchmark**:
```python
# Run 1,000 requests with realistic persona keys
hit_count = 0
for i in range(1000):
    key = get_random_persona_key()
    if cache.get(key):
        hit_count += 1

hit_rate = (hit_count / 1000) * 100
print(f"L1 Hit Rate: {hit_rate}%")  # Target: > 65%
assert hit_rate > 65, "Hit rate too low"
```

4. **Memory verification**:
```bash
# Check memory usage
ps aux | grep python  # Should be < 4MB increase
docker stats           # Or container memory usage
```

5. **Deploy to production** (if test passes):
```bash
gcloud run deploy ion-mentoring-api \
  --source=./persona_system \
  --set-env-vars="CACHE_MAX_ITEMS=1500,CACHE_TTL=45" \
  --region=us-central1 \
  --project=ion-mentoring

# Apply to all regions
for region in us-central1 europe-west1 asia-southeast1; do
  gcloud run services update ion-mentoring-api \
    --region=$region \
    --set-env-vars="CACHE_MAX_ITEMS=1500,CACHE_TTL=45"
done
```

**Monitoring** (30 minutes post-deployment):
- [ ] L1 hit rate increase to 65%+
- [ ] Memory usage increase by <1MB
- [ ] No performance degradation
- [ ] Eviction rate stable

**Expected Impact**: L1 64% → 70% (+6 points)

#### 3.2: Implement Cache Warming

**Time**: 10 AM - 11 AM

**Implementation**:
```python
def preload_common_personas(pipeline):
    """Pre-populate cache with top 100 persona combinations"""

    # Top 100 most common resonance key combinations
    common_combos = [
        ("calm", "flowing", "seek_advice"),      # 1st
        ("analytical", "burst", "problem_solving"),  # 2nd
        ("frustrated", "medium", "learning"),    # 3rd
        # ... 97 more from analytics
    ]

    for i, (tone, pace, intent) in enumerate(common_combos):
        try:
            key = f"{tone}-{pace}-{intent}"
            # Process to fill cache
            result = pipeline.process(
                user_input="warmup",
                resonance_key=key,
                use_cache=True
            )

            if i % 10 == 0:
                print(f"Warming cache: {i}/100")
        except Exception as e:
            print(f"Warm-up failed for {key}: {e}")

    print("Cache warming complete")

# Call on Cloud Run startup
@app.on_event("startup")
def startup_event():
    logger.info("Starting cache warmup")
    preload_common_personas(pipeline)
    logger.info("Cache warmup complete")
```

**Deployment**:
```bash
# Update Cloud Run code with warmup
gcloud run deploy ion-mentoring-api \
  --source=./ \
  --set-env-vars="ENABLE_CACHE_WARMUP=true"
```

**Verification** (5 minutes after deployment):
```python
# Check that cache has warmed entries
assert cache.l1.hit_count > 50, "Warmup failed"
print(f"Cache has {cache.l1.size()} entries")  # Should be ~100
```

**Expected Impact**: +2-3 percentage points during peak times

#### 3.3: Day 3 Verification

**End of Day 3**:
- L1 cache size: 1000 → 1500 (+50%)
- L1 TTL: 60s → 45s (faster refresh)
- Cache warming: Implemented
- **Expected L1 hit rate**: 64% → 70%

**Monitoring Dashboard**:
```
Metric              Before    After     Target
─────────────────────────────────────────────
L1 Hit Rate         64.2%     ~70%      75%+
L1 Size (MB)        2.5MB     3.5MB     <4MB
L1 Items            1,000     1,500     ✓
Cache Warmup        No        Yes       ✓
Response Time       28.7ms    28.5ms    <50ms
```

---

### Days 4-5 (Thursday-Friday): Validation & Monitoring

**Thursday**:
- Monitor all changes from Days 1-3
- Review metrics and alerts
- Perform smoke tests
- Document any issues

**Friday**:
- Generate Day 1-5 summary report
- Calculate actual cost savings
- Plan Phase 2 (Days 6-10)
- Team retrospective

---

## PHASE 2: Major Optimizations (Days 6-10)

### Day 6 (Monday): Cache Phase 2 - Multi-tier Warming

**Objective**: Implement predictive cache warming and L2→L1 promotion

#### 6.1: Multi-Tier Warming Strategy

```python
class MultiTierCacheWarmer:
    def __init__(self, pipeline, cache):
        self.pipeline = pipeline
        self.cache = cache
        self.hot_keys = {}

    # Tier 1: Periodic Refresh (every 30 min)
    @scheduler.scheduled_job('interval', minutes=30)
    def refresh_hot_keys(self):
        """Refresh top 50 hot keys"""
        hot_keys = self.cache.get_hot_keys(n=50)
        for key in hot_keys:
            self.pipeline.prefetch(key)
        logger.info(f"Refreshed {len(hot_keys)} hot keys")

    # Tier 2: On-Demand Prefetching
    def prefetch_related(self, primary_key):
        """Prefetch likely next requests"""
        tone, pace, intent = parse_key(primary_key)
        related = [
            f"{tone}-{pace}-learning",
            f"analytical-{pace}-{intent}",
        ]
        for key in related:
            if not self.cache.exists(key):
                self.pipeline.prefetch(key)
```

**Deployment**: Monday 9 AM
**Monitoring**: Track prefetch success rate
**Expected Impact**: +2-3 points

### Day 7 (Tuesday): Cost Optimization Phase 2

**Objective**: Database instance downsizing

#### 7.1: Database Downsizing

**Current**: db-custom-16 (16 vCPU, 32GB) = $400/month
**Target**: db-custom-8 (8 vCPU, 16GB) = $300/month

**Procedure**:
1. Create replica with smaller instance
2. Test with production traffic
3. Promote if successful
4. Keep old instance as standby for 48 hours

**Expected Savings**: -$100/month

### Day 8 (Wednesday): Cache Phase 3 - Endpoint Optimization

**Objective**: Optimize /recommend and /bulk-process endpoints

#### 8.1: Recommend Endpoint

```python
@cached(ttl=600, key_prefix="recommend")
def get_recommendations(scenario, context):
    """Cache recommendations by scenario"""
    # ... recommendation logic
```

**Expected**: 15% → 45% hit rate for this endpoint

#### 8.2: Bulk-Process Endpoint

```python
def bulk_process(items):
    """Process items with caching"""
    results = []
    for item in items:
        # Check L1 cache first
        cached = cache.l1.get(item.key)
        if cached:
            results.append(cached)
        else:
            # Process and cache
            result = process_item(item)
            cache.l1.set(item.key, result)
            results.append(result)
    return results
```

**Expected**: 22% → 50% hit rate for this endpoint

### Days 9-10: Production Rollout & Validation

**Thursday-Friday**: Gradual rollout to production with continuous monitoring

---

## Success Metrics (End of Week 17)

### Performance Targets

```
Metric                  Current    Week 17 Target    Status
──────────────────────────────────────────────────────────
Response Time P95       36.4ms     35ms              -4%
Cache Hit Rate (L1)     64.2%      70%               +6pt
Cache Hit Rate (L2)     89.3%      91%               +2pt
Combined Hit Rate       82.3%      85%               +3pt
DB Query Time           18.3ms     15ms              -18%
```

### Cost Targets

```
Service            Current    Week 17 Target    Savings
──────────────────────────────────────────────────────
Cloud Run          $1,200     $950              -$250
Cloud SQL          $800       $700              -$100
Cache              $300       $250              -$50
────────────────────────────────────────────────────────
Total              $2,300     $1,900            -$400 (16%)

(Note: Full target is $615/month achieved by Week 18)
```

### Quality Targets

```
✓ Uptime: 99.95%+
✓ Error Rate: <0.5%
✓ Zero data loss
✓ All tests passing
✓ No production incidents
```

---

## Rollback Procedures

**For Cache Optimization**:
```bash
# Revert to previous config
git checkout HEAD~1 persona_system/caching.py
gcloud run deploy ion-mentoring-api --source=./
```

**For Cost Optimization**:
```bash
# Increase minimum instances
gcloud run services update ion-mentoring-api \
  --min-instances=3 --region=us-central1
```

**For Database Optimization**:
```bash
# Scale database back to db-custom-16
gcloud sql instances patch ion-primary \
  --tier=db-custom-16 --format=json
```

**Trigger Rollback If**:
- Error rate > 1% for > 5 minutes
- Response time P95 > 100ms
- Cache hit rate drops > 5 points
- Database replication lag > 500ms
- Any production incident

---

## Daily Standup Schedule

**Time**: 9:00 AM (US), 6:00 PM (EU), 10:00 PM (Asia)
**Duration**: 15 minutes
**Attendees**: All team members

**Agenda**:
1. What was completed yesterday?
2. What are we doing today?
3. Any blockers or issues?
4. Metric updates (cost, performance)

---

## Documentation & Handoff

**Daily Reports**: Email each day at 5 PM
```
Week 17 Day X Report

Completed:
- [ ] Task 1
- [ ] Task 2

Metrics (vs baseline):
- Cache: 82.3% → X%
- Cost: $2,460 → $X
- Response: 28.7ms → Xms

Issues/Blockers:
- None

Next Day Plan:
- [ ] Task Y
```

**Week 17 Final Report**: Friday 5 PM (deliverable)

---

## Go/No-Go Decision Points

**Day 3 (Wednesday 5 PM)**: Database + Cache Phase 1
- [ ] No production incidents
- [ ] Metrics within acceptable range
- [ ] Team confident
- **Decision**: GO to Phase 2 or PAUSE

**Day 7 (Tuesday 5 PM)**: Cost optimization evaluation
- [ ] Savings tracking on target
- [ ] No performance degradation
- [ ] Infrastructure stable
- **Decision**: Continue with Phase 3 or adjust

**Day 10 (Friday 5 PM)**: Week 17 Complete
- [ ] All Phase 1-2 changes deployed
- [ ] Metrics validated
- [ ] Documentation complete
- **Decision**: Proceed to Week 18 or extend Week 17

---

## Sign-Off

**Week 17 Implementation Guide**: READY ✓
**Pre-Implementation Approval**: _____ (Manager)
**Implementation Lead**: _____ (Engineer)
**On-Call Support**: _____ (SRE)

**Date**: ___________

---

**Ready to Execute Week 17 Optimization Implementation**

---
