"""Utility scripts package for the ion-mentoring project."""

from __future__ import annotations

from pathlib import Path

_root_scripts = Path(__file__).resolve().parents[3] / "scripts"
if _root_scripts.exists():
    _root_path = str(_root_scripts)
    package_path = globals().get("__path__")
    if isinstance(package_path, list) and _root_path not in package_path:
        # Make top-level ``scripts`` subpackages (e.g. ``scripts.rag``) discoverable
        package_path.append(_root_path)
