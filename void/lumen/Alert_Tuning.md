# Alert Tuning (ELO)

- **Efficiency**: Start warn 0.20, crit 0.10. Domain-level alerts mirror globals.
- **Intent Entropy**: Warn 1.8, adjust per taxonomy breadth. Domain entropy too high → prune/merge tags.
- **Samples**: Starvation alert if <10 for 15m; adjust for your QPS.
- Combine signals: `efficiency low` + `entropy high` → topic drift or labeler drift.
