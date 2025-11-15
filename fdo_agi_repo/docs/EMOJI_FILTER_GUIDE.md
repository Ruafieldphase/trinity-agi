# Emoji Filter Guide

## 개요

Windows PowerShell 콘솔에서 이모지로 인한 인코딩 오류를 방지하기 위한 필터입니다.

## 사용법

### 1. 직접 사용

```python
from fdo_agi_repo.utils.emoji_filter import strip_emojis

text = "Hello 👋 World 🌍"
clean_text = strip_emojis(text)
# 결과: "Hello  World "
```

### 2. LLM 출력에 적용 (예정)

Claude/GPT 등의 LLM 응답에 자동 적용:

```python
from fdo_agi_repo.orchestrator.llm_client import LLMClient
from fdo_agi_repo.utils.emoji_filter import strip_emojis

client = LLMClient(provider="anthropic", model="claude-3-5-sonnet")
response = client.generate(system_prompt, user_prompt)

# 자동 필터링 (LLMClient 내부에서 처리 예정)
clean_response = strip_emojis(response)
```

### 3. 설정으로 제어 (예정)

환경 변수:
```bash
# 활성화 (기본값)
export CLAUDE_EMOJI_FILTER_ENABLED=true

# 비활성화
export CLAUDE_EMOJI_FILTER_ENABLED=false
```

또는 `config/resonance.json`:
```json
{
  "claude_emoji_filter": {
    "enabled": true,
    "description": "Remove emojis from Claude outputs (PowerShell console compatibility)"
  }
}
```

## 기술 세부사항

### 필터링되는 이모지 타입

1. **기본 이모지**: 😀, 🎉, 👍 등
2. **스킨톤 변형**: 👋🏻, 👍🏿 등
3. **복합 이모지**: 👨‍👩‍👧‍👦 (Zero Width Joiner 포함)
4. **플래그**: 🇰🇷, 🇺🇸 등
5. **Emoji Variation Selector**: ❤️ (U+FE0F 포함)

### Unicode 범위

- `\U0001F300-\U0001F9FF`: 기타 기호, 그림문자
- `\U0001FA00-\U0001FAFF`: 확장 그림문자-A
- `\U00002600-\U000027BF`: 기타 기호
- `\U0001F1E0-\U0001F1FF`: 지역 표시 기호 (국기)
- 기타 보조 플레인 이모지

### 성능

- **시간 복잡도**: O(n), n = 문자열 길이
- **공간 복잡도**: O(n) (새 문자열 생성)
- **벤치마크**: 10KB 텍스트 < 1ms

## 테스트

```bash
# 단위 테스트
pytest tests/test_emoji_filter.py -v

# 커버리지
pytest tests/test_emoji_filter.py --cov=fdo_agi_repo.utils.emoji_filter
```

테스트 케이스:
- ✅ 기본 이모지 제거
- ✅ 한글/영어/공백 유지
- ✅ 스킨톤 변형 제거
- ✅ 복합 이모지 제거
- ✅ 플래그 제거
- ✅ 빈 문자열/None 처리
- ✅ 특수문자 유지

## 제한사항

1. **일부 특수문자 오탐지 가능**: ™️, ©️ 등은 제거됨
2. **ZWJ 시퀀스**: 일부 복합 이모지는 잔여 문자가 남을 수 있음
3. **유니코드 버전**: Python 빌드의 Unicode 데이터베이스에 의존

## 향후 개선

1. [ ] Claude Anthropic 클라이언트에 통합
2. [ ] 설정 파일 기반 활성화/비활성화
3. [ ] 선택적 이모지 허용 리스트
4. [ ] 로그 레벨별 필터 제어

## 관련 문서

- PowerShell UTF-8 설정: `scripts/fix_font_encoding.ps1`
- LLM 클라이언트: `fdo_agi_repo/orchestrator/llm_client.py`
- 테스트: `tests/test_emoji_filter.py`
