# path-config-v0.1

This note records the first Trinity YouTube path configuration baseline.

## Trinity YouTube Path Config

This update connects the YouTube operation helpers to the public path configuration layer.

Included in this baseline:

- `scripts/upload_to_youtube.py` now uses `path_config.resolve_paths()`
- `scripts/youtube_bulk_scheduler.py` now uses `path_config.resolve_paths()`
- `config/paths.example.yaml` includes `ready_videos` and `ready_shorts`
- Direct upload and scheduler paths now derive from configurable roots
- Existing `YOUTUBE_READY_VIDEO_DIR` and `YOUTUBE_READY_SHORTS_DIR` overrides are preserved
- Dry-run scheduler initialization works without a YouTube token
- Dry-run/import path works without Google client packages
- Real uploads still require `--confirm-upload`
- Public uploads still require `--confirm-public-upload`
- Public safety behavior tests cover confirm gates and path config loading
- CI verifies the public safety path

## Why This Matters

This is the first small path cleanup step after `public-onboarding-v0.1.0`.

The public onboarding entry remains stable, while internal local path dependency begins to move into explicit configuration.

## Next Direction

Next steps should remain small:

1. Do not rewrite all hardcoded paths at once.
2. Connect one more lightweight file to path config.
3. Prefer files that read `outputs`, `memory`, or `logs`.
4. Keep `shion_runtime_server.py` for a later phase.

## Korean Summary

이 노트는 Trinity YouTube 계열의 첫 path-config 기준점입니다.

이번 변경으로 `upload_to_youtube.py`와 `youtube_bulk_scheduler.py`가 `path_config.resolve_paths()`를 사용하게 되었고, `ready_videos`, `ready_shorts` 경로가 공개 예시 설정에 추가되었습니다.

dry-run 경로는 YouTube token이나 Google client 패키지 없이도 확인 가능하며, 실제 업로드와 public 업로드는 여전히 명시적 confirm gate를 요구합니다.

다음 단계는 전체 경로를 한 번에 바꾸는 것이 아니라, Shion 또는 Trinity의 가벼운 파일 하나를 더 path config에 연결하는 것입니다.
