---
title: desktop commander mcp
date: 2025-08-23
url: https://www.perplexity.ai/search/https://www.perplexity.ai/search/4f5c3710-a336-4480-a1da-ef293c55be9c
tags: perplexity, ai, internet
uuid: 4f5c3710-a336-4480-a1da-ef293c55be9c
model: pplx_pro
mode: COPILOT
---
# desktop commander mcp

Desktop Commander MCP는 Claude Desktop과 같은 MCP(Model Context Protocol) 클라이언트에서 자연어로 터미널 명령 실행, 파일 관리, 코드 편집 등 다양한 데스크톱 작업을 자동화해주는 오픈소스 도구입니다. Claude(및 Cursor 등 MCP 지원 클라이언트)와 PC(Windows, macOS, Linux)를 자연스럽게 연결해주는 브릿지 역할을 하며, 반복 작업이나 대규모 파일·코드 관리, 프로세스 제어까지 지원합니다.[1][2][3]

***

## 주요 특징
- **자연어 명령으로** 터미널 명령 실행, 파일 읽기/쓰기, 압축 해제, 파일 검색, 코드 수정, 프로세스 조회·종료 등이 가능
- **여러 OS 지원:** Windows, macOS, Linux에서 동작
- **보안 설정:** 허용 디렉토리/명령, 블랙리스트, 읽기/쓰기 제한 등 세분화된 설정 가능
- **완전 무료 오픈소스**(별도 API 비용 없음, Claude Pro 구독 필요)
- **대규모 코드베이스와 멀티 프로젝트 지원**(수만 개 파일, 수백만 라인도 사용 가능)

## 설치 방법 요약
1. **사전 조건:** Claude Desktop 앱 및 Node.js(v18.18.0 이상) 설치
2. **자동 설치(Smithery 이용):**
   ```bash
   npx -y @smithery/cli install @wonderwhy-er/desktop-commander --client claude
   ```
3. **직접 설치(npx 명령):**
   ```bash
   npx @wonderwhy-er/desktop-commander@latest setup
   ```
4. **macOS 간편 설치:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/wonderwhy-er/DesktopCommanderMCP/refs/heads/main/install.sh | bash
   ```
5. **설정 파일 수동 편집:** `claude_desktop_config.json`에 MCP 서버 항목을 추가
   ```json
   {
     "mcpServers": {
       "desktop-commander": {
         "command": "npx",
         "args": [
           "-y",
           "@wonderwhy-er/desktop-commander"
         ]
       }
     }
   }
   ```
   (설정 파일 위치: macOS는 `~/Library/Application Support/Claude/claude_desktop_config.json`, Windows는 `%APPDATA%\Claude\claude_desktop_config.json`, Linux는 `~/.config/Claude/claude_desktop_config.json`)[2][1]

## 활용 예시
- 디렉터리 생성/삭제, 압축 및 암호 설정, 패턴 기반 파일 검색, 텍스트 파일 내용 요약 등 각종 자동화 작업
- 프로세스 일괄 종료, 위험 명령어(예: rm) 실행 차단 등 고급 제어
- 반복적인 개발/파일 작업 루틴을 Claude에게 자연어로 요청·자동화

## 주의 및 TIP
- **강력한 자동화 도구이므로, 권한·범위 설정에 주의해야 합니다.**
- 실제 파일 삭제/변경 명령은 실행 전 꼭 검토 필요
- 설정에서 허용 디렉토리, 차단 명령어 등을 적극 활용해 시스템 안정성을 높이세요.[3][4]

***

이 도구를 PC에 설치하고 Claude(혹은 지원되는 MCP 클라이언트)에서 활성화하면, 자연어만으로도 매우 다양한 개발/자동화 워크플로우가 가능합니다.[1][2][3]

## Sources

1. [Desktop Commander MCP - Terminal Commands and File Editing ...](https://desktopcommander.app)
2. [Claude AI 완벽 가이드: Desktop Commander MCP로 생산성 높이기](https://birdspring.com/claude-ai-%EC%99%84%EB%B2%BD-%EA%B0%80%EC%9D%B4%EB%93%9C-desktop-commander%EB%A1%9C-%EC%83%9D%EC%82%B0%EC%84%B1-%EB%86%92%EC%9D%B4%EA%B8%B0/)
3. [Desktop Commander MCP - 데스크톱 자동화의 새로운 패러다임 🖥️](https://memoryhub.tistory.com/entry/Desktop-Commander-MCP-%EB%8D%B0%EC%8A%A4%ED%81%AC%ED%86%B1-%EC%9E%90%EB%8F%99%ED%99%94%EC%9D%98-%EC%83%88%EB%A1%9C%EC%9A%B4-%ED%8C%A8%EB%9F%AC%EB%8B%A4%EC%9E%84-%F0%9F%96%A5%EF%B8%8F)
4. [MCP 인기 서버 소개 #1 Desktop Commander | 장승국 - LinkedIn](https://kr.linkedin.com/posts/lou2_github-wonderwhy-erclaudedesktopcommander-activity-7310208889503809536-3JhF)
5. [wonderwhy-er/DesktopCommanderMCP: This is MCP ... - GitHub](https://github.com/wonderwhy-er/DesktopCommanderMCP)
6. [Desktop Commander (MCP) for Claude – The "Cost-Capped ...](https://www.reddit.com/r/ClaudeAI/comments/1kcpzmd/desktop_commander_mcp_for_claude_the_costcapped/)
7. [Desktop Commander MCP 서버 (모듈식 FastMCP 구현) - LobeHub](https://lobehub.com/ko/mcp/mcp-mirror-nexus-digital-automations_mcp-filesystem-updated?activeTab=deployment)
8. [mcp/desktop-commander - Docker Image](https://hub.docker.com/r/mcp/desktop-commander)

## Related Questions

- Explore example commands for file and process management
- Learn security best practices when using Desktop Commander MCP
- Discover how to customize MCP server settings on each OS
- Find troubleshooting tips for installation and updates
- Compare Desktop Commander MCP with other MCP tools
