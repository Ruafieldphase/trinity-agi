from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_direct_youtube_upload_is_not_public_by_default() -> None:
    source = (ROOT / "scripts" / "upload_to_youtube.py").read_text(encoding="utf-8")

    assert 'DEFAULT_PRIVACY_STATUS = "private"' in source
    assert "dry_run=True" in source
    assert "confirm_upload=True" in source
    assert "--confirm-upload" in source
    assert '"privacyStatus": privacy_status' in source
    assert "--confirm-public-upload" in source
    assert '"privacyStatus": "public"' not in source


def test_direct_youtube_upload_confirm_gates_behave() -> None:
    script_dir = ROOT / "scripts"
    sys.path.insert(0, str(script_dir))
    try:
        spec = importlib.util.spec_from_file_location("upload_to_youtube", script_dir / "upload_to_youtube.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(script_dir))
        except ValueError:
            pass

    assert asyncio.run(module.upload_video(dry_run=True)) is None

    try:
        asyncio.run(module.upload_video(dry_run=False, confirm_upload=False))
    except ValueError as exc:
        assert "confirm_upload=True" in str(exc)
    else:
        raise AssertionError("real upload without confirm_upload should fail")

    try:
        asyncio.run(module.upload_video(privacy_status="public", confirm_public_upload=False, dry_run=True))
    except ValueError as exc:
        assert "--confirm-public-upload" in str(exc)
    else:
        raise AssertionError("public upload without confirm_public_upload should fail")


def test_bulk_scheduler_requires_confirm_for_real_uploads() -> None:
    source = (ROOT / "scripts" / "youtube_bulk_scheduler.py").read_text(encoding="utf-8")

    assert "--confirm-upload" in source
    assert "--limit" in source
    assert "SAFE DEFAULT" in source
    assert "effective_dry_run = args.dry_run or not args.confirm_upload" in source
    assert '"privacyStatus": "private"' in source


def test_paths_example_loads_without_external_dependencies() -> None:
    config_path = ROOT / "config" / "paths.example.yaml"
    resolver_path = ROOT / "scripts" / "path_config.py"
    spec = importlib.util.spec_from_file_location("trinity_path_config", resolver_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    previous = os.environ.get("AGI_WORKSPACE_ROOT")
    previous_workspace = os.environ.get("WORKSPACE_ROOT")
    os.environ.pop("AGI_WORKSPACE_ROOT", None)
    os.environ.pop("WORKSPACE_ROOT", None)
    try:
        values = module.load_path_config(config_path)
        resolved = module.resolve_paths(config_path)
    finally:
        if previous is not None:
            os.environ["AGI_WORKSPACE_ROOT"] = previous
        if previous_workspace is not None:
            os.environ["WORKSPACE_ROOT"] = previous_workspace

    assert values["agi_workspace_root"] == "."
    assert values["outputs"] == "outputs"
    assert resolved["agi_workspace_root"] == ROOT.resolve()
    assert resolved["outputs"] == (ROOT / "outputs").resolve()
    assert resolved["archive_workspace"] is None

    previous = os.environ.get("AGI_WORKSPACE_ROOT")
    previous_workspace = os.environ.get("WORKSPACE_ROOT")
    os.environ["AGI_WORKSPACE_ROOT"] = str(ROOT / "custom_agi")
    os.environ.pop("WORKSPACE_ROOT", None)
    try:
        overridden = module.resolve_paths(config_path)
    finally:
        if previous is None:
            os.environ.pop("AGI_WORKSPACE_ROOT", None)
        else:
            os.environ["AGI_WORKSPACE_ROOT"] = previous
        if previous_workspace is not None:
            os.environ["WORKSPACE_ROOT"] = previous_workspace

    assert overridden["agi_workspace_root"] == (ROOT / "custom_agi").resolve()
