# API 버전 관리 및 Backward Compatibility 가이드

## 📋 개요

**목표**: 안정적인 API 진화와 하위 호환성 보장
**전략**: Semantic Versioning + URL 버전 관리
**지원**: v1, v2 동시 운영

---

## 🎯 버전 관리 전략

### Semantic Versioning

```
v1.2.3 (Major.Minor.Patch)
├─ Major: 호환 불가 변경 (v1 → v2)
├─ Minor: 하위 호환 기능 추가 (v1.0 → v1.1)
└─ Patch: 버그 수정 (v1.1.0 → v1.1.1)
```

### URL 구조

```
/api/v1/chat          # v1 (안정)
/api/v2/chat          # v2 (최신)
/api/latest/chat      # 최신 버전 (권장하지 않음)
```

---

## 🛠️ 구현 (3시간)

### Step 1: 라우터 분리

```python
# app/routes/v1.py

from fastapi import APIRouter
from app.schemas import ChatRequestV1, ChatResponseV1

router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

@router_v1.post("/chat", response_model=ChatResponseV1)
async def chat_v1(request: ChatRequestV1):
    """v1 API (레거시)"""
    # 원본 구현
    ...

# app/routes/v2.py

from fastapi import APIRouter
from app.schemas import ChatRequestV2, ChatResponseV2

router_v2 = APIRouter(prefix="/api/v2", tags=["v2"])

@router_v2.post("/chat", response_model=ChatResponseV2)
async def chat_v2(request: ChatRequestV2):
    """v2 API (현재)"""
    # 개선된 구현
    ...

# app/main.py

app.include_router(router_v1)
app.include_router(router_v2)
```

### Step 2: 스키마 버전 관리

```python
# app/schemas.py

# v1 스키마 (레거시)
class ChatRequestV1(BaseModel):
    message: str
    user_id: str

class ChatResponseV1(BaseModel):
    content: str
    persona_used: str

# v2 스키마 (개선됨)
class ChatRequestV2(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    include_reasoning: bool = False  # 새 필드

class ChatResponseV2(BaseModel):
    content: str
    persona_used: str
    reasoning: Optional[Dict] = None  # 새 필드
    confidence: float  # 새 필드
    metadata: Dict  # 새 필드
```

### Step 3: 마이그레이션 가이드

```markdown
# API v1 → v2 마이그레이션 가이드

## 변경 사항

### 추가된 필드
- `session_id`: 세션 추적 (선택사항)
- `include_reasoning`: 라우팅 이유 반환
- `reasoning`: 라우팅 분석 정보
- `confidence`: 신뢰도 점수
- `metadata`: 추가 메타데이터  
  - `rhythm`: 리듬 분석 값 (pace, avg_length 등)
  - `tone`: 감정 톤 분석 값 (primary, confidence 등)
  - `routing`: 2순위 페르소나 및 선택 근거
  - `phase`: Phase Injection 스냅샷 (phase_label, guidance, bqi)
  - `rune`: RUNE 품질 평가 (overall_quality, feedback, transparency)

### 제거된 필드
- 없음 (v1 필드 모두 호환)

### 마이그레이션 단계
1. v1 엔드포인트 호출 코드 검토
2. v2 스키마 대응 확인
3. 필드 매핑 테스트
4. 프로덕션 배포

## 타임라인
- 2024-06-01: v2 출시
- 2024-09-01: v1 Deprecated 공지
- 2024-12-01: v1 지원 종료
```

---

## 📊 버전 관리 플랜

| 시점 | v1 | v2 | v3 |
|------|----|----|-----|
| 2024-01 | GA | - | - |
| 2024-06 | Stable | GA | - |
| 2024-09 | Deprecated | Stable | - |
| 2024-12 | EOL | GA | - |
| 2025-06 | - | Deprecated | GA |

---

## ⏱️ 예상 소요 시간: 3시간
