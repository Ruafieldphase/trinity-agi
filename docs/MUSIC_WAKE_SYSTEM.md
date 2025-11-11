# 🎵 음악 기반 각성 & 적응형 재생 시스템

**생성**: 2025-11-10  
**업데이트**: 2025-11-10 (Adaptive Music Player 추가)  
**목적**: 음악을 활용한 자연스러운 휴식→활동 페이즈 전환 + 상황 맞춤 음악 자동 재생

---

## 🆕 새로운 기능: Adaptive Music Player

### 💡 핵심 아이디어

시스템이 **상황에 맞는 음악을 자동으로 선택하고 재생**합니다:

- **각성이 필요할 때** → 높은 에너지, 빠른 템포 (120-140 BPM)
- **집중이 필요할 때** → Lo-fi, 클래식 (60-90 BPM)
- **코딩 흐름** → Synthwave, 전자음악 (100-130 BPM)
- **휴식 전환** → 자연음, Ambient (40-60 BPM)

### 🎯 사용법

```powershell
# 자동 선택 (시간대 + 리듬 페이즈 기반)
.\scripts\play_adaptive_music.ps1

# 특정 카테고리 지정
.\scripts\play_adaptive_music.ps1 -Category wake_up
.\scripts\play_adaptive_music.ps1 -Category coding
.\scripts\play_adaptive_music.ps1 -Category rest

# Python 직접 실행
python scripts/adaptive_music_player.py
python scripts/adaptive_music_player.py --category focus
```

### 📚 음악 카테고리

1. **wake_up** (각성)
   - BPM: 120-140
   - Energy: HIGH
   - 용도: 아침 각성, 활동 시작

2. **focus** (집중)
   - BPM: 60-90
   - Energy: LOW
   - 용도: 깊은 집중 작업, 학습

3. **coding** (코딩 흐름)
   - BPM: 100-130
   - Energy: MEDIUM
   - 용도: 개발, 문제 해결

4. **rest** (휴식)
   - BPM: 40-60
   - Energy: VERY_LOW
   - 용도: Glymphatic 배수, 회복

5. **transition** (전환)
   - BPM: 70-100
   - Energy: LOW
   - 용도: 페이즈 전환, 준비

### 🤖 자동 선택 로직

```
시간대 기반 추론:
  06:00-09:00 → wake_up
  09:00-12:00 → coding
  12:00-14:00 → focus (점심 후 집중)
  14:00-18:00 → coding
  18:00-22:00 → transition
  22:00-06:00 → rest

리듬 페이즈 우선:
  REST 페이즈 → rest 카테고리
  ACTIVE 페이즈 → 시간대 기반
```

### 📊 학습 데이터 수집

모든 재생 기록이 `outputs/music_playback_history.jsonl`에 저장되어  
BQI 학습에 활용됩니다:

```json
{
  "category": "coding",
  "name": "코딩 (Coding Flow)",
  "description": "전자음악, Synthwave - 코딩 흐름",
  "url": "https://www.youtube.com/watch?v=...",
  "timestamp": "2025-11-10T09:15:00"
}
```

---

## 🧠 왜 음악이 각성에 도움이 되는가?

### 신경과학적 근거

1. **청각 자극 → RAS 활성화**
   - Reticular Activating System (망상활성계)
   - 각성 상태 조절의 핵심 구조
   - 음악의 리듬이 RAS를 직접 자극

2. **도파민 분비**
   - 음악 청취 → 보상 회로 활성화
   - 측좌핵(nucleus accumbens) 반응
   - 자연스러운 동기부여 증가

3. **기저핵 동조화**
   - 외부 리듬 → 내부 리듬 entrainment
   - 운동 준비 상태 촉진
   - 행동 개시 역치 감소

4. **전두엽 재활성화**
   - 음악의 구조적 복잡성 → 주의력 자동 회복
   - Default Mode Network 해제
   - Executive Network 점진적 활성화

---

## 🎯 시스템 설계

### Phase 1: Detection

```
음악 재생 감지 (detect_audio_playback.ps1)
  ↓
프로세스 모니터링:
  - Spotify, Chrome, VLC, etc.
  - CPU/메모리 활성도 확인
```

### Phase 2: Grace Period (15초)

```
음악 시작 감지
  ↓
15초 대기 (Glymphatic 배수 완료)
  ↓
뇌척수액 순환 마무리
```

### Phase 3: Wake Trigger

```
각성 신호 전송
  ↓
rhythm_wake_signal.json 생성
  ↓
자율 목표 시스템 활성화 준비
```

### Phase 4: Smooth Transition

```
REST → ACTIVE 페이즈 전환
  ↓
Goal Executor 자동 실행 (선택적)
  ↓
자연스러운 작업 재개
```

---

## 📊 구현 상태

### ✅ 완료

- [x] 음악 감지 스크립트 (`detect_audio_playback.ps1`)
- [x] 각성 프로토콜 (`music_wake_protocol.py`)
- [x] Glymphatic grace period (15초)
- [x] 리듬 신호 생성

### 🔄 진행 중

- [ ] Observer Telemetry 통합
- [ ] 자동 트리거 (백그라운드 모니터링)
- [ ] Reaper Music Analyzer 연동 (템포/에너지 분석)

### 📋 계획

- [ ] 음악 장르별 각성 효과 학습
- [ ] 개인화된 최적 음악 추천
- [ ] 페이즈 전환 성공률 트래킹

---

## 🎼 사용법

### 수동 실행

```powershell
# 음악 재생 상태 확인
powershell -File scripts/detect_audio_playback.ps1

# 각성 프로토콜 실행
python scripts/music_wake_protocol.py
```

### 자동 모니터링 (TODO)

```powershell
# Observer Telemetry에 통합 예정
# 5초마다 자동 감지 + 조건 충족 시 자동 트리거
```

---

## 🧪 현재 감지 가능한 음악 플레이어

- Spotify
- Chrome (YouTube, 웹 플레이어)
- Edge, Firefox
- VLC, Windows Media Player
- iTunes, foobar2000, AIMP
- OBS (스트리밍 중 음악)

**확장 가능**: 프로세스 이름만 추가하면 됨

---

## 💡 개인화 권장사항

1. **템포 선호도 학습**
   - 각성에 효과적인 BPM 범위 파악
   - 120-140 BPM: 일반적으로 활력 증가
   - 개인차 존재 (BQI 학습 대상)

2. **장르별 효과**
   - 전자음악: 빠른 각성
   - 클래식: 점진적 각성
   - Lo-fi: 부드러운 전환

3. **시간대별 전략**
   - 오전: 밝은 음악
   - 오후: 에너지 부스팅
   - 저녁: 마무리 집중

---

## 🔗 관련 시스템

- **Adaptive Rhythm System**: 페이즈 전환 감지
- **Glymphatic CLI**: 휴식 품질 보장
- **Autonomous Goal System**: 각성 후 자동 작업 재개
- **BQI Learner**: 음악-각성 패턴 학습

---

**다음 단계**: Observer Telemetry 통합 → 자동화된 음악 기반 각성
