from __future__ import annotations

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


def test_bulk_scheduler_requires_confirm_for_real_uploads() -> None:
    source = (ROOT / "scripts" / "youtube_bulk_scheduler.py").read_text(encoding="utf-8")

    assert "--confirm-upload" in source
    assert "--limit" in source
    assert "SAFE DEFAULT" in source
    assert "effective_dry_run = args.dry_run or not args.confirm_upload" in source
    assert '"privacyStatus": "private"' in source
