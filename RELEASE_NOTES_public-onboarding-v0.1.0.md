# public-onboarding-v0.1.0

This release marks the first public onboarding baseline for the Shion-Trinity system.

## Trinity AGI

Trinity AGI now presents itself first as the body/infrastructure layer that turns formed AI intent into safe local operation.

Included in this baseline:

- Upload helpers default to private/dry-run
- Real uploads require `--confirm-upload`
- Public uploads also require `--confirm-public-upload`
- Public safety CI checks upload safety boundaries
- 3-Minute Safety section at the top of README
- Dry-run first command
- Expected result for dry-run operation
- Shion -> Trinity -> evidence return flow

## Public Safety

This repository now includes public safety checks intended to make the first public entry safer:

- Dry-run/private upload boundaries
- Explicit confirmation gates for real and public uploads
- CI verification for public safety assumptions

## Next Direction

The next phase is path and environment cleanup:

- `SHION_ROOT`
- `AGI_WORKSPACE_ROOT`
- `WORKSPACE_ROOT`
- `config/paths.example.yaml` or `local_paths.example.json`
- hardcoded local path reduction

This release freezes the first public onboarding baseline before deeper internal path cleanup begins.

## Korean Summary

이 릴리즈는 Shion-Trinity 시스템의 첫 공개 온보딩 기준점입니다.

Trinity는 형성된 AI 의도를 안전한 로컬 운영으로 바꾸는 몸체/인프라 레이어로 정리되었습니다.

이번 기준점에는 다음이 포함됩니다.

- Trinity private/dry-run 기본값
- `--confirm-upload`, `--confirm-public-upload` 승인 경계
- public safety CI
- README 최상단 3분 안전 입구
- expected result
- Shion-Trinity 흐름도

다음 단계는 path resolver, config example, hardcoded local path cleanup입니다.
