# REAPER Automation Bridge

이 문서는 Gitko/Core/AGI 파이프라인에 REAPER 기반 오디오 렌더 단계를 편입하기 위한 최소 구성 요소를 정리한 것입니다. 목표는 기존 PowerShell 자동화 루틴(scripts/*.ps1)과 동일한 패턴으로 음성/사운드 산출물을 생성·검증·배포할 수 있도록 하는 것입니다.

## 구성 개요

1. **템플릿 프로젝트**  
   - 모든 .RPP 템플릿은 udio_templates/ 폴더에서 관리하며, 세부 원칙은 udio_templates/README.md에 기록했습니다.  
   - 현재 Gitko_Agent_Default.RPP는 빠른 쉘프 테스트를 위한 자리표시자입니다. 실무에서는 REAPER에서 제작한 실제 템플릿으로 교체한 뒤 config/reaper_automation.json의 템플릿 맵과 연결하세요.  

2. **렌더 스크립트 (scripts/render_reaper_project.ps1)**  
   - REAPER 실행 파일, 템플릿 키(-TemplateKey) 또는 직접 경로(-ProjectPath), 출력 이름을 입력받아 
eaper.exe -renderproject를 호출합니다.  
   - -DryRun 스위치를 제공하므로, REAPER가 설치되지 않은 환경에서도 경로/설정 검증과 산출물 폴더 구조를 미리 확인할 수 있습니다.  
   - 실행 결과는 
ender.log, 
ender-error.log, metadata.json으로 남아 CI 로그나 대시보드에서 재활용할 수 있습니다.  

3. **설정 파일 (config/reaper_automation.json)**  
   - 전역 경로(reaper_path, output_root, render_extension) 외에 	emplates 맵을 도입했습니다.  
   - 예: 	emplates.gitko_default.path = audio_templates/Gitko_Agent_Default.RPP, 	emplates.gitko_default.output_subdir = gitko_agent. 작업 유형별로 다른 출력 폴더/확장자를 지정할 수 있습니다.  

4. **파이프라인 연동**  
   - 기존 스케줄러 스크립트(예: scripts/register_*_task.ps1)에서 렌더 스크립트를 호출하면 특정 이벤트나 CI 단계에 자동 삽입할 수 있습니다.  
   - 렌더 결과(metadata/logs)는 outputs/ 하위 JSON/로그 파일로 남기고, 모니터링/알림 스택에 전달하도록 설계합니다.  

## 실행 준비
1. **REAPER 설치**  
   - Windows 기본 경로 C:\Program Files\REAPER (x64)\reaper.exe를 사용하며, 다른 경로일 경우 config의 
eaper_path 또는 -ReaperPath 파라미터로 지정합니다.  
   - CLI 호출이 가능하도록 
eaper.exe가 PATH 또는 절대경로로 접근 가능해야 합니다.  

2. **ReaPack 플러그인** (선택)  
   - PowerShell에서 ReaScript를 배포할 계획이 있다면 ReaPack 저장소 등록을 권장합니다.  
   - 내부 Git 저장소를 ReaPack 포맷으로 내보내면 스크립트 배포/버전 관리를 수월하게 할 수 있습니다.  

3. **템플릿 배치**  
   - udio_templates/ 폴더에 버전 관리된 템플릿을 넣거나, 별도의 공유 경로를 config에 기술합니다.  
   - 템플릿에는 믹스 구조(버스/이펙트/아웃풋 셋업)만 남기고, 렌더 경로나 파일명은 자동화가 덮어쓰게 둡니다.  

## 실행 흐름

1. PowerShell에서 렌더 스크립트를 호출합니다.  
   `powershell
   pwsh scripts/render_reaper_project.ps1 
     -TemplateKey "gitko_default" 
     -OutputName "session_20250115" 
     -ConfigPath "config/reaper_automation.json" 
     -DryRun
   `
2. 스크립트는 설정 파일을 병합해 REAPER 실행 경로, 출력 루트, 템플릿별 서브폴더·확장자를 확정합니다.  
3. 세션 폴더(outputs/audio/gitko_agent/<세션명>/)를 생성하고 템플릿을 복사한 뒤, RENDER_FILE 항목을 실제 산출물 경로로 덮어씁니다.  
4. 렌더가 성공하면 오디오 파일과 metadata.json, 
ender.log가 같은 폴더에 기록되어 추후 파이프라인에서 참조할 수 있습니다.  

## 템플릿 및 드라이런 체크리스트
- 	emplates 맵을 활용하면 Task/프로젝트별로 서로 다른 템플릿, 출력 확장자, 서브디렉터리를 구성할 수 있습니다.  
- -ProjectPath와 -TemplateKey는 상호 배타적으로 사용하며, CLI 호출 시 우선순위는 ProjectPath → TemplateKey → config.template_path입니다.  
- -DryRun 사용 시에는 빈 오디오 파일과 로그가 생성되어 경로만 검증하고, metadata.json의 dry_run: true 플래그로 식별할 수 있습니다.  
- 모든 실행 결과는 metadata.json에 	emplate_key, 
ender_success, log_stdout, log_stderr 필드로 정리되므로 외부 모듈에서 상태를 파싱하기 쉽습니다.  

## 향후 확장 포인트
- **템플릿 맵 확장**: Config에 다중 템플릿을 등록한 뒤 Task별 키만 전달하면 다른 오디오 자산을 순차 렌더링할 수 있습니다.  
- **ReaScript 호출**: 렌더 이전/이후에 ReaScript를 실행해 트랙 활성화, 마커 정리, loudness 노멀라이즈 등을 자동화할 수 있습니다.  
- **CI 통합**: GitHub Actions, Windows Scheduler 등에 본 스크립트를 연결해 빌드-렌더-배포 단일 파이프라인을 구성합니다.  
- **QA 자동화**: 렌더 출력에 대해 FFmpeg/sox 등을 호출해 RMS, LUFS, Peak 등 품질 지표를 측정하고 모니터링 스택에 송신합니다.  

---

본 문서는 REAPER 연동의 기본 가드레일을 제공하므로, 구체적인 템플릿/스크립트 내용은 프로젝트 요구사항에 맞춰 확장하면 됩니다.
