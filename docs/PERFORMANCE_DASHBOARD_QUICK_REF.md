# Performance Dashboard Quick Reference

## Quick Start Wrappers

### dashboard_quick_needs.ps1

**Purpose**: Show only systems requiring attention  
**Usage**: `.\scripts\dashboard_quick_needs.ps1 -Open`

- Filters to "Needs" band only
- Top attention respects band filter
- Exports JSON + CSV with metadata
- Updates latest aliases

### dashboard_quick_full.ps1

**Purpose**: Complete dashboard with all systems  
**Usage**: `.\scripts\dashboard_quick_full.ps1 -Open`

- Shows all bands (Excellent, Good, Needs, No Data)
- Full JSON/CSV export
- Allows empty test runs
- Updates latest aliases

### dashboard_ops_daily.ps1

**Purpose**: Daily operations view  
**Usage**: `.\scripts\dashboard_ops_daily.ps1 -Open`

- Uses 'ops-daily' profile (configurable via JSON)
- Predefined include/exclude filters
- Exports all formats

### dashboard_ops_focus.ps1

**Purpose**: Focus on critical systems  
**Usage**: `.\scripts\dashboard_ops_focus.ps1 -Open`

- Uses 'ops-focus' profile
- Targeted system monitoring
- Exports all formats

### dashboard_ops_attention.ps1

**Purpose**: Show only systems needing attention  
**Usage**: `.\scripts\dashboard_ops_attention.ps1 -Open`

- Filters to Needs + No Data bands
- Top attention respects band filter
- 7-day lookback period
- Exports all formats

### dashboard_ops_excellent.ps1

**Purpose**: Showcase excellent performing systems  
**Usage**: `.\scripts\dashboard_ops_excellent.ps1 -Open`

- Filters to Excellent band only
- 30-day trend analysis
- Higher thresholds (95%/80%)
- Celebrates wins and best practices

## Tools

### generate_performance_dashboard.ps1

Main dashboard generator with comprehensive filtering and export options.

**Key Parameters**:

- `-Days` - Analysis period (default: 7)
- `-OnlyBands` - Filter by performance bands
- `-AttentionRespectsBands` - Sync attention list with band filter
- `-Profile` - Use predefined profile
- `-ExportJson`, `-ExportCsv` - Export formats
- `-OpenDashboard` - Auto-open report

### compare_performance_periods.ps1

Compare metrics across different time periods to identify trends.

**Purpose**: Analyze performance evolution  
**Usage**: `.\scripts\compare_performance_periods.ps1 -PeriodDays1 3 -PeriodDays2 7 -OpenReport`

**Parameters**:

- `-PeriodDays1` - First period length (default: 7)
- `-PeriodDays2` - Second period length (default: 30)
- `-Label1` - First period label (default: "Short-term")
- `-Label2` - Second period label (default: "Long-term")
- `-OpenReport` - Auto-open comparison report

**Output**: Markdown report with:

- Overall metrics delta
- System-by-system comparison
- Trend indicators (IMPROVED/DEGRADED/STABLE)
- New/removed system detection

## Profile Wrappers

### Filter to specific bands

```powershell
.\scripts\generate_performance_dashboard.ps1 -OnlyBands Good,Needs -AttentionRespectsBands -Open
```

### Custom thresholds

```powershell
.\scripts\generate_performance_dashboard.ps1 -ExcellentAt 95 -GoodAt 80 -WriteLatest
```

### Export with custom period

```powershell
.\scripts\generate_performance_dashboard.ps1 -Days 30 -ExportJson -ExportCsv -WriteLatest
```

### Include specific systems

```powershell
.\scripts\generate_performance_dashboard.ps1 -IncludeSystems "Orchestration","Daily Briefing" -Open
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Days` | Analysis period | 7 |
| `-OnlyBands` | Filter bands (Excellent, Good, Needs, NoData) | All |
| `-AttentionRespectsBands` | Top attention follows band filter | Off |
| `-ExcellentAt` | Excellent band threshold (%) | 90 |
| `-GoodAt` | Good band threshold (%) | 70 |
| `-OpenDashboard` | Open MD in VS Code | Off |
| `-ExportJson` | Export metrics JSON | Off |
| `-ExportCsv` | Export metrics CSV (with metadata) | Off |
| `-WriteLatest` | Update *_latest.* aliases | Off |
| `-AllowEmpty` | Generate even with no data | Off |
| `-SortBy` | Sort by: effective, overall, name | effective |
| `-Order` | Sort order: asc, desc | asc |

## Output Files

- `outputs/performance_dashboard_YYYY-MM-DD.md` - Human-readable report
- `outputs/performance_metrics_YYYY-MM-DD.json` - Structured metrics
- `outputs/performance_metrics_YYYY-MM-DD.csv` - Tabular data with metadata headers
- `outputs/performance_*_latest.*` - Aliases to latest versions (with `-WriteLatest`)

## CSV Metadata Headers

When `-ExportCsv` is used, the CSV includes metadata comments:

```text
# Performance Metrics CSV - 2025-11-01 07:09:39
# Period: Last 7 days
# Systems Considered: 6
# Bands Considered: Needs Attention
# Systems Displayed: 1
# Top Attention Respects Bands: Yes
```

## Tips

- Use `-AttentionRespectsBands` with `-OnlyBands` to focus attention list
- Combine `-WriteLatest` with scripts that read latest aliases
- CSV metadata headers help external pipelines understand context
- Profile JSON files: `configs/perf_dashboard_profiles.json`
