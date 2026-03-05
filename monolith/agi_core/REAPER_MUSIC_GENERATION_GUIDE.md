# 🎼 Reaper 음악 자동 생성 가이드

## 목적

리듬 페이즈에 최적화된 음악을 **직접 생성**하여:

- ✅ 완벽한 BPM/에너지 제어
- ✅ 무한 라이선스 (저작권 자유)
- ✅ 실시간 적응 가능
- ✅ 신경과학 기반 최적화 (RAS 자극)

---

## 🎵 페이즈별 음악 파라미터

### WAKE_UP (각성)

```
BPM: 135
Energy: HIGH
Duration: 3분
Instruments: synth_lead, bass, drums, pad
Frequency: 120-8000Hz (RAS 자극)
Pattern: 4/4_energetic
Key: C major
```

### CODING (코딩 흐름)

```
BPM: 120
Energy: MEDIUM
Duration: 15분
Instruments: synth_arp, bass, light_drums, ambient
Frequency: 80-6000Hz
Pattern: 4/4_steady
Key: A minor
```

### FOCUS (깊은 집중)

```
BPM: 75
Energy: LOW
Duration: 20분
Instruments: piano, strings, ambient, soft_pad
Frequency: 60-4000Hz
Pattern: 3/4_gentle
Key: D minor
```

### REST (휴식/회복)

```
BPM: 50
Energy: VERY LOW
Duration: 10분
Instruments: pad, ambient, nature_sounds
Frequency: 40-2000Hz
Pattern: free_flowing
Key: G major
Purpose: Glymphatic 배수 촉진
```

### TRANSITION (전환)

```
BPM: 90
Energy: LOW
Duration: 5분
Instruments: piano, pad, light_perc
Frequency: 60-5000Hz
Pattern: 4/4_relaxed
Key: F major
```

---

## 🚀 사용법

### 1. 프로젝트 생성

```powershell
# 모든 카테고리 보기
.\scripts\generate_music_simple.ps1 -List

# 특정 카테고리 프로젝트 생성
.\scripts\generate_music_simple.ps1 -Category wake_up

# 생성 후 Reaper에서 자동 열기
.\scripts\generate_music_simple.ps1 -Category coding -Open
```

### 2. Reaper에서 작곡

프로젝트가 열리면:

1. **트랙 추가**
   - `Ctrl+T` 또는 `Track → Insert new track`
   - 각 악기별로 트랙 생성

2. **VST/JS 플러그인 추가**
   - 트랙 FX 버튼 클릭
   - 추천 플러그인:
     - **Synth**: ReaSynth, Surge XT, Vital
     - **Bass**: ReaSynth, Dexed
     - **Drums**: MT Power Drum Kit, ReaDrums
     - **Ambient/Pad**: Dexed, Surge XT
     - **Piano**: Keyzone Classic, Spitfire LABS

3. **MIDI 작곡**
   - 트랙 더블클릭 → MIDI 아이템 생성
   - MIDI 에디터 열기 (`Alt+E`)
   - 노트 입력 (파라미터 참조)

4. **믹싱**
   - 볼륨/팬 조정
   - EQ, Compressor 추가
   - 페이즈 목적에 맞게 조정

### 3. 렌더링

1. `File → Render` (Ctrl+Alt+R)
2. 설정:
   - **Source**: Master mix
   - **Format**: WAV (44.1kHz, 24bit) 또는 MP3
   - **Output**: `outputs/generated_music/`
3. **Render** 클릭

---

## 🎹 추천 무료 플러그인

### Synth

- **Surge XT** - 강력한 웨이브테이블 신스
- **Vital** - 모던 신스 (wave_up/coding용)
- **Dexed** - FM 신스 (ambient/pad)
- **ReaSynth** - Reaper 내장

### Drums

- **MT Power Drum Kit** - 어쿠스틱 드럼
- **DrumMic'a** - 리얼 드럼 샘플
- **ReaDrums** - Reaper 내장

### Piano/Keys

- **Keyzone Classic** - 피아노
- **Spitfire LABS** - 다양한 악기
- **PianoOne** - 무료 그랜드 피아노

### Ambient/Pad

- **TAL-Reverb-4** - 리버브
- **Valhalla SuperMassive** - 거대한 리버브/딜레이
- **Dexed** - FM pad 사운드

---

## 🧠 신경과학 기반 최적화

### RAS (Reticular Activating System) 자극

- **주파수 범위**: 120-8000Hz (wake_up)
- **리듬 패턴**: 빠른 템포 (135 BPM)
- **에너지**: HIGH

### Glymphatic System 지원

- **주파수 범위**: 40-2000Hz (rest)
- **리듬 패턴**: 느린 흐름 (50 BPM)
- **에너지**: VERY LOW
- **목적**: 뇌 노폐물 배출 촉진

### Flow State 유도

- **주파수 범위**: 80-6000Hz (coding/focus)
- **리듬 패턴**: 안정적 4/4 (75-120 BPM)
- **에너지**: MEDIUM/LOW
- **목적**: 몰입 상태 유지

---

## 📁 파일 구조

```
reaper_projects/
├── templates/              # 템플릿 저장
├── wake_up_20251110_143022.rpp
├── wake_up_20251110_143022_render.json
├── wake_up_20251110_143022_metadata.json
└── ...

outputs/
└── generated_music/
    ├── wake_up_20251110_143022.wav
    ├── coding_20251110_144500.wav
    └── ...
```

---

## 🎯 통합 워크플로우

### 1단계: 템플릿 생성 (1회)

```powershell
.\scripts\generate_music_simple.ps1 -Category wake_up -Open
# Reaper에서 작곡 → 템플릿으로 저장
```

### 2단계: 변형 생성 (자동화)

```powershell
# 각 카테고리별 여러 버전 생성
.\scripts\generate_music_simple.ps1 -Category wake_up
.\scripts\generate_music_simple.ps1 -Category coding
.\scripts\generate_music_simple.ps1 -Category focus
```

### 3단계: Adaptive Player 연동

```powershell
# 생성된 음악이 자동으로 선택됨
.\scripts\play_adaptive_music.ps1 -Category wake_up
```

---

## 💡 팁

### 빠른 프로토타입

1. ReaSynth로 기본 트랙 생성
2. MIDI 패턴 간단하게 입력
3. 렌더링 후 테스트
4. BQI 피드백 수집
5. 효과적인 패턴만 정교화

### 템플릿 활용

- 각 카테고리별 "골든 템플릿" 생성
- 템플릿 기반으로 빠른 변형 제작
- `Track → Track template → Save tracks as template`

### 자동화 (향후)

- ReaScript (Lua/Python)로 자동 작곡
- MIDI 패턴 자동 생성
- 파라미터 기반 자동 렌더링

---

## ✅ 체크리스트

- [ ] Reaper 설치 (<https://www.reaper.fm/>)
- [ ] 무료 플러그인 설치
- [ ] wake_up 템플릿 생성
- [ ] coding 템플릿 생성
- [ ] focus 템플릿 생성
- [ ] rest 템플릿 생성
- [ ] transition 템플릿 생성
- [ ] adaptive_music_player와 통합
- [ ] BQI 피드백 수집 시작

---

**생성 완료 후**: `outputs/generated_music/`의 음악을  
`adaptive_music_player.py`가 자동으로 인식하고 재생합니다! 🎶
