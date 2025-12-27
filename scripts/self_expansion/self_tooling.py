from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional
import time


@dataclass
class ToolPlan:
    name: str
    description: str
    entrypoint: str
    code: str


class SelfTooling:
    """
    Self-Tooling (자기 도구 생성) 스켈레톤
    - 필요 도구 설계 → 코드 생성 → 간단 검증/등록(플레이스홀더)
    - 실제 코드 생성/검증 로직은 여기서 확장.
    """

    def __init__(self, tools_dir: Path):
        self.tools_dir = tools_dir
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self.tools_dir / ".self_tooling_state.json"

    def materialize(self, plan: ToolPlan) -> Path:
        target = self.tools_dir / f"{plan.name}.py"
        target.write_text(plan.code, encoding="utf-8")
        return target

    def basic_check(self, path: Path) -> bool:
        """간단 실행 검증 placeholder."""
        try:
            subprocess.run([sys.executable, "-m", "py_compile", str(path)], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def smoke_run(self, path: Path, entrypoint: str = "main") -> bool:
        """
        매우 제한된 스모크 실행: import 후 entrypoint 존재 여부만 확인.
        """
        try:
            code = (
                "import importlib.util, pathlib;"
                f"path=pathlib.Path({path.as_posix()!r});"
                "spec=importlib.util.spec_from_file_location('auto_tool', str(path));"
                "m=importlib.util.module_from_spec(spec);"
                "spec.loader.exec_module(m);"
                f"getattr(m, {entrypoint!r}, None)"
            )
            subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def register(self, plan: ToolPlan) -> Dict[str, Any]:
        # 너무 잦은 도구 생성 방지 (기본 10분 쿨다운)
        try:
            if self._state_path.exists():
                st = json.loads(self._state_path.read_text(encoding="utf-8"))
                last_ts = float(st.get("last_generated_ts") or 0)
                if (time.time() - last_ts) < 600 and st.get("last_name") == plan.name:
                    return {
                        "name": plan.name,
                        "path": str(self.tools_dir / f"{plan.name}.py"),
                        "verified": True,
                        "skipped": True,
                        "reason": "cooldown",
                    }
        except Exception:
            pass

        path = self.materialize(plan)
        ok = self.basic_check(path)
        smoke = self.smoke_run(path, plan.entrypoint) if ok else False
        info = {
            "name": plan.name,
            "path": str(path),
            "verified": ok and smoke,
        }
        # index 갱신
        index_path = self.tools_dir / "index.json"
        try:
            index = []
            if index_path.exists():
                index = json.loads(index_path.read_text(encoding="utf-8"))
            index = [i for i in index if i.get("name") != plan.name]
            index.append(info)
            index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        try:
            self._state_path.write_text(
                json.dumps(
                    {"last_generated_ts": time.time(), "last_name": plan.name},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass
        return info
