#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compat wrapper for docs/imports:
- docs refer to `orchestrator/amygdala.py`
- real implementation lives in `fdo_agi_repo/orchestrator/amygdala.py`
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load() -> object:
    ws = Path(__file__).resolve().parents[1]
    target = ws / "fdo_agi_repo" / "orchestrator" / "amygdala.py"
    name = "_fdo_orchestrator_amygdala"
    spec = importlib.util.spec_from_file_location(name, str(target))
    if spec is None or spec.loader is None:
        raise ImportError(f"failed_to_load_spec:{target}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_m = _load()
for _k in dir(_m):
    if _k.startswith("_"):
        continue
    globals()[_k] = getattr(_m, _k)

