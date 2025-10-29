from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, Optional


class MetricsLogger:
    """
    Safe wrapper around Google Cloud Logging for structured metrics logs.
    Falls back to stdlib logging if google-cloud-logging is unavailable.
    """

    def __init__(self, project_id: Optional[str] = None, log_name: str = "feedback-loop") -> None:
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
        self.log_name = log_name
        self._client = None
        self._logger = None
        self._use_cloud = False

        try:
            # Lazy import to avoid hard dependency
            from google.cloud import logging as cloud_logging  # type: ignore
            self._client = cloud_logging.Client(project=self.project_id) if self.project_id else cloud_logging.Client()
            self._logger = self._client.logger(self.log_name)
            self._use_cloud = True
        except Exception as e:
            # Fallback to std logging
            logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
            self._std_logger = logging.getLogger(self.log_name)
            self._std_logger.debug("Falling back to std logging: %s", e)

    def log_struct(self, payload: Dict[str, Any], severity: str = "INFO", dry_run: bool = False) -> None:
        if dry_run:
            print(json.dumps({"severity": severity, **payload}, ensure_ascii=False))
            return
        if self._use_cloud and self._logger is not None:
            # Rely on default resource detection (Cloud Run sets resource automatically)
            self._logger.log_struct(payload, severity=severity)
        else:
            self._std_logger.info(json.dumps(payload, ensure_ascii=False))


def log_feedback_metrics(
    *,
    service_name: Optional[str],
    cache_hit_rate: float,
    memory_usage_percent: float,
    avg_ttl_seconds: float,
    unified_health_score: float,
    project_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
) -> None:
    """
    Emit structured metrics for Feedback Loop. These can be picked up by
    logs-based metrics (logging.googleapis.com/user/*) configured in Cloud Monitoring.

    Fields:
    - cache_hit_rate: 0.0 ~ 1.0
    - memory_usage_percent: 0 ~ 100
    - avg_ttl_seconds: >= 0
    - unified_health_score: 0 ~ 100
    """
    payload: Dict[str, Any] = {
        "component": "feedback_loop",
        "metric": "feedback_metrics",
        "service_name": service_name,
        "cache_hit_rate": float(cache_hit_rate),
        "cache_memory_usage_percent": float(memory_usage_percent),
        "cache_avg_ttl_seconds": float(avg_ttl_seconds),
        "unified_health_score": float(unified_health_score),
    }
    if extra:
        payload.update(extra)

    logger = MetricsLogger(project_id=project_id)
    logger.log_struct(payload, severity="INFO", dry_run=dry_run)
