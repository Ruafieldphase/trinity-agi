# Pandoc 설치 & PDF 변환 가이드 (Windows)

## 1. 설치 방법
### 옵션 A — 공식 설치 관리자
1. <https://github.com/jgm/pandoc/releases> 접속
2. 최신 `pandoc-*-windows-x86_64.msi` 다운로드
3. 설치 마법사에서 PATH 추가 옵션 체크
4. PowerShell에서 `pandoc --version`으로 확인

### 옵션 B — Scoop 패키지 관리자
```powershell
winget install --id=JGM.Pandoc -e
# 또는
scoop install pandoc
```

## 2. PDF 변환 명령 예시
```powershell
pandoc outputs/agi_research_onepager.md -o outputs/agi_research_onepager.pdf --from markdown --pdf-engine xelatex
pandoc outputs/agi_research_onepager_ko.md -o outputs/agi_research_onepager_ko.pdf --from markdown --pdf-engine xelatex
pandoc outputs/ion_research_brief.md -o outputs/ion_research_brief.pdf --from markdown --pdf-engine xelatex
pandoc outputs/ion_research_brief_ko.md -o outputs/ion_research_brief_ko.pdf --from markdown --pdf-engine xelatex
```
> xelatex 엔진이 없으면 MiKTeX 설치 후 재실행.

## 3. 대안 도구
- Word(Office) 설치 시: Markdown → Word → PDF 수동 변환 가능
- Python 경량 옵션: `pip install fpdf` 후 간단 텍스트 PDF 생성 (서식 제한)
