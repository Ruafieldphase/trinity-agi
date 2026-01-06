# Performance Dashboard Profile Guide

## Available Profiles

### 1. ops-daily (Daily Operations)

**Command**: `.\scripts\dashboard_ops_daily.ps1 -Open`

- **Period**: Last 7 days
- **Systems**: Orchestration, Monitoring, Daily Briefing
- **Thresholds**: 90% / 70%
- **Use Case**: Daily standup, routine monitoring

### 2. ops-focus (Critical Focus)

**Command**: `.\scripts\dashboard_ops_focus.ps1 -Open`

- **Period**: Last 3 days
- **Systems**: Orchestration only
- **Thresholds**: 92% / 75% (higher bar)
- **Sort**: Descending by effective rate
- **Use Case**: Deep dive into core system health

### 3. ops-attention (Needs Attention)

**Command**: `.\scripts\dashboard_ops_attention.ps1 -Open`

- **Period**: Last 7 days
- **Bands**: Needs + No Data only
- **Attention**: Respects band filter
- **Thresholds**: 90% / 70%
- **Use Case**: Action items, troubleshooting focus

### 4. ops-excellent (Excellence Showcase)

**Command**: `.\scripts\dashboard_ops_excellent.ps1 -Open`

- **Period**: Last 30 days
- **Bands**: Excellent only
- **Thresholds**: 95% / 80% (stringent)
- **Sort**: Descending (best first)
- **Use Case**: Success stories, best practices

## Creating Custom Profiles

Edit `configs/perf_dashboard_profiles.json`:

```json
{
  "profiles": {
    "my-custom-profile": {
      "Days": 14,
      "IncludeSystems": ["System A", "System B"],
      "ExcludeSystems": ["System C"],
      "OnlyBands": ["Good", "Needs"],
      "AttentionRespectsBands": true,
      "SortBy": "effective",
      "Order": "asc",
      "ExcellentAt": 92,
      "GoodAt": 75,
      "TopHistory": 15
    }
  }
}
```

### Profile Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `Days` | int | Analysis period | `7`, `30` |
| `IncludeSystems` | array | Whitelist systems | `["Orchestration"]` |
| `ExcludeSystems` | array | Blacklist systems | `["YouTube Learning"]` |
| `OnlyBands` | array | Filter bands | `["Needs", "NoData"]` |
| `AttentionRespectsBands` | bool | Top attention follows bands | `true` |
| `SortBy` | string | Sort key | `"effective"`, `"overall"`, `"name"` |
| `Order` | string | Sort direction | `"asc"`, `"desc"` |
| `ExcellentAt` | int | Excellent threshold (%) | `90`, `95` |
| `GoodAt` | int | Good threshold (%) | `70`, `80` |
| `TopHistory` | int | Max test runs in history | `10`, `20` |

## Usage Patterns

### Morning Standup

```powershell
# Quick overview
.\scripts\dashboard_ops_daily.ps1 -Open

# Check action items
.\scripts\dashboard_ops_attention.ps1 -Open
```

### Weekly Review

```powershell
# Full report
.\scripts\dashboard_quick_full.ps1 -Open

# Excellence showcase
.\scripts\dashboard_ops_excellent.ps1 -Open
```

### Incident Response

```powershell
# Focus on critical system
.\scripts\dashboard_ops_focus.ps1 -Open

# All systems needing attention
.\scripts\dashboard_ops_attention.ps1 -Open
```

### Custom Ad-hoc Analysis

```powershell
# Direct invocation with overrides
.\scripts\generate_performance_dashboard.ps1 `
  -Profile ops-daily `
  -Days 14 `
  -ExcellentAt 95 `
  -OnlyBands Needs,Good `
  -AttentionRespectsBands `
  -OpenDashboard
```

## Profile Override Behavior

Command-line parameters override profile settings:

```powershell
# Profile sets Days=7, but we override to 14
.\scripts\generate_performance_dashboard.ps1 -Profile ops-daily -Days 14
```

This allows flexible profile reuse with situation-specific adjustments.

## Tips

- **Local overrides**: Create `perf_dashboard_profiles.local.json` for personal profiles (gitignored)
- **Validation**: Run `.\scripts\validate_performance_dashboard.ps1 -VerboseOutput` to check profile syntax
- **Naming**: Use descriptive profile names like `sprint-review`, `oncall-focus`, etc.
- **Band combos**: Mix bands for custom views: `["Good", "Needs"]` for "not excellent"
