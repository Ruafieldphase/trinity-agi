from __future__ import annotations
from typing import Dict, Any, List

DANGEROUS = {"EXEC": 3, "WEB": 2, "WRITE": 1, "READ": 0}

def assess_risk(permissions: List[str]) -> int:
    return max((DANGEROUS.get(p, 0) for p in permissions), default=0)

def SAFE_pre(task: Dict[str, Any], ledger_tail: List[Dict[str, Any]]):
    risk = assess_risk(task.get("permissions", []))
    allowed = risk <= 1  # WRITE까지 자동 허용, WEB/EXEC는 승인 필요
    return {"allowed": allowed, "risk": risk, "needs_approval": risk >= 2}
