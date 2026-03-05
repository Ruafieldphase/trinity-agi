# Original Data Integration

## 개요

`C:\workspace\original_data` 폴더의 파일들을 인덱싱하고 API를 통해 접근할 수 있는 시스템.

## 구성 요소

### 1. 인덱스 시스템

- **위치**: `C:\workspace\original_data`
- **인덱스 파일**: `outputs/original_data_index.json`
- **인덱스 빌더**: `scripts/build_original_data_index.ps1`, `scripts/build_original_data_index.py`

### 2. API 서버

- **포트**: 8093
- **서버 스크립트**: `scripts/original_data_server.py`
- **엔드포인트**:
  - `/health` - 헬스 체크
  - `/search?q=<query>&ext=<ext>&tags=<tags>&since_days=<days>&top=<count>` - 검색

### 3. 검색 유틸리티

- **쿼리 스크립트**: `scripts/query_original_data.py`
- **라이브러리**: `scripts/original_data_index.py`

## 통합 지점

### Unified Dashboard (`scripts/quick_status.ps1`)

**섹션**: `[1.5] Original Data API (Port 8093)`

**체크 항목**:

- ✅ API 헬스 (레이턴시 측정)
  - 경고: 500ms
  - 알림: 1000ms
- ✅ 인덱스 신선도
  - 녹색: ≤ 1일
  - 노란색: 1-3일
  - 빨간색: > 3일
- ✅ 인덱스된 파일 수

### Morning Kickoff (`scripts/morning_kickoff.ps1`)

**스텝**: `[4.5/7] Checking Original Data index...`

**동작**:

- 인덱스 신선도 체크
- 3일 이상 오래된 경우 자동 재생성
- 인덱스 없으면 자동 생성

## VS Code 작업 (Tasks)

### 인덱스 관리

```json
"Original Data: Build Index (open)"
"Original Data: Build Index (no open)"
"Original Data: Open Index (MD)"
"Original Data: Open Index (JSON)"
```

### API 서버

```json
"Original Data: Start API (8093)"
"Original Data: API Health"
```

### 검색

```json
"Original Data: Quick Search (AGI, 14d, md)"
```

## 사용 예시

### 1. 인덱스 빌드

```powershell
.\scripts\build_original_data_index.ps1 -OpenMd
```

### 2. API 서버 시작

```powershell
python .\scripts\original_data_server.py --port 8093
```

### 3. 검색

```powershell
python .\scripts\query_original_data.py --query "AGI" --ext md --since-days 14 --top 20
```

### 4. API를 통한 검색

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8093/search?q=AGI&ext=md&since_days=14&top=20'
```

## 자동화

### Morning Kickoff에 포함됨

- ✅ 매일 아침 인덱스 신선도 자동 체크
- ✅ 필요시 자동 재생성

### Unified Dashboard에 포함됨

- ✅ API 상태 실시간 모니터링
- ✅ 인덱스 신선도 표시

## 성능 특성

### 인덱스 크기

- **현재**: ~7.5MB (10,000 파일)
- **빌드 시간**: 약 1-2분 (파일 수에 따라)

### API 응답 시간

- **헬스 체크**: < 100ms (정상)
- **검색**: < 500ms (정상), 복잡한 쿼리는 더 오래 걸릴 수 있음

## 향후 개선 사항

### 단기

- [ ] API 서버 자동 시작 (auto-resume에 추가)
- [ ] 인덱스 증분 업데이트 (전체 재생성 대신)
- [ ] 검색 결과 캐싱

### 중기

- [ ] 벡터 검색 지원 (시맨틱 검색)
- [ ] 실시간 파일 감지 및 자동 인덱싱
- [ ] API 인증 및 rate limiting

### 장기

- [ ] 분산 인덱싱 (대용량 데이터)
- [ ] ML 기반 관련성 순위
- [ ] 통합 대시보드에 검색 UI

## 트러블슈팅

### API 오프라인

**증상**: `원격 서버에 연결할 수 없습니다.`

**해결**:

```powershell
# API 서버 시작
python .\scripts\original_data_server.py --port 8093
```

### 인덱스 오래됨

**증상**: Dashboard에서 빨간색 표시

**해결**:

```powershell
# 수동 재생성
.\scripts\build_original_data_index.ps1 -NoOpen

# 또는 Morning Kickoff 실행 (자동 재생성)
.\scripts\morning_kickoff.ps1 -Hours 1
```

### 검색 결과 없음

**확인 사항**:

1. 인덱스가 최신인가?
2. 검색 조건이 올바른가? (`--ext`, `--since-days` 등)
3. `C:\workspace\original_data` 폴더에 파일이 있는가?

## 관련 문서

- `docs/AGI_UNIVERSAL_ROADMAP.md` - 전체 시스템 로드맵
- `outputs/original_data_index.md` - 인덱스 요약 (자동 생성)
- `scripts/build_original_data_index.ps1` - 인덱스 빌더 소스

---
**작성일**: 2025-11-04  
**마지막 업데이트**: 2025-11-04  
**상태**: ✅ 통합 완료 (Dashboard + Morning Kickoff)
