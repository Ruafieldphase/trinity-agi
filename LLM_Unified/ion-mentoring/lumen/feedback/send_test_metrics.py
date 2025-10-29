import argparse
import random
from metrics_logger import log_feedback_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Send test feedback metrics (structured logging)")
    parser.add_argument("--project-id", default=None, help="GCP project id (optional)")
    parser.add_argument("--service-name", default="lumen-gateway", help="Service name for logs")
    parser.add_argument("--hit-rate", type=float, default=0.72, help="Cache hit rate (0~1)")
    parser.add_argument("--memory-percent", type=float, default=68.5, help="Cache memory usage percent (0~100)")
    parser.add_argument("--ttl-seconds", type=float, default=1240, help="Average TTL in seconds")
    parser.add_argument("--health", type=float, default=87.0, help="Unified health score (0~100)")
    parser.add_argument("--dry-run", action="store_true", help="Print payload instead of sending")
    args = parser.parse_args()

    extra = {
        "event_id": f"test-{random.randint(1000, 9999)}",
        "source": "send_test_metrics.py",
    }

    log_feedback_metrics(
        service_name=args.service_name,
        cache_hit_rate=args.hit_rate,
        memory_usage_percent=args.memory_percent,
        avg_ttl_seconds=args.ttl_seconds,
        unified_health_score=args.health,
        project_id=args.project_id,
        extra=extra,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
