# Monitoring Dashboard Changes - 2025-10-26

This change set delivers two low-risk UX improvements aligned with the handover and current monitoring goals.

## What changed

- Persona trend sparklines
  - Added tooltips showing time and last value (Success% or Duration).
  - Color coding continues to respect injected thresholds.
- Trend metric toggle
  - New toggle button in Persona Performance to switch sparkline metric:
    - Trend: Success% (default)
    - Trend: Duration(s)
  - Table header updates accordingly.
  - Chart instances are safely destroyed and recreated to prevent overlay.

## Files touched

- `scripts/monitoring_dashboard_template.html`
  - Added toggle button and UI labels.
  - Enabled sparkline tooltips with timestamp.
  - Managed chart lifecycle (bar + sparklines).

## How to use

- Open `outputs/monitoring_dashboard_latest.html`.
- In the “🧠 Persona Performance” card, click “Trend: Success%” to toggle to “Trend: Duration(s)”.
- Hover over sparklines to see per-bin timestamp and value.

## Notes

- No changes required to the collector or generator pipeline.
- Threshold precedence remains: `AGI.Thresholds` > `Health.thresholds_ui` > `Health.thresholds`.
- Auto-refresh remains compatible; sparklines and bar chart reinitialize safely.

---

## Additional hardening (later on 2025-10-26)

- Auto-refresh preference persisted via `localStorage` and restored on load.
- Auto-pause when tab is hidden; resume only if the user preference is enabled.
- Clear timers on page unload to prevent leaks/overlays.
- Verified by regenerating the 24h report; `outputs/monitoring_dashboard_latest.html` includes `setAutoRefresh`, `visibilitychange`, and `beforeunload` handlers.

---

## Interval selector, in-flight guard, and markup fixes (final pass on 2025-10-26)

- Auto-refresh interval selector added (15s/30s/60s/2m/5m) with persistence via `localStorage`.
- In-flight refresh guard prevents overlapping fetch/render during slow network.
- Fixed a regression where stray inline JS leaked into the HTML body; removed and restored missing sections in template.
- Restored “Alert Severity Distribution” two-column layout (left: doughnut + badges, right: Recent Critical Alerts) and added the missing closing `</div>` for the row wrapper.
- Regenerated 24h report and confirmed the section renders with proper structure in `outputs/monitoring_dashboard_latest.html`.
