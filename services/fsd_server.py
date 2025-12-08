"""Lightweight FastAPI server for FSDController."""

import sys
from pathlib import Path

from fastapi import FastAPI
import uvicorn

# Ensure project root on sys.path for "services.*" imports inside fsd_controller
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fsd_controller import create_fsd_routes


app = FastAPI(title="FSD Controller", version="0.1")
create_fsd_routes(app)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8105, log_level="info")
