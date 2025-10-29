# -*- coding: utf-8 -*-
"""
Phase 4 Verification: Pattern Learning

Steps:
1) Run learn_bqi_patterns.py to generate model from ledger
2) Call analyse_question() before/after model to compare coordinates
"""
from __future__ import annotations
import importlib
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure we can import learner and adapter
HERE = Path(__file__).resolve().parent
# Discover workspace root that holds scripts/rune/bqi_adapter.py
ADAPTER_DIR = None
for p in [HERE] + list(HERE.parents):
    cand = p / ".." / ".."  # climb two levels as a quick check
    for base in [p, p.parent, cand.resolve() if cand.exists() else p]:
        probe = base / "scripts" / "rune" / "bqi_adapter.py"
        if probe.exists():
            ADAPTER_DIR = probe.parent
            break
    if ADAPTER_DIR:
        break
if ADAPTER_DIR is None:
    # Fallback to the typical layout
    ADAPTER_DIR = HERE.parents[2] / "scripts" / "rune"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(ADAPTER_DIR))

# Optional UTF-8 setup
try:
    import encoding_setup  # type: ignore  # noqa: F401
except Exception:
    pass

from learn_bqi_patterns import main as learn_main  # type: ignore

# Try normal import; fallback to direct file loader
try:
    import bqi_adapter  # type: ignore
except ModuleNotFoundError:
    import importlib.util
    adapter_path = ADAPTER_DIR / "bqi_adapter.py"
    spec = importlib.util.spec_from_file_location("bqi_adapter", str(adapter_path))
    if spec and spec.loader:
        bqi_adapter = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(bqi_adapter)  # type: ignore
    else:
        raise


def call_analyse(prompt: str, use_model: bool) -> Dict[str, Any]:
    # Reload adapter to reset cache
    mod = importlib.reload(bqi_adapter)
    if not use_model:
        # Force empty model cache
        try:
            setattr(mod, "_MODEL_CACHE", {})
        except Exception:
            pass
    coord = mod.analyse_question(prompt)
    return coord.to_dict()


def print_diff(title: str, before: Dict[str, Any], after: Dict[str, Any]) -> None:
    print("\n===" + title + "===")
    print("before:", before)
    print("after :", after)
    deltas = []
    if before.get("priority") != after.get("priority"):
        deltas.append(f"priority {before.get('priority')} -> {after.get('priority')}")
    if before.get("rhythm_phase") != after.get("rhythm_phase"):
        deltas.append(f"rhythm {before.get('rhythm_phase')} -> {after.get('rhythm_phase')}")
    before_em = set(before.get("emotion", {}).get("keywords", []) or [])
    after_em = set(after.get("emotion", {}).get("keywords", []) or [])
    if before_em != after_em:
        deltas.append(f"emotion {sorted(before_em)} -> {sorted(after_em)}")
    if deltas:
        print("delta:", "; ".join(deltas))
    else:
        print("delta: (no change)")


def main() -> int:
    print("[Phase4] Learning model from ledger...")
    rc = learn_main()
    if rc != 0:
        print("[WARN] Learner returned non-zero; proceeding with test anyway.")

    samples = [
        # urgent failure analysis
        "긴급: 배포 실패 원인 분석하고 즉시 복구 계획 세워줘",
        # reflective evaluation
        "왜 우리 BQI 시스템이 효과적이었는지 회고하고 개선점을 정리해줘",
        # success gratitude / integration
        "덕분에 성공했어! 다른 시스템과 통합해서 다음 단계를 계획하자",
        # curiosity exploration
        "새로운 아이디어로 어떤 실험을 해볼 수 있을까?",
    ]

    for s in samples:
        before = call_analyse(s, use_model=False)
        after = call_analyse(s, use_model=True)
        print_diff(s[:30] + ("..." if len(s) > 30 else ""), before, after)

    print("\n[Phase4] Verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
