#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Storage (stub v1)
"""

from __future__ import annotations

from typing import Any, Dict


def put(key: str, value: Any) -> Dict[str, Any]:
    return {"ok": False, "reason": "stub_only", "key": key}


def get(key: str) -> Dict[str, Any]:
    return {"ok": False, "reason": "stub_only", "key": key}

