# v1.5 — Release Publisher with QA Gate

## 워크플로
- `.github/workflows/lumen_v15_release_publish_with_QA.yaml`

## 사용
1) GitHub → Actions → **lumen_v15_release_publish_with_QA** 실행
   - `tag = v1.5-rc` (또는 목표 버전)
   - `prerelease = true` (RC인 경우)

2) 파이프라인 흐름
   - **qa_precheck**: Dual-Gate QA 실행 → 결과 산출물 업로드
   - **release**: QA가 PASS일 때만 GitHub Release 게시
     - 본문: 기본 Release Notes + QA Diff Report 요약

## 산출물
- `logs/gate_pre.json`, `logs/gate_post.json`
- `docs/V15_QA_DIFF_REPORT.md`, `docs/V15_QA_RESULT_CARD.json`, `docs/V15_QA_SUMMARY.txt`
