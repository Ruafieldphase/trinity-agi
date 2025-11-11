# ✅ New Session Checklist

## 🚀 Start Here (5분)

- [ ] 1. Read: `outputs/HIPPOCAMPUS_PHASE1_COMPLETE.md`
- [ ] 2. Read: `NEXT_SESSION_QUICK_START.md`
- [ ] 3. Test: `python scripts/test_hippocampus.py`
- [ ] 4. Check Dreams: `Get-Content outputs/dreams.jsonl -Tail 3 | ConvertFrom-Json | ft`
- [ ] 5. Choose: Option 1 (Dream Integration) **OR** Option 2 **OR** Option 3

---

## 🎯 If Option 1: Dream Integration (추천)

### Phase 1: Glymphatic System (30분)

- [ ] 1. Create: `fdo_agi_repo/copilot/glymphatic.py`
- [ ] 2. Implement `clean()` method (노이즈 제거)
- [ ] 3. Test basic functionality

### Phase 2: Synaptic Pruner (30분)

- [ ] 1. Create: `fdo_agi_repo/copilot/synaptic_pruner.py`
- [ ] 2. Implement `prune()` method (가지치기)
- [ ] 3. Test basic functionality

### Phase 3: Integration (30분)

- [ ] 1. Create: `scripts/integrate_dreams.py`
- [ ] 2. Connect: Dreams → Glymphatic → Pruner → Hippocampus
- [ ] 3. Test full pipeline

### Phase 4: Validation (10분)

- [ ] 1. Run: `python scripts/integrate_dreams.py`
- [ ] 2. Verify: Long-term memory populated
- [ ] 3. Run: `python scripts/test_hippocampus.py`

---

## 🎓 If Option 2: System Validation

- [ ] 1. Re-run: `python scripts/test_hippocampus.py`
- [ ] 2. Re-run: `powershell scripts/run_dream_mode.ps1 -Iterations 20`
- [ ] 3. Check: `outputs/dreams.jsonl` (should have 20+ dreams)
- [ ] 4. Test consolidation: `python scripts/test_memory_consolidation.py`

---

## 🔬 If Option 3: Phase 2 Start

- [ ] 1. Read: `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` (Phase 2 section)
- [ ] 2. Create: `scripts/test_wave_particle_duality.py`
- [ ] 3. Create: `fdo_agi_repo/copilot/wave_particle_detector.py`
- [ ] 4. Test basic detection

---

## ✅ Success Criteria (Option 1)

### Glymphatic Working

- [ ] Loads dreams from `outputs/dreams.jsonl`
- [ ] Removes contradictions
- [ ] Removes duplicates
- [ ] Removes emotional noise
- [ ] Returns cleaned dreams

### Synaptic Pruning Working

- [ ] Takes cleaned dreams
- [ ] Ranks by importance
- [ ] Keeps top 70%
- [ ] Returns pruned dreams

### Integration Working

- [ ] Full pipeline runs without errors
- [ ] Dreams → Glymphatic → Pruner → Hippocampus
- [ ] Long-term memory stores 5-10 high-quality dreams
- [ ] `python scripts/test_hippocampus.py` still passes

---

## 📊 Expected Results (Option 1)

**Before Integration:**

```
Dreams: 18 raw (outputs/dreams.jsonl)
Long-term: 0 consolidated
```

**After Integration:**

```
Dreams: 18 raw
  ↓ Glymphatic cleaning (-30%)
Cleaned: ~13
  ↓ Synaptic pruning (-30%)
Pruned: ~9
  ↓ Hippocampus storage
Long-term: 9 high-quality memories

Quality: ★★★★★ (90%+ purity)
```

---

## 🐛 Known Issues

None. All tests passing.

---

## 📞 Help

### If Stuck

1. Read: `docs/AGENT_HANDOFF.md` (full context)
2. Re-run: `python scripts/test_hippocampus.py`
3. Check: `outputs/dreams.jsonl` (should have 18 entries)

### If Tests Fail

1. Check: `fdo_agi_repo/copilot/hippocampus.py` (should have bug fix)
2. Verify: `_calculate_importance()` checks `if "importance" in item`
3. Re-run: `python scripts/test_memory_consolidation.py`

---

## 🎯 Time Budget

### Option 1 (Dream Integration)

- Glymphatic: 30min
- Pruner: 30min
- Integration: 30min
- Test: 10min
- **Total: ~1.5h**

### Option 2 (Validation)

- Re-test: 10min
- Dream re-run: 5min
- Verification: 15min
- **Total: ~30min**

### Option 3 (Phase 2)

- Design: 30min
- Implementation: 90min
- Test: 30min
- **Total: ~2.5h**

---

## 🎁 Quick Commands

### Immediate Context

```bash
# 1. Read summary
code outputs/HIPPOCAMPUS_PHASE1_COMPLETE.md

# 2. Verify tests
python scripts/test_hippocampus.py

# 3. Check dreams
Get-Content outputs/dreams.jsonl -Tail 3 | ConvertFrom-Json | ft
```

### Start Option 1

```bash
# Create files
code fdo_agi_repo/copilot/glymphatic.py
code fdo_agi_repo/copilot/synaptic_pruner.py
code scripts/integrate_dreams.py
```

### Start Option 2

```bash
# Re-validate
python scripts/test_hippocampus.py
powershell scripts/run_dream_mode.ps1 -Iterations 20
```

### Start Option 3

```bash
# Phase 2
code docs/AGI_RESONANCE_INTEGRATION_PLAN.md
code scripts/test_wave_particle_duality.py
```

---

**Last Updated**: 2025-11-05 22:35  
**Status**: Ready for next agent  
**Priority**: Option 1 (Dream Integration)

---

Good luck! 🚀
