---
title: desktop commander mcp
date: 2025-08-23
url: https://www.perplexity.ai/search/https://www.perplexity.ai/search/44c63d26-26bd-4e63-bd85-3a5c7f485ea6
tags: perplexity, ai, internet
uuid: 44c63d26-26bd-4e63-bd85-3a5c7f485ea6
model: turbo
mode: COPILOT
---
# desktop commander mcp

Desktop Commander MCP는 Claude Desktop 등 주요 MCP (Model Context Protocol) 클라이언트에서 사용하는 오픈소스 도구로, 자연어 명령을 통해 PC의 파일 시스템과 터미널을 직접 제어할 수 있게 해주는 강력한 자동화 툴입니다. 개발자 및 파워유저들이 반복되는 작업을 쉽게 자동화하고, 시스템 관리・코드 편집・파일 관리 등 다양한 작업을 효율적으로 처리할 수 있도록 설계되었습니다.[1][3][5]

## 주요 특징
- **다양한 OS 지원:** Windows, macOS, Linux 모두 지원.
- **작업 자동화:** 자연어로 파일 읽기, 쓰기, 찾기, 디렉토리 생성/이동/삭제, 압축 및 압축 해제, 터미널 명령어 실행, 프로세스 관리 등 가능.[4][5]
- **보안 및 권한 제한:** 접근 가능한 디렉터리, 차단 명령어, 읽기/쓰기 제한 등 상세한 보안 설정 가능.[3][5]
- **대용량 프로젝트 지원:** 수만 개 파일/수백만 라인의 대규모 코드베이스 작업도 문제없이 지원.[3]
- **자동 업데이트:** 설치 후 Claude Desktop 재시작 시 자동으로 최신 버전 유지.[1][3]
- **무료 오픈소스:** 별도의 추가 요금 없이 자유롭게 사용, 단 Claude Pro 구독 필요.[3]

## 설치 및 사용법
1. **사전 설치**
   - Claude Desktop 앱
   - Node.js(v18.18.0 이상)

2. **설치 방법 (예시, macOS 기준)**
   - 터미널에서 다음 명령 실행:
     ```bash
     npx @wonderwhy-er/desktop-commander@latest setup
     ```
   - 또는 Smithery 를 통한 설치:
     ```bash
     npx -y @smithery/cli install @wonderwhy-er/desktop-commander --client claude
     ```

3. **수동 설정**
   - `claude_desktop_config.json`에 MCP 서버 등록:
     ```json
     "mcpServers": {
       "desktop-commander": {
         "command": "npx",
         "args": ["-y", "@wonderwhy-er/desktop-commander"]
       }
     }
     ```
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. **도커 지원:** Node.js 없이 Docker 컨테이너로만 실행하는 강제 격리 환경도 지원.[1]

## 대표 명령 예시
- "내 문서 폴더의 모든 PDF 파일 찾아줘"
- "Downloads 디렉토리의 모든 파일을 test.zip으로 압축해줘. 비밀번호는 test123으로"
- "Documents/info.md 내용을 요약해줘"
- "rm 명령을 블랙리스트에 추가해줘" (명령어 차단)
- "python으로 실행 중인 모든 프로세스를 종료해줘"[4]

## 활용 시 주의점
- 실제 파일 변경・삭제 등의 명령 실행 전 반드시 Claude가 제안하는 작업을 꼼꼼히 검토할 것.[5][4]
- 권한 제한, 명령 차단 설정 등 보안 옵션을 적극 활용할 것.[5][3]

Desktop Commander MCP는 Claude Desktop의 생산성, 자동화, 개발 환경 통합을 획기적으로 끌어올리는 도구로, 개발자 뿐 아니라 다양한 윈도우/맥/리눅스 사용자의 반복 작업 자동화에 폭넓게 활용되고 있습니다.[4][5][3]

## Sources

1. [Desktop Commander MCP - Terminal Commands and File Editing ...](https://desktopcommander.app)
2. [wonderwhy-er/DesktopCommanderMCP: This is MCP ... - GitHub](https://github.com/wonderwhy-er/DesktopCommanderMCP)
3. [Claude AI 완벽 가이드: Desktop Commander MCP로 생산성 높이기](https://birdspring.com/claude-ai-%EC%99%84%EB%B2%BD-%EA%B0%80%EC%9D%B4%EB%93%9C-desktop-commander%EB%A1%9C-%EC%83%9D%EC%82%B0%EC%84%B1-%EB%86%92%EC%9D%B4%EA%B8%B0/)
4. [MCP 인기 서버 소개 #1 Desktop Commander | 장승국 - LinkedIn](https://kr.linkedin.com/posts/lou2_github-wonderwhy-erclaudedesktopcommander-activity-7310208889503809536-3JhF)
5. [Desktop Commander MCP - 데스크톱 자동화의 새로운 패러다임 🖥️](https://memoryhub.tistory.com/entry/Desktop-Commander-MCP-%EB%8D%B0%EC%8A%A4%ED%81%AC%ED%86%B1-%EC%9E%90%EB%8F%99%ED%99%94%EC%9D%98-%EC%83%88%EB%A1%9C%EC%9A%B4-%ED%8C%A8%EB%9F%AC%EB%8B%A4%EC%9E%84-%F0%9F%96%A5%EF%B8%8F)
6. [Desktop Commander (MCP) for Claude – The "Cost-Capped ...](https://www.reddit.com/r/ClaudeAI/comments/1kcpzmd/desktop_commander_mcp_for_claude_the_costcapped/)
7. [Desktop Commander MCP 서버 (모듈식 FastMCP 구현) - LobeHub](https://lobehub.com/ko/mcp/mcp-mirror-nexus-digital-automations_mcp-filesystem-updated?activeTab=deployment)
8. [mcp/desktop-commander - Docker Image](https://hub.docker.com/r/mcp/desktop-commander)

## Related Questions

- Explore how to automate file system tasks with Desktop Commander MCP
- Learn to integrate Desktop Commander MCP with Claude Desktop
- Discover security best practices when using Desktop Commander MCP
- Find common terminal commands supported by Desktop Commander MCP
- Get setup troubleshooting tips for Windows, macOS, and Linux environments
