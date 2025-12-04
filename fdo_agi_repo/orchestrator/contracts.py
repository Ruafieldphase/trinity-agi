from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class TaskSpec(BaseModel):
    task_id: str
    title: str
    goal: str
    constraints: List[str] = []
    inputs: Dict[str, Any] = {}
    scope: Literal["doc", "code", "analysis"] = "doc"
    permissions: List[Literal["READ","WRITE","WEB","EXEC"]] = ["READ"]
    evidence_required: bool = True

class Action(BaseModel):
    type: Literal["TOOL_CALL"]
    tool: Literal["rag","web","fileio","codeexec","tabular"]
    args: Dict[str, Any] = {}

class PersonaOutput(BaseModel):
    task_id: str
    persona: Literal["thesis","antithesis","synthesis"]
    summary: str
    rationale: str = ""
    actions: List[Action] = []
    citations: List[Dict[str, str]] = []

class ToolCallResult(BaseModel):
    tool: str
    ok: bool
    output: Dict[str, Any] = {}
    artifacts: List[Dict[str, str]] = []
    cost: Dict[str, Any] = {}
    notes: str = ""

class EvalReport(BaseModel):
    task_id: str
    quality: float = 0.0
    evidence_ok: bool = False
    risks: List[str] = []
    notes: str = ""

class RUNEReport(BaseModel):
    task_id: str
    impact: float = 0.0
    transparency: float = 0.0
    confidence: float = 0.0
    risks: List[str] = []
    recommendations: List[str] = []
    replan: bool = False
