# Trinity path-config-v0.1: YouTube Workflow as the First Operation Example

This note records the first Trinity path configuration baseline, using the YouTube workflow as the first operation example.

The YouTube workflow is a personal publishing use case, but the pattern is general: configurable paths, dry-run by default, explicit confirmation gates, private credentials, and CI-verified safety.

## Trinity YouTube Path Config

This update connects the first real operation helpers to the public path configuration layer.

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

The public onboarding entry remains stable, while internal local path dependency begins to move into explicit configuration. The specific workflow is YouTube publishing, but the reusable operating pattern can apply to other local automations such as blog publishing, backups, batch jobs, or local agent operations.

## Next Direction

Next steps should remain small:

1. Do not rewrite all hardcoded paths at once.
2. Connect one more lightweight file to path config.
3. Prefer files that read `outputs`, `memory`, or `logs`.
4. Keep `shion_runtime_server.py` for a later phase.

## Korean Summary

이 노트는 YouTube 작업을 첫 운영 예제로 삼은 Trinity path-config 기준점입니다.

YouTube 워크플로우는 개인적인 게시 작업 사례이지만, 그 패턴은 범용적입니다. 설정 가능한 경로, 기본 dry-run, 명시적 승인 경계, 비공개 인증 정보, CI로 검증되는 안전 경계가 핵심입니다.

이번 변경으로 `upload_to_youtube.py`와 `youtube_bulk_scheduler.py`가 `path_config.resolve_paths()`를 사용하게 되었고, `ready_videos`, `ready_shorts` 경로가 공개 예시 설정에 추가되었습니다.

dry-run 경로는 YouTube token이나 Google client 패키지 없이도 확인 가능하며, 실제 업로드와 public 업로드는 여전히 명시적 confirm gate를 요구합니다.

다음 단계는 전체 경로를 한 번에 바꾸는 것이 아니라, Shion 또는 Trinity의 가벼운 파일 하나를 더 path config에 연결하는 것입니다.
