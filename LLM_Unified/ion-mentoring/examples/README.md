# 파동키 변환 시스템 데모

## 📖 개요

이 디렉토리는 `ResonanceConverter` 클래스의 실제 작동을 시연하는 예제 스크립트를 포함합니다.

## 🚀 실행 방법

### 기본 실행 (오프라인 모드)

```powershell
cd ion-mentoring/examples
python resonance_demo.py
```

오프라인 모드에서는 로컬 키워드 기반 분석만 수행됩니다.

### Vertex AI 통합 실행 (온라인 모드)

환경 변수를 설정한 후 실행:

```powershell
# PowerShell에서
cd ion-mentoring/tools
./load_env.ps1 -Path ..\..\..\.env

# 데모 실행
cd ..\examples
python resonance_demo.py
```

온라인 모드에서는 Vertex AI Gemini를 활용한 고급 감정 톤 분석이 수행됩니다.

## 🎯 데모 구성

### 1. 오프라인 모드 데모

5가지 사전 정의된 입력 샘플을 처리하여 다음을 출력합니다:

- 리듬 패턴 (속도감, 문장 길이, 문장부호 밀도)
- 감정 톤 (주요 감정, 신뢰도)
- 생성된 파동키

### 2. 온라인 모드 데모 (선택사항)

Vertex AI가 설정된 경우:

- 고급 감정 분석
- 더 정확한 감정 분류
- JSON 형식 응답 파싱

### 3. 대화형 모드

사용자가 직접 텍스트를 입력하여 실시간으로 파동키 변환을 체험할 수 있습니다.

종료: `quit`, `exit`, `종료` 입력 또는 Ctrl+C

## 📊 출력 예시

```text
[1] 입력: "이 코드가 왜 안 돌아가는 거야?! 답답해!"
   📏 리듬: fast
      - 평균 문장 길이: 3.5 단어
      - 문장부호 밀도: 12.50%
      - 질문 비율: 0.5
      - 느낌표 비율: 1.0
   🎭 감정: curious
      - 신뢰도: 70.00%
   🎯 파동키: curious-burst-inquiry
```

## 🔧 트러블슈팅

### ImportError 발생 시

모듈 경로 문제일 수 있습니다. 다음을 확인하세요:

- `ion-mentoring/examples/` 디렉토리에서 실행 중인지
- `resonance_converter.py`와 `prompt_client.py`가 상위 디렉토리에 존재하는지

### Vertex AI 연결 실패 시

1. 환경 변수 확인:

   ```powershell
   $env:GOOGLE_CLOUD_PROJECT
   $env:GOOGLE_APPLICATION_CREDENTIALS
   ```

2. `.env` 파일이 올바르게 구성되었는지 확인

3. 오프라인 모드로 자동 폴백되므로 데모는 계속 진행됩니다

## 📚 관련 문서

- [DAY3_RESONANCE_IMPLEMENTATION.md](../DAY3_RESONANCE_IMPLEMENTATION.md) - 구현 가이드
- [resonance_converter.py](../resonance_converter.py) - 소스 코드
- [test_resonance_converter.py](../tests/test_resonance_converter.py) - 테스트 코드

---

**작성일**: 2025-10-17  
**버전**: 1.0  
**상태**: ✅ 실행 준비 완료
