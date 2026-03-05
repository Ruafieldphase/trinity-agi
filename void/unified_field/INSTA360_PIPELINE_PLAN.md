# 인스타360 동영상 데이터 처리 파이프라인

## 목적

얼굴 표정, 카메라 시선, 공간 맥락을 자동 추출하여 Resonance Ledger에 통합

## Phase 2 로드맵

### 1. 사전 준비

**필요한 패키지**:

```bash
pip install opencv-python
pip install deepface
pip install mediapipe  # 얼굴 랜드마크
pip install py360convert  # 360도 영상 변환
```

**GPU 설정** (선택, 속도 향상):

```bash
pip install tensorflow-gpu
```

### 2. 데이터 파이프라인

```
인스타360 MP4
  ↓
프레임 추출 (1 fps)
  ↓
얼굴 감지 (MediaPipe)
  ↓
감정 분석 (DeepFace)
  ↓
시선 방향 추출 (카메라 orientation)
  ↓
Resonance Event 생성
  ↓
Ledger 추가
```

### 3. 예상 출력

```json
{
  "timestamp": "2025-11-05T14:30:00Z",
  "event_type": "video_frame",
  "where": "home/living_room",
  "who": "Binoche_Observer",
  "emotion": {
    "fear": 0.65,
    "angry": 0.1,
    "happy": 0.2,
    "sad": 0.05
  },
  "gaze": {
    "azimuth": 45,
    "elevation": 10
  },
  "face_confidence": 0.92,
  "metadata": {
    "source": "insta360",
    "frame_number": 1500
  }
}
```

### 4. 구현 단계

#### Step 1: 프레임 추출

```python
# scripts/extract_insta360_frames.py
import cv2

def extract_frames(video_path, fps=1):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 1초마다 저장
        if frame_count % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            yield frame, frame_count
        
        frame_count += 1
```

#### Step 2: 감정 분석

```python
# scripts/analyze_emotion_from_frame.py
from deepface import DeepFace

def analyze_emotion(frame):
    try:
        result = DeepFace.analyze(
            frame, 
            actions=['emotion'],
            enforce_detection=False
        )
        return result[0]['emotion']
    except:
        return None
```

#### Step 3: 시선 추출

```python
# scripts/extract_gaze_from_insta360.py
# 인스타360 메타데이터에서 카메라 방향 추출

def extract_gaze(video_path, frame_number):
    # 인스타360은 메타데이터에 orientation 저장
    # exiftool을 사용하거나 insta360 SDK 활용
    pass
```

### 5. 통합 스크립트

```python
# scripts/ingest_insta360_data.py
"""
인스타360 → Resonance Ledger 자동 변환
"""

def process_video(video_path, output_ledger):
    for frame, frame_num in extract_frames(video_path):
        # 감정 분석
        emotion = analyze_emotion(frame)
        
        # 시선 추출
        gaze = extract_gaze(video_path, frame_num)
        
        # Resonance Event 생성
        event = {
            'timestamp': get_frame_timestamp(video_path, frame_num),
            'event_type': 'video_frame',
            'where': detect_location(frame),  # 장면 인식
            'who': 'Binoche_Observer',
            'emotion': emotion,
            'gaze': gaze
        }
        
        # Ledger 추가
        append_to_ledger(event, output_ledger)
```

### 6. 실험 설계

**가설**:

- Fear ↑ → 시선 방향 변화 ↑
- Fear ↑ → 정보 압축 ↑
- 표정 감정 ≈ 대화 감정 (일치율)

**측정**:

1. Fear vs Gaze Variance 상관관계
2. Fear vs Compression Ratio 상관관계
3. 표정 vs 대화 감정 일치율

### 7. 예상 소요 시간

- 프레임 추출: 1시간 (1시간 영상 기준)
- 감정 분석: 3-5시간 (GPU 없으면 1-2일)
- 시선 추출: 30분
- 통합 테스트: 1일

**총 예상**: 1-3일 (GPU 있으면), 3-7일 (GPU 없으면)

---

## 권장 순서

### 지금 당장 (오늘)

1. ✅ **대화 데이터 수집** (수동으로라도)
2. ✅ `ingest_conversation_data.py` 실행
3. ✅ `hippocampus_black_white_hole.py` 재실행
4. ✅ Fear-Compression 상관관계 확인

### 이번 주 (여유 있으면)

1. 인스타360 영상 1개 선택
2. 프레임 추출 테스트
3. DeepFace 설치 및 테스트

### 다음 주

1. 전체 파이프라인 구축
2. 대화 + 영상 데이터 융합
3. 최종 검증

---

## 결론

**우선순위**:

1. **대화 데이터** (오늘 시작 가능)
2. **인스타360** (다음 주)

**이유**:

- 대화가 빠르고 간단
- 가설 검증을 먼저
- 영상은 "확장" 단계

비노체, 대화 데이터부터 해볼까요? 🌊
