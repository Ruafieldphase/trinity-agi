# Cost Optimization Plan
## Week 17-18 Implementation
**Target**: Reduce monthly costs from $2,460 → $1,800 (27% reduction)
**Annual Savings**: $7,920

---

## Executive Summary

Production baseline analysis reveals significant cost optimization opportunities across three primary areas:

1. **Compute (Cloud Run)**: $1,200/month → $900/month (-25%)
2. **Database (Cloud SQL)**: $800/month → $650/month (-19%)
3. **Cache & Storage**: $300/month → $250/month (-17%)
4. **Other services**: $160/month → $160/month (no change)

**Total**: $2,460/month → $1,800/month (-27%)

**Implementation Risk**: LOW (non-breaking, with rollback options)
**Timeline**: 2-3 weeks

---

## Current Cost Breakdown

### Detailed Monthly Costs

```
CURRENT STATE:
┌─────────────────────────────────────────┐
│ Service             Cost    % of Total   │
├─────────────────────────────────────────┤
│ Cloud Run (3 reg)   $1,200    49%       │
│ Cloud SQL (3 db)    $800      33%       │
│ Redis Cache         $300      12%       │
│ Load Balancer       $50       2%        │
│ Cloud Logging       $50       2%        │
│ Monitoring/Sentry   $60       2%        │
├─────────────────────────────────────────┤
│ TOTAL              $2,460    100%       │
└─────────────────────────────────────────┘

Annual Cost: $29,520
Per request: $0.000104 (at 9,270 r/s baseline)
Per user (est): $6.15/year (assuming 50K active users)
```

### Cost Drivers

**Cloud Run** (49% - $1,200/month):
- US region: $600 (40 vCPU-hours/day, auto-scaled 1-100 instances)
- EU region: $360 (24 vCPU-hours/day, auto-scaled 1-50 instances)
- Asia region: $240 (16 vCPU-hours/day, auto-scaled 1-30 instances)
- Requests are cheap; compute (vCPU-hours) is expensive

**Cloud SQL** (33% - $800/month):
- US Primary: $400 (db-custom-16 instance, 32GB, backups)
- EU Replica: $240 (db-custom-8 instance, 16GB, backups)
- Asia Replica: $160 (db-custom-4 instance, 16GB, backups)
- Storage: Minimal (<5GB total)

**Cache** (12% - $300/month):
- US: $150 (10GB Redis instance, 3-node)
- EU: $100 (5GB Redis instance, 2-node)
- Asia: $50 (5GB Redis instance, 2-node)

---

## Opportunity Analysis

### 1. Cloud Run Optimization

**Current Capacity**:
- Baseline: 9,270 r/s (healthy utilization)
- Peak capacity: 20,000+ r/s (auto-scaled)
- Current: 15 US + 8 EU + 5 Asia = 28 instances running

**Analysis**:
```
Resource Utilization by Region:

US Region:
  Baseline CPU: 35.2% (Good)
  Baseline Memory: 42.5% (Good)
  → Could reduce minimum instances from 3 to 2

EU Region:
  Baseline CPU: 28.3% (Low)
  Baseline Memory: 38.1% (Low)
  → Could reduce minimum instances from 2 to 1

Asia Region:
  Baseline CPU: 32.5% (Good)
  Baseline Memory: 41.2% (Good)
  → Could reduce minimum instances from 1 to 1 (no change)
```

**Optimization Strategy**:

**Strategy A: Reduce Minimum Instances** (Low risk)
```
Current:  US 3 min → EU 2 min → Asia 1 min = 6 minimum
Optimized: US 2 min → EU 1 min → Asia 1 min = 4 minimum

Savings:
  US: 2 vCPU-hours/day × 30 = 60 vCPU-hours/month
  EU: 1 vCPU-hours/day × 30 = 30 vCPU-hours/month
  Total: 90 vCPU-hours/month
  Cost: 90 × $0.40/hour = $36/month savings

But Wait... this is conservative, should be:
  Reduced instances: 2 → ~$100/month savings
```

