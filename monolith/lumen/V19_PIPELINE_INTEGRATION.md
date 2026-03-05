# v1.9 — Pipeline Integration

## Files
- Reusable event recorder: `.github/workflows/lumen_v19_record_event_reusable.yaml`
- Auto record on release: `.github/workflows/lumen_v19_auto_record_on_release.yaml`
- ROI snapshot generator: `scripts/gen_roi_snapshot_v19.py`
- Snapshot workflow: `.github/workflows/lumen_v19_roi_snapshot.yaml`
- v1.4 Session Restore: `SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml`

## Usage
```bash
# v1.4 세션 복원
source SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml
l14.run

# 다른 워크플로에서 재사용 예시
# jobs.record_release:
#   uses: ./.github/workflows/lumen_v19_record_event_reusable.yaml
#   with:
#     env: prod
#     action: deploy
#     version: v1.9.0
#     author: ${{ github.actor }}
#     result: success
#     notes: "CD pipeline auto"

# ROI 스냅샷 실행
gh workflow run lumen_v19_roi_snapshot
```
