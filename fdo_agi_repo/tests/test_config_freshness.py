import os
import time
import tempfile
from pathlib import Path

import yaml


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def test_get_app_config_defaults_when_missing(monkeypatch):
    from fdo_agi_repo.orchestrator import config as cfg

    tmp_missing = Path(tempfile.gettempdir()) / "nonexistent_app_config.yaml"
    if tmp_missing.exists():
        tmp_missing.unlink()

    monkeypatch.setattr(cfg, "_APP_CONFIG_PATH", str(tmp_missing), raising=True)
    monkeypatch.setattr(cfg, "_APP_CONFIG_CACHE", None, raising=False)
    monkeypatch.setattr(cfg, "_APP_CONFIG_MTIME", None, raising=False)

    data = cfg.get_app_config()
    assert isinstance(data, dict)
    assert data.get("llm", {}).get("enabled") is False
    assert data.get("corrections", {}).get("enabled") is True


def test_get_app_config_mtime_reload(monkeypatch):
    from fdo_agi_repo.orchestrator import config as cfg

    # Ensure no env override interferes
    monkeypatch.delenv("EVAL_MIN_QUALITY", raising=False)

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "app.yaml"
        write_yaml(
            p,
            {
                "llm": {"enabled": False, "provider": "local_proxy"},
                "corrections": {"enabled": True, "max_passes": 2},
                "evaluation": {"min_quality": 0.6},
            },
        )

        monkeypatch.setattr(cfg, "_APP_CONFIG_PATH", str(p), raising=True)
        monkeypatch.setattr(cfg, "_APP_CONFIG_CACHE", None, raising=False)
        monkeypatch.setattr(cfg, "_APP_CONFIG_MTIME", None, raising=False)

        first = cfg.get_app_config()
        assert first["llm"]["enabled"] is False
        assert first["corrections"]["max_passes"] == 2
        assert cfg.get_evaluation_config()["min_quality"] == 0.6

        # Ensure mtime will differ on Windows (coarse mtime resolution)
        time.sleep(2.2)

        # Modify values and confirm reload picks them up
        write_yaml(
            p,
            {
                "llm": {"enabled": True, "provider": "local_proxy"},
                "corrections": {"enabled": True, "max_passes": 5},
                "evaluation": {"min_quality": 0.8},
            },
        )
        # Force filesystem to record a fresh mtime
        import os as _os
        _os.utime(p, None)

        second = cfg.get_app_config()
        assert second["llm"]["enabled"] is True
        assert second["corrections"]["max_passes"] == 5
        assert cfg.get_evaluation_config()["min_quality"] == 0.8


def test_env_overrides_for_corrections_and_eval(monkeypatch):
    from fdo_agi_repo.orchestrator import config as cfg

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "app.yaml"
        write_yaml(
            p,
            {
                "corrections": {"enabled": False, "max_passes": 2},
                "evaluation": {"min_quality": 0.5},
            },
        )

        monkeypatch.setattr(cfg, "_APP_CONFIG_PATH", str(p), raising=True)
        monkeypatch.setattr(cfg, "_APP_CONFIG_CACHE", None, raising=False)
        monkeypatch.setattr(cfg, "_APP_CONFIG_MTIME", None, raising=False)

        # Environment overrides corrections.enabled and max_passes
        monkeypatch.setenv("CORRECTIONS_ENABLED", "true")
        monkeypatch.setenv("CORRECTIONS_MAX_PASSES", "7")

        assert cfg.is_corrections_enabled() is True
        cconf = cfg.get_corrections_config()
        assert cconf["enabled"] is True
        assert cconf["max_passes"] == 7

        # EVAL_MIN_QUALITY env wins over file
        monkeypatch.setenv("EVAL_MIN_QUALITY", "0.9")
        econf = cfg.get_evaluation_config()
        assert abs(econf["min_quality"] - 0.9) < 1e-9