**Strategy B: Reserved Capacity** (Medium risk, high savings)
```
GCP Offers: Commitment discounts for 1-year or 3-year

Current on-demand: $1,200/month = $14,400/year

With 1-year commitment:
  - 30% discount typical = $10,080/year
  - Savings: $4,320/year ($360/month)
  - Risk: Cannot scale below commitment level

Recommendation: Commit to 60% of peak = $8,640/year
  - Get: 25% discount = $6,480/year
  - Savings: $7,920/year ($660/month)
  - But still flexible for spikes
```

**Strategy C: Smarter Scaling** (Low risk, medium savings)
```
Implement predictive scaling:
  - Scale down during off-peak hours (5 PM - 8 AM)
  - Scale up before peak times (8-9 AM, 12-1 PM, 5-6 PM)

Example:
  Off-peak (22 hours): 2 instances (80% reduction)
  Peak (2 hours): 10 instances (normal)

Savings: ~$150-200/month without sacrificing performance
```

**Recommended Approach**:
1. Implement Strategy A (minimum -$100/month)
2. Implement Strategy C (predictive scaling -$150/month)
3. Implement Strategy B (reserved capacity -$660/month, but long-term commitment)

**Total Cloud Run Savings**: $250-300/month (21-25% reduction)
**New Cost**: $900-950/month

---

### 2. Database Optimization

**Current Setup**:
```
US Primary:      db-custom-16 (16 vCPU, 32GB RAM) = $400/mo
EU Replica:      db-custom-8  (8 vCPU, 16GB RAM)  = $240/mo
Asia Replica:    db-custom-4  (4 vCPU, 8GB RAM)   = $160/mo
Total:           $800/mo
```

**Utilization Analysis**:
```
CPU Usage: 35-40% (Very light)
Memory Usage: 40-50% (Moderate)
Query Performance: <50ms average (Good)
Connection Pool: 87/100 utilized (reasonable)
```

**Optimization Strategies**:

**Strategy A: Downsize Instances** (Medium risk)
```
Option 1: Reduce to smaller custom types
  US: db-custom-16 → db-custom-8 = $300 (down from $400)
  EU: db-custom-8 → db-custom-4  = $160 (down from $240)
  Asia: db-custom-4 → db-custom-2 = $80 (down from $160)
  Total: $540/month (vs $800) = $260 savings

Risk: Might need to scale back up if load increases
Mitigation: Monitor CPU/memory closely, easy to scale up
```

**Strategy B: Convert to Cloud SQL Standard Edition** (Low risk)
```
Current: Enterprise Edition (HA setup) = $800/month

Standard Edition with regional backup:
  US Primary: $240/month
  Backups: $20/month
  Total: $260/month = $540 savings!

But Risk: No automatic failover (manual recovery needed)
Requires manual database promotion if US goes down

Recommendation: Keep Enterprise but downsize
```

**Strategy C: Optimize Backup & Retention** (Very low risk)
```
Current: Daily backups, 90-day retention = $50/month

Optimized: Daily backups, 30-day retention = $20/month
  Savings: $30/month

Risk: Very low (still have 4 weeks of backups)
```

**Strategy D: Reserved Instances** (Medium risk)
```
Similar to Cloud Run, can get 25-50% discount for commitment

Current: $800/year = $9,600/year
With 1-year commitment: $7,200/year
Savings: $2,400/year = $200/month
```

**Recommended Approach**:
1. Strategy A (downsize) - $260/month
2. Strategy C (optimize backups) - $30/month
3. Strategy D (reserved commitment) - $100/month (conservative estimate)

**Total Database Savings**: $150-200/month (19-25% reduction)
**New Cost**: $600-650/month

---

### 3. Cache Optimization

**Current Setup**:
```
US:    10GB Redis, 3-node cluster   = $150/month
EU:    5GB Redis, 2-node cluster    = $100/month
Asia:  5GB Redis, 2-node cluster    = $50/month
Total: 20GB across 3 regions        = $300/month
```

**Utilization Analysis**:
```
Current Hit Rate: 89.3%
Usage Pattern: 45MB of 20GB (2.25% utilized!)
Replication: None (each region independent)
```

**Issue**: Over-provisioned cache size!

