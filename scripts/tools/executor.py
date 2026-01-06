#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tools Executor (stub v1)
"""

from __future__ import annotations

from typing import Any, Dict


def run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": False, "reason": "stub_only", "tool": name}

