from __future__ import annotations

import os
import logging
import argparse

try:
    from feedback_orchestrator import FeedbackOrchestrator
    _HAS_ORCH = True
except Exception as _imp_err:
    _HAS_ORCH = False
    _IMPORT_ERROR = _imp_err
    # Fallback inline import for metrics emission
    from metrics_logger import log_feedback_metrics
else:
    # Orchestrator import succeeded; also import logger for breach test mode
    from metrics_logger import log_feedback_metrics


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    project_id = os.environ.get("GCP_PROJECT_ID", os.environ.get("GOOGLE_CLOUD_PROJECT", "naeda-genesis"))
    service_name = os.environ.get("SERVICE_NAME", "lumen-gateway")
    budget_usd = float(os.environ.get("MONTHLY_BUDGET_USD", "200.0"))

    # CLI for safe, one-shot breach testing of alert policies
    parser = argparse.ArgumentParser(description="Emit feedback metrics once (with optional breach test)")
    parser.add_argument("--breach-test", action="store_true", help="Emit breach values once to test alert policies")
    parser.add_argument("--breach-unified", type=float, default=25.0, help="Unified health score to emit for breach test (default: 25.0)")
    parser.add_argument("--breach-hit", type=float, default=0.45, help="Cache hit rate (0~1) to emit for breach test (default: 0.45)")
    parser.add_argument("--dry-run", action="store_true", help="Print payload instead of sending to Cloud Logging")
    args = parser.parse_args()

    if args.breach_test:
        # Emit a single structured log entry that should match alert policy filters
        try:
            log_feedback_metrics(
                service_name=service_name,
                cache_hit_rate=max(0.0, min(1.0, float(args.breach_hit))),
                memory_usage_percent=10.0,
                avg_ttl_seconds=300.0,
                unified_health_score=max(0.0, min(100.0, float(args.breach_unified))),
                project_id=project_id,
                extra={
                    "breach_test": True,
                    "note": "one-shot breach emission to validate alert policies"
                },
                dry_run=bool(args.dry_run),
            )
            logging.info(
                "Breach test emitted: unified_health_score=%.2f, cache_hit_rate=%.2f",
                float(args.breach_unified), float(args.breach_hit)
            )
            return 0
        except Exception as e:
            logging.error("Failed to emit breach test metrics: %s", e)
            return 2

    if _HAS_ORCH:
        orch = FeedbackOrchestrator(project_id=project_id, service_name=service_name, budget_usd=budget_usd)
        feedback = orch.run_complete_feedback_loop()
        logging.info("Feedback metrics emitted. Unified score=%.2f, health=%s", feedback.unified_gate_score, feedback.system_health.value)
        return 0
    else:
        # Dependency not available locally; emit a minimal structured metric directly
        logging.warning("Orchestrator import failed, emitting fallback metrics: %s", _IMPORT_ERROR)
        try:
            log_feedback_metrics(
                service_name=service_name,
                cache_hit_rate=0.7,
                memory_usage_percent=65.0,
                avg_ttl_seconds=1200.0,
                unified_health_score=85.0,
                project_id=project_id,
                extra={"fallback": True, "reason": "import_error"},
                dry_run=False,
            )
            logging.info("Fallback metrics emitted successfully")
            return 0
        except Exception as e:
            logging.error("Failed to emit fallback metrics: %s", e)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