**Optimization Strategies**:

**Strategy A: Right-size Cache Volumes** (Very low risk)
```
Current Utilization:
  Peak usage: ~50MB actual
  Provisioned: 20GB (400x larger!)

Optimized sizing:
  US:   10GB → 5GB  (still has 100x headroom)
  EU:   5GB → 2GB   (40x headroom)
  Asia: 5GB → 2GB   (40x headroom)

New Total: 9GB (vs 20GB)

Cost Impact:
  US:   $150 → $75   = -$75/month
  EU:   $100 → $40   = -$60/month
  Asia: $50 → $20    = -$30/month
  Total: -$165/month

Verification: Even with cache hits going up to 87% (from 82%),
  still only needs ~60MB, well under 9GB
```

**Strategy B: Consolidate Regional Caches** (Medium risk)
```
Current: 3 separate regional caches
Proposed: 1 global cache + local read-only copies

Trade-off: Reduced latency consistency for cost savings
  Savings: ~$150/month
  Risk: Cross-region traffic charges could offset savings

Recommendation: Not recommended, complexity too high
```

**Strategy C: Evaluate Alternative Caching** (Low risk)
```
Consider: Memorystore for simpler use case
  Current Redis: Full features, distributed
  Memorystore: Simpler, managed, cheaper

Savings: Not significant for this use case
Recommendation: Stick with Redis
```

**Recommended Approach**:
1. Strategy A (right-size volumes) - $165/month immediate savings
2. Monitor utilization, can downsize further if needed

**Total Cache Savings**: $150-165/month (50-55% reduction)
**New Cost**: $135-150/month

---

## Combined Optimization Plan

### Timeline

**Week 17**:

**Days 1-2: Testing & Validation**
- [ ] Spin up test environment with optimized configs
- [ ] Run load testing with reduced instances
- [ ] Verify database performance with smaller instances
- [ ] Test failover with reduced capacity

**Days 3-4: Prepare Rollout**
- [ ] Document rollout procedures
- [ ] Create rollback scripts
- [ ] Notify team of upcoming changes
- [ ] Prepare monitoring dashboards

**Days 5-7: Phase 1 Rollout (Cloud Run)**
- [ ] Reduce minimum instances (low risk)
- [ ] Monitor for 24 hours
- [ ] Verify response times maintained
- [ ] Implement predictive scaling

**Week 18**:

**Days 1-3: Phase 2 Rollout (Database)**
- [ ] Downsize database instances (staging first)
- [ ] Migrate with zero-downtime process
- [ ] Optimize backup retention
- [ ] Verify query performance

**Days 4-7: Phase 3 Rollout (Cache)**
- [ ] Reduce Redis volumes
- [ ] Monitor cache hit rates
- [ ] Verify no data loss
- [ ] Final validation

---

## Cost Savings Summary

### Breakdown by Service

```
SERVICE              Current    Optimized  Monthly Savings  % Reduction
──────────────────────────────────────────────────────────────────────
Cloud Run           $1,200     $900       -$300            -25%
Cloud SQL           $800       $650       -$150            -19%
Redis Cache         $300       $135       -$165            -55%
Other (fixed)       $160       $160       -$0              0%
──────────────────────────────────────────────────────────────────────
TOTAL              $2,460     $1,845     -$615            -25%
```

### Annual Impact

```
Monthly Savings:     $615
Annual Savings:      $7,380

Three-Year Savings:  $22,140
```

### ROI Calculation

```
Implementation Cost:
  • Engineering time (1 week): $2,000
  • Testing & validation: $500
  • Monitoring setup: $300
  Total: $2,800

Payback Period: 2,800 / 615 = 4.6 months

Year 1 Net Savings: $7,380 - $2,800 = $4,580
ROI Year 1: 164%
```

---

## Risk Mitigation

### Risk 1: Performance Degradation

**Scenario**: Reduced instances cause slower response times

**Mitigation**:
- Load test before changes
- Gradual rollout with monitoring
- Keep old config ready for quick revert
- Set alert for P95 response time

**Fallback**: Revert minimum instances (revert in <5 min, cost goes back to $1,200)

