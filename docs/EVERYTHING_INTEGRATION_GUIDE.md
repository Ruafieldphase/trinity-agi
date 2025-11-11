# Everything 검색 통합 가이드

## 현재 상태 ✅

- **Everything 실행 중**: ✅ `C:\Program Files\Everything\Everything.exe`
- **HTTP 서버**: ✅ 포트 8080에서 활성화
- **CLI 도구 (es.exe)**: ✅ `c:\workspace\agi\scripts\es.exe`

## 빠른 시작

### 1. 워크스페이스를 Everything 인덱스에 추가 (필수)

Everything이 현재 `c:\workspace\agi`를 인덱싱하지 않고 있습니다. 다음 단계를 따라주세요:

```powershell
# 자동으로 Everything 옵션 창 열기
.\scripts\everything_setup.ps1 -AddWorkspaceToIndex -WorkspaceFolder "c:\workspace\agi"
```

**수동 설정**:

1. Everything 실행
2. `도구 (Tools)` → `옵션 (Options)` → `인덱스 (Indexes)` → `폴더 (Folders)`
3. `추가... (Add...)` 클릭
4. `c:\workspace\agi` 경로 선택
5. `확인` 클릭하여 저장

⏱️ 인덱싱은 보통 몇 초 내에 완료됩니다.

### 2. 검색 사용하기

#### CLI 직접 사용

```powershell
# 기본 검색
.\scripts\es.exe -n 20 "hippocampus"

# 특정 확장자만
.\scripts\es.exe -n 20 "ext:py resonance"

# 특정 경로에서만
.\scripts\es.exe -n 20 "path:""c:\workspace\agi"" copilot"
```

#### 편리한 래퍼 스크립트

```powershell
# 기본 검색
.\scripts\everything_quick_search.ps1 "hippocampus"

# Python 파일만 검색
.\scripts\everything_quick_search.ps1 "resonance" -Extension py -MaxResults 10

# 특정 폴더에서만
.\scripts\everything_quick_search.ps1 "pipeline" -Path "c:\workspace\agi\scripts"

# 첫 번째 결과 자동 열기
.\scripts\everything_quick_search.ps1 "hippocampus.py" -OpenFirst

# JSON 출력 (다른 도구와 연동)
.\scripts\everything_quick_search.ps1 "config" -JsonOutput
```

#### HTTP API 사용

```powershell
# REST API로 검색 (다른 언어/도구에서 사용 가능)
$query = [System.Web.HttpUtility]::UrlEncode("hippocampus")
Invoke-RestMethod "http://localhost:8080/?search=$query&count=10&json=1"
```

## VS Code 통합

### Task 사용 (추가 예정)

```
Ctrl+Shift+P → Tasks: Run Task → Everything: Quick Search
```

### Keybinding (추가 예정)

```
Ctrl+Alt+F → Everything 검색 열기
```

## 활용 아이디어

### 1. **빠른 파일 찾기**

기존 `grep_search`나 `file_search`보다 훨씬 빠릅니다.

```powershell
# 기존 방식 (느림)
Get-ChildItem -Recurse -Filter "*hippocampus*"

# Everything 방식 (초고속)
.\scripts\everything_quick_search.ps1 "hippocampus"
```

### 2. **원본 데이터 인덱스 고속화**

현재 `build_original_data_index.ps1`를 Everything 기반으로 교체 가능.

### 3. **Hippocampus 메모리 검색 강화**

해마 시스템이 과거 컨텍스트를 검색할 때 Everything 활용.

### 4. **실시간 파이프라인 분석**

로그, 결과 파일을 빠르게 찾아서 분석 체인에 투입.

### 5. **자동화된 워크플로우**

```powershell
# 최근 24시간 내 생성된 결과 파일 모두 찾기
.\scripts\es.exe "path:""c:\workspace\agi\outputs"" dm:today"

# YouTube 분석 결과만 필터링
.\scripts\everything_quick_search.ps1 "youtube_learner" -Path "c:\workspace\agi\outputs" -Extension json
```

## 유용한 Everything 쿼리 패턴

### 시간 기반 검색

```
dm:today           # 오늘 수정된 파일
dm:yesterday       # 어제 수정된 파일
dm:lastweek        # 지난주 수정된 파일
dc:thismonth       # 이번 달 생성된 파일
```

### 크기 기반 검색

```
size:>1mb          # 1MB 이상 파일
size:<100kb        # 100KB 미만 파일
empty:             # 빈 파일/폴더
```

### 확장자 검색

```
ext:py;js;ts       # 여러 확장자 동시 검색
!ext:md            # Markdown 제외
```

### 경로 검색

```
path:"outputs"     # outputs 폴더 내
parent:"scripts"   # scripts 폴더의 직계 자식만
```

### 복합 검색

```
ext:py resonance dm:lastweek size:>10kb
# 지난주 수정된, 10KB 이상, resonance 포함, Python 파일
```

## 문제 해결

### Everything이 워크스페이스를 찾지 못함

```powershell
# 상태 확인
.\scripts\everything_setup.ps1 -CheckStatus

# 인덱스 재구축 (Everything 메뉴)
# Index → Rebuild
```

### HTTP 서버 오류

Everything 옵션에서 HTTP 서버가 활성화되어 있는지 확인:

- `Tools` → `Options` → `HTTP Server` → `Enable HTTP Server` 체크

### CLI 명령이 작동하지 않음

```powershell
# CLI 재다운로드
.\scripts\everything_setup.ps1 -DownloadCLI
```

## 고급 통합 계획

### Phase 1: 기본 통합 ✅ (완료)

- [x] Everything 설치 확인
- [x] CLI 다운로드 및 설치
- [x] 기본 검색 스크립트

### Phase 2: 워크플로우 통합 (진행 중)

- [ ] VS Code Task 추가
- [ ] 키보드 단축키 설정
- [ ] 원본 데이터 인덱스 교체

### Phase 3: AI 통합 (예정)

- [ ] Hippocampus 검색 엔진으로 통합
- [ ] 자동 컨텍스트 검색 (Copilot 요청 시 자동)
- [ ] 실시간 파이프라인 모니터링 강화

## 참고 자료

- **Everything 공식 사이트**: <https://www.voidtools.com/>
- **CLI 문서**: <https://www.voidtools.com/support/everything/command_line_interface/>
- **HTTP API**: <https://www.voidtools.com/support/everything/http/>
- **검색 문법**: <https://www.voidtools.com/support/everything/searching/>

## 다음 단계

1. **워크스페이스 인덱스 추가** (위 1번 참조)
2. **검색 테스트**: `.\scripts\everything_quick_search.ps1 "hippocampus"`
3. **VS Code Task 추가** (선택사항)
4. **자동화 적용** (Hippocampus, 실시간 파이프라인 등)

---

💡 **Tip**: Everything은 NTFS 저널을 사용하여 실시간으로 파일 변경을 추적합니다. 한 번 인덱싱하면 이후 검색은 거의 즉시 수행됩니다!
