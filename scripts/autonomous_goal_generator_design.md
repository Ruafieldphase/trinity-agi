"""
Autonomous Goal Generator - Design Specification

작성일: 2025-11-05
Phase: 1 (즉시 가능)
목표: Resonance Simulator + Autopoietic Trinity → 목표 생성 연동

---

## 1. 개요 (Overview)

### 목적
시스템의 Resonance 메트릭과 Trinity 피드백을 분석하여
자동으로 우선순위가 지정된 목표 리스트를 생성한다.

### 핵심 원리
- **입력**: 정량적 메트릭 (Resonance) + 정성적 피드백 (Trinity)
- **처리**: 규칙 기반 분석 + 임계값 비교
- **출력**: 우선순위 목표 리스트 (JSON)

---

## 2. 입력 스키마 (Input Schema)

### 2.1 Resonance Metrics (정량적)

Source: `outputs/resonance_simulation_latest.json`

```json
{
  "info_density": 0.523,
  "resonance": 0.782,
  "entropy": 0.234,
  "horizon_crossings": 3,
  "temporal_phase": 4.2,
  "final_step": 336
}
```

**해석 규칙**:

| 메트릭 | 임계값 | 의미 | 생성 목표 |
|--------|--------|------|-----------|
| `info_density` | > 0.7 | 정보 과부하 | "Simplify system architecture" |
| `info_density` | < 0.3 | 정보 부족 | "Increase data collection" |
| `resonance` | > 0.8 | 높은 공명 (안정) | "Maintain current approach" |
| `resonance` | < 0.4 | 낮은 공명 (불안정) | "Refactor core components" |
| `entropy` | > 0.5 | 높은 엔트로피 (혼란) | "Improve clarity and structure" |
| `entropy` | < 0.2 | 낮은 엔트로피 (경직) | "Explore new approaches" |
| `horizon_crossings` | > 5 | 빈번한 임계점 초과 | "Stabilize system dynamics" |
| `horizon_crossings` | < 2 | 안정적 동작 | "Incremental improvements" |

### 2.2 Trinity Feedback (정성적)

Source: `outputs/autopoietic_loop_report_latest.md`

**핵심 추출 항목**:

1. **Lua 관점 (관찰)**:
   - 이슈 개수 (Critical/Warning)
   - 리포트 제목 (예: "Performance degradation detected")

2. **Elo 관점 (검증)**:
   - 검증 결과 (Pass/Fail)
   - 실패 이유 요약

3. **Core 관점 (통합)**:
   - 통합 결론 (예: "Need optimization")
   - 권장 액션 (예: "Refactor memory management")

**파싱 방식**:
```python
# Markdown → JSON 변환
{
  "lua_issues": ["Performance degradation", "Memory leak"],
  "elo_verification": "Failed: 3 tests",
  "core_recommendation": "Refactor memory management"
}
```

---

## 3. 처리 로직 (Processing Logic)

### 3.1 Resonance State Analysis

```python
def analyze_resonance_state(metrics: dict) -> list[str]:
    """
    Resonance 메트릭을 분석하여 시스템 상태를 진단한다.
    
    Returns:
        List of state indicators (e.g., ["info_overload", "low_resonance"])
    """
    states = []
    
    if metrics["info_density"] > 0.7:
        states.append("info_overload")
    elif metrics["info_density"] < 0.3:
        states.append("info_starvation")
    
    if metrics["resonance"] < 0.4:
        states.append("low_resonance")
    elif metrics["resonance"] > 0.8:
        states.append("high_resonance")
    
    if metrics["entropy"] > 0.5:
        states.append("high_entropy")
    elif metrics["entropy"] < 0.2:
        states.append("low_entropy")
    
    if metrics["horizon_crossings"] > 5:
        states.append("unstable_dynamics")
    elif metrics["horizon_crossings"] < 2:
        states.append("stable_dynamics")
    
    return states
```

### 3.2 Trinity Feedback Extraction

```python
def extract_trinity_feedback(report_path: str) -> dict:
    """
    Trinity 보고서에서 핵심 피드백을 추출한다.
    
    Returns:
        {
            "lua_issues": list[str],
            "elo_status": str,
            "core_recommendation": str
        }
    """
    # Markdown 파일 파싱
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 정규표현식으로 섹션 추출
    lua_section = re.search(r'## Lua.*?(?=##)', content, re.DOTALL)
    elo_section = re.search(r'## Elo.*?(?=##)', content, re.DOTALL)
    core_section = re.search(r'## Core.*?(?=##)', content, re.DOTALL)
    
    return {
        "lua_issues": extract_issues(lua_section),
        "elo_status": extract_status(elo_section),
        "core_recommendation": extract_recommendation(core_section)
    }
```

### 3.3 Goal Generation

```python
def generate_goals(resonance_states: list[str], trinity_feedback: dict) -> list[dict]:
    """
    Resonance 상태와 Trinity 피드백을 결합하여 목표를 생성한다.
    
    Returns:
        List of goal dicts with title, description, priority, source
    """
    goals = []
    
    # Rule-based goal generation
    GOAL_RULES = {
        "info_overload": {
            "title": "Simplify System Architecture",
            "description": "Reduce information density by refactoring complex modules",
            "base_priority": 8
        },
        "low_resonance": {
            "title": "Refactor Core Components",
            "description": "Improve resonance by restructuring core logic",
            "base_priority": 9
        },
        "high_entropy": {
            "title": "Improve Clarity and Structure",
            "description": "Reduce entropy through better organization",
            "base_priority": 7
        },
        # ... more rules
    }
    
    # Apply rules
    for state in resonance_states:
        if state in GOAL_RULES:
            goal = GOAL_RULES[state].copy()
            goal["source"] = "resonance"
            goals.append(goal)
    
    # Add Trinity-derived goals
    if trinity_feedback["core_recommendation"]:
        goals.append({
            "title": "Address Trinity Recommendation",
            "description": trinity_feedback["core_recommendation"],
            "base_priority": 8,
            "source": "trinity"
        })
    
    return goals
```

### 3.4 Goal Prioritization

```python
def prioritize_goals(goals: list[dict]) -> list[dict]:
    """
    목표에 우선순위를 할당한다.
    
    Factors:
    - base_priority: 규칙 기반 기본 우선순위
    - urgency: 메트릭 임계값 초과 정도
    - impact: 예상 영향도
    
    Returns:
        Sorted list of goals (highest priority first)
    """
    for goal in goals:
        # Calculate final priority
        urgency_boost = calculate_urgency(goal)
        impact_boost = estimate_impact(goal)
        
        goal["final_priority"] = (
            goal["base_priority"] +
            urgency_boost +
            impact_boost
        )
    
    # Sort by final_priority (descending)
    return sorted(goals, key=lambda g: g["final_priority"], reverse=True)
```

---

## 4. 출력 스키마 (Output Schema)

### 4.1 JSON Format

Output File: `outputs/autonomous_goals_latest.json`

```json
{
  "generated_at": "2025-11-05T14:30:00Z",
  "window_hours": 24,
  "input_sources": {
    "resonance_metrics": "outputs/resonance_simulation_latest.json",
    "trinity_report": "outputs/autopoietic_loop_report_latest.md"
  },
  "resonance_states": [
    "low_resonance",
    "high_entropy"
  ],
  "trinity_summary": {
    "lua_issues": ["Performance degradation"],
    "elo_status": "Failed: 3 tests",
    "core_recommendation": "Refactor memory management"
  },
  "goals": [
    {
      "id": 1,
      "title": "Refactor Core Components",
      "description": "Improve resonance by restructuring core logic",
      "base_priority": 9,
      "urgency_boost": 2,
      "impact_boost": 1,
      "final_priority": 12,
      "source": "resonance",
      "estimated_effort": "3 days",
      "dependencies": []
    },
    {
      "id": 2,
      "title": "Improve Clarity and Structure",
      "description": "Reduce entropy through better organization",
      "base_priority": 7,
      "urgency_boost": 1,
      "impact_boost": 1,
      "final_priority": 9,
      "source": "resonance",
      "estimated_effort": "2 days",
      "dependencies": [1]
    },
    {
      "id": 3,
      "title": "Address Trinity Recommendation",
      "description": "Refactor memory management",
      "base_priority": 8,
      "urgency_boost": 1,
      "impact_boost": 2,
      "final_priority": 11,
      "source": "trinity",
      "estimated_effort": "1 day",
      "dependencies": []
    }
  ],
  "summary": {
    "total_goals": 3,
    "high_priority": 2,
    "medium_priority": 1,
    "low_priority": 0
  }
}
```

### 4.2 Markdown Report (Optional)

Output File: `outputs/autonomous_goals_latest.md`

```markdown
# Autonomous Goals Report

Generated: 2025-11-05 14:30:00  
Window: Last 24 hours

## Summary

- **Total Goals**: 3
- **High Priority (≥10)**: 2
- **Medium Priority (7-9)**: 1
- **Low Priority (<7)**: 0

## Resonance State Analysis

- ⚠️ Low Resonance (0.38)
- ⚠️ High Entropy (0.67)

## Trinity Feedback

- **Lua**: Performance degradation detected
- **Elo**: Failed: 3 tests
- **Core**: Refactor memory management

## Goals (Prioritized)

### 1. Refactor Core Components (Priority: 12)

**Description**: Improve resonance by restructuring core logic  
**Source**: Resonance Analysis  
**Effort**: 3 days  
**Dependencies**: None

**Actions**:
- Review core module architecture
- Identify refactoring candidates
- Plan incremental migration

---

### 2. Address Trinity Recommendation (Priority: 11)

**Description**: Refactor memory management  
**Source**: Trinity Feedback (Core)  
**Effort**: 1 day  
**Dependencies**: None

**Actions**:
- Analyze memory usage patterns
- Implement caching strategy
- Optimize data structures

---

### 3. Improve Clarity and Structure (Priority: 9)

**Description**: Reduce entropy through better organization  
**Source**: Resonance Analysis  
**Effort**: 2 days  
**Dependencies**: #1 (Refactor Core Components)

**Actions**:
- Reorganize module structure
- Improve naming conventions
- Add documentation
```

---

## 5. 알고리즘 상세 (Algorithm Details)

### 5.1 Urgency Calculation

```python
def calculate_urgency(goal: dict) -> int:
    """
    긴급도를 계산한다 (0-3점).
    
    Factors:
    - 메트릭 임계값 초과 정도
    - 문제 지속 시간
    """
    urgency = 0
    
    # 임계값 초과 정도
    if goal["source"] == "resonance":
        if "critical" in goal["description"].lower():
            urgency += 3
        elif "warning" in goal["description"].lower():
            urgency += 2
        elif "notice" in goal["description"].lower():
            urgency += 1
    
    # Trinity 피드백 심각도
    if goal["source"] == "trinity":
        if "failed" in goal["description"].lower():
            urgency += 2
        elif "warning" in goal["description"].lower():
            urgency += 1
    
    return min(urgency, 3)  # 최대 3점
```

### 5.2 Impact Estimation

```python
def estimate_impact(goal: dict) -> int:
    """
    예상 영향도를 계산한다 (0-3점).
    
    Factors:
    - 영향 범위 (전체 시스템 vs 일부 모듈)
    - 개선 예상 효과
    """
    impact = 0
    
    # 키워드 기반 영향도 추정
    HIGH_IMPACT_KEYWORDS = ["core", "architecture", "refactor", "system-wide"]
    MEDIUM_IMPACT_KEYWORDS = ["module", "component", "feature"]
    
    desc_lower = goal["description"].lower()
    
    if any(kw in desc_lower for kw in HIGH_IMPACT_KEYWORDS):
        impact = 3
    elif any(kw in desc_lower for kw in MEDIUM_IMPACT_KEYWORDS):
        impact = 2
    else:
        impact = 1
    
    return impact
```

### 5.3 Effort Estimation

```python
def estimate_effort(goal: dict) -> str:
    """
    예상 소요 시간을 추정한다.
    
    Returns:
        Human-readable duration (e.g., "1 day", "3 days", "1 week")
    """
    # 간단한 휴리스틱
    priority = goal["final_priority"]
    
    if priority >= 10:
        return "3 days"  # 고우선순위, 복잡함
    elif priority >= 7:
        return "2 days"  # 중우선순위
    else:
        return "1 day"   # 저우선순위, 간단함
```

---

## 6. 에지 케이스 처리 (Edge Cases)

### 6.1 입력 파일 없음

```python
def load_resonance_metrics(path: str) -> dict:
    """Load resonance metrics with fallback."""
    if not os.path.exists(path):
        logger.warning(f"Resonance metrics not found: {path}")
        return {
            "info_density": 0.5,
            "resonance": 0.5,
            "entropy": 0.5,
            "horizon_crossings": 0
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### 6.2 목표 생성 없음

```python
def generate_goals(...) -> list[dict]:
    goals = []
    
    # ... goal generation logic ...
    
    # Fallback: 목표가 없으면 기본 목표 추가
    if not goals:
        goals.append({
            "title": "Maintain Current State",
            "description": "System is stable, continue monitoring",
            "base_priority": 5,
            "source": "fallback"
        })
    
    return goals
```

### 6.3 중복 목표 제거

```python
def deduplicate_goals(goals: list[dict]) -> list[dict]:
    """Remove duplicate goals based on title similarity."""
    seen_titles = set()
    unique_goals = []
    
    for goal in goals:
        title_lower = goal["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_goals.append(goal)
    
    return unique_goals
```

---

## 7. 확장 포인트 (Extension Points)

### Phase 2 (Learning Loop 통합 후)

- **학습 기반 우선순위 조정**
  - 과거 목표 달성률 → 우선순위 가중치
  - 실패한 목표 패턴 인식 → 회피

### Phase 3 (LLM 통합 후)

- **자연어 목표 생성**
  - Resonance + Trinity → LLM 프롬프트
  - LLM → 상세한 목표 설명 및 액션 아이템

### Phase 4 (자율 실행 후)

- **자동 목표 분해**
  - 복잡한 목표 → 하위 작업 DAG
  - 의존성 관리 및 자동 스케줄링

---

## 8. 테스트 계획 (Test Plan)

### 8.1 Unit Tests

```python
def test_analyze_resonance_state():
    metrics = {
        "info_density": 0.8,
        "resonance": 0.3,
        "entropy": 0.6,
        "horizon_crossings": 7
    }
    states = analyze_resonance_state(metrics)
    assert "info_overload" in states
    assert "low_resonance" in states
    assert "high_entropy" in states
    assert "unstable_dynamics" in states
```

### 8.2 Integration Tests

```python
def test_end_to_end_goal_generation():
    # Given: Resonance 메트릭과 Trinity 보고서
    resonance_path = "test_data/resonance_metrics.json"
    trinity_path = "test_data/trinity_report.md"
    
    # When: Goal Generator 실행
    goals = generate_autonomous_goals(resonance_path, trinity_path)
    
    # Then: 목표가 생성됨
    assert len(goals) >= 3
    assert goals[0]["final_priority"] >= goals[-1]["final_priority"]
```

### 8.3 Smoke Test

```bash
# Resonance Simulator 실행
python scripts/resonance_simulator.py

# Trinity Cycle 실행
.\scripts\autopoietic_trinity_cycle.ps1 -Hours 24

# Goal Generator 실행
python scripts/autonomous_goal_generator.py --hours 24

# 결과 확인
code outputs/autonomous_goals_latest.json
code outputs/autonomous_goals_latest.md
```

---

## 9. 구현 체크리스트 (Implementation Checklist)

### Phase 1.1: 설계 완료 (현재)

- [x] 입력/출력 스키마 정의
- [x] 처리 로직 설계
- [x] 알고리즘 상세화
- [x] 테스트 계획 수립

### Phase 1.2: 핵심 구현 (다음)

- [ ] `autonomous_goal_generator.py` 생성
- [ ] `analyze_resonance_state()` 구현
- [ ] `extract_trinity_feedback()` 구현
- [ ] `generate_goals()` 구현
- [ ] `prioritize_goals()` 구현
- [ ] JSON/Markdown 출력 생성

### Phase 1.3: 테스트 및 통합

- [ ] Unit Tests 작성
- [ ] Integration Tests 작성
- [ ] Smoke Test 실행
- [ ] VS Code Task 등록
- [ ] PowerShell 러너 작성

### Phase 1.4: 문서화 및 배포

- [ ] 사용자 가이드 작성
- [ ] 핸드오프 문서 업데이트
- [ ] Phase 1 완료 보고서 작성

---

## 10. 예상 결과 (Expected Output Example)

### 시나리오: 낮은 공명도 + 높은 엔트로피

**입력**:
```json
{
  "resonance": 0.35,
  "entropy": 0.68,
  "info_density": 0.55,
  "horizon_crossings": 4
}
```

**출력**:
```json
{
  "goals": [
    {
      "id": 1,
      "title": "Refactor Core Components",
      "final_priority": 12,
      "estimated_effort": "3 days"
    },
    {
      "id": 2,
      "title": "Improve Clarity and Structure",
      "final_priority": 9,
      "estimated_effort": "2 days"
    },
    {
      "id": 3,
      "title": "Monitor System Stability",
      "final_priority": 7,
      "estimated_effort": "1 day"
    }
  ]
}
```

---

**설계 승인**: ✅ Ready for Implementation  
**다음 단계**: `scripts/autonomous_goal_generator.py` 구현 시작  
**예상 완료**: 2025-11-07 (2-3일)
"""