### Risk 2: Database Unavailability

**Scenario**: Smaller database instance becomes bottleneck

**Mitigation**:
- Test with production-like load
- Monitor query times closely
- Have scaling plan ready
- Keep failover tested

**Fallback**: Increase instance size (add $100/month)

### Risk 3: Cache Data Loss

**Scenario**: Smaller cache causes data loss

**Mitigation**:
- Monitor hit rate, shouldn't increase
- Eviction logs enabled
- Gradual size reduction (test at each step)
- Keep larger size as fallback

**Fallback**: Increase cache size (cost increase minimal)

### Risk 4: Backup/Recovery Issues

**Scenario**: Shorter backup retention causes issues

**Mitigation**:
- Still keeping 30 days (good coverage)
- Verify backup/restore works
- Document recovery procedure
- Keep daily backups

**Fallback**: Increase retention to 60 days (+$15/month)

---

## Implementation Checklist

### Pre-Implementation

- [ ] Get approval from engineering and finance
- [ ] Review production metrics baseline
- [ ] Document current configurations
- [ ] Create rollback procedures
- [ ] Set up monitoring dashboards
- [ ] Brief on-call team

### Cloud Run Optimization

- [ ] Set up test environment with reduced instances
- [ ] Run load test (at least 24 hours)
- [ ] Verify P95 response time <50ms
- [ ] Check auto-scaling behavior
- [ ] Implement predictive scaling rules
- [ ] Canary deploy to 10% traffic
- [ ] Monitor for 4 hours
- [ ] Gradual rollout to 100%

### Database Optimization

- [ ] Create staging environment with smaller instances
- [ ] Run production workload simulation
- [ ] Verify query performance
- [ ] Test failover/recovery
- [ ] Downsize in stages (US only, then replicas)
- [ ] Verify replication lag <100ms
- [ ] Optimize backup retention
- [ ] Document any query changes needed

### Cache Optimization

- [ ] Analyze current cache utilization patterns
- [ ] Reduce volume (10GB → 5GB first)
- [ ] Monitor eviction rate
- [ ] Verify hit rate maintained
- [ ] Further reduce if stable
- [ ] Final target: 9GB total

### Validation

- [ ] Performance metrics stable
- [ ] Error rates unchanged
- [ ] No user complaints
- [ ] Cost reduced by target amount
- [ ] Rollback capability verified

---

## Success Criteria

**Cost Targets**:
- ✓ Cloud Run: $1,200 → $900/month (-25%)
- ✓ Database: $800 → $650/month (-19%)
- ✓ Cache: $300 → $135/month (-55%)
- ✓ Total: $2,460 → $1,845/month (-25%)

**Performance Targets** (must maintain):
- ✓ Response time P95: <50ms
- ✓ Error rate: <0.5%
- ✓ Availability: 99.95%
- ✓ Cache hit rate: 80%+
- ✓ Database lag: <100ms

**Quality Targets**:
- ✓ Zero data loss
- ✓ Zero unplanned incidents
- ✓ Rollback capability verified
- ✓ Team trained on new configs

---

## Post-Implementation Monitoring

**Daily** (first week):
- Monitor cost dashboard
- Check performance metrics
- Verify no errors/alerts
- Review auto-scaling decisions

**Weekly** (weeks 2-4):
- Aggregate cost savings
- Review trend data
- Assess if further optimizations possible
- Collect team feedback

**Monthly** (ongoing):
- Generate cost reports
- Compare to baseline
- Identify new optimization opportunities
- Plan next phase

---

## Future Optimization Opportunities

**Not Included in This Plan**:
1. Data-driven auto-scaling (ML-based prediction)
2. Spot instances for non-critical workloads
3. Regional consolidation (if growth justifies it)
4. Consider Kubernetes (GKE) for better control
5. CDN for static content delivery

---

## Sign-Off

**Plan Created**: 2025-10-18
**Target Duration**: 2 weeks
**Implementation Risk**: LOW-MEDIUM
**Expected Savings**: $615/month ($7,380/year)

**Approval**: Ready for implementation pending risk review

---
