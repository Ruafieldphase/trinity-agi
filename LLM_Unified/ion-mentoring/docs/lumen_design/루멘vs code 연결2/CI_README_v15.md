# v1.5 CI — Image Build & Helm Package

## 수동 실행(태그 지정)
- 워크플로: `lumen_v15_build_and_release` → Run workflow → `tag` 입력 (예: `v1.5-rc`)

## 자동 동작
- `main` 브랜치에 변경이 들어오면:
  1) Docker 이미지를 빌드해 **ghcr.io/<owner>/lumen:<sha7>** 태그로 푸시
  2) Helm 차트를 패키징하여 **Artifacts**로 업로드

## 이미지 사용
- Helm values에서
```yaml
image:
  repository: ghcr.io/<owner>/lumen
  tag: <sha7 or v1.5-rc>
```
