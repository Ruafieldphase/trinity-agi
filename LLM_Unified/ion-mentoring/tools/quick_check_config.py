# quick_check_config.py
# 목적: Vertex AI 실행 구성이 settings/env 우선순위에 따라 제대로 적용되는지 빠르게 확인

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SYS_PATH_ADDED = str(ROOT / "ion-mentoring")
if SYS_PATH_ADDED not in sys.path:
    sys.path.insert(0, SYS_PATH_ADDED)

from app.config import settings  # type: ignore
from ion_first_vertex_ai import get_runtime_config  # type: ignore


def _fmt(value: Any) -> str:
    """빈 문자열까지 고려해 출력 포맷統일."""
    if value is None or value == "":
        return "<unset>"
    return str(value)


if __name__ == "__main__":
    project_id, location, model_name = get_runtime_config()
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    print("=== Runtime Config Check ===")
    print("--- Settings defaults ---")
    print(f"settings.vertex_project_id : {_fmt(settings.vertex_project_id)}")
    print(f"settings.vertex_location   : {_fmt(settings.vertex_location)}")
    print(f"settings.vertex_model      : {_fmt(settings.vertex_model)}")
    print(f"settings.phase4_enabled    : {_fmt(settings.phase4_enabled)}")
    print(f"settings.canary_percent    : {_fmt(settings.canary_traffic_percentage)}%")

    print("\n--- Environment overrides ---")
    print(f"VERTEX_PROJECT_ID          : {_fmt(os.getenv('VERTEX_PROJECT_ID'))}")
    print(f"VERTEX_LOCATION            : {_fmt(os.getenv('VERTEX_LOCATION'))}")
    print(f"VERTEX_MODEL               : {_fmt(os.getenv('VERTEX_MODEL'))}")
    print(f"GOOGLE_CLOUD_PROJECT       : {_fmt(os.getenv('GOOGLE_CLOUD_PROJECT'))}")
    print(f"GCP_PROJECT                : {_fmt(os.getenv('GCP_PROJECT'))}")
    print(f"GCP_LOCATION               : {_fmt(os.getenv('GCP_LOCATION'))}")
    print(f"GOOGLE_CLOUD_LOCATION      : {_fmt(os.getenv('GOOGLE_CLOUD_LOCATION'))}")
    print(f"GEMINI_MODEL               : {_fmt(os.getenv('GEMINI_MODEL'))}")
    print(f"PHASE4_ENABLED             : {_fmt(os.getenv('PHASE4_ENABLED'))}")
    print(f"CANARY_TRAFFIC_PERCENTAGE  : {_fmt(os.getenv('CANARY_TRAFFIC_PERCENTAGE'))}")

    print("\n--- Effective ---")
    print(f"Project                    : {_fmt(project_id)}")
    print(f"Location                   : {_fmt(location)}")
    print(f"Model                      : {_fmt(model_name)}")
    print(f"Credentials Path           : {_fmt(creds)}")

    if creds and creds not in ("<unset>", ""):
        creds_path = Path(creds)
        if not creds_path.is_absolute():
            creds_path = ROOT / creds_path
        print(f"Creds path exists? {creds_path.exists()} -> {creds_path}")
    else:
        print("Creds path exists? False -> (환경변수 미설정)")
