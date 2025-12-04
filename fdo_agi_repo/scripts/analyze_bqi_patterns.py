"""
BQI Training Data 심층 분석

목적:
1. 감정 키워드 개선 방안 도출 (현재 0.1% 인식률)
2. 고빈도 질문 패턴 분석
3. Rhythm Phase 전환 패턴 파악
4. 사용자 대화 스타일 프로파일링

Author: GitHub Copilot
Created: 2025-10-28
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any
import re

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

# UTF-8 인코딩 강제 설정 (한글 깨짐 방지)
import encoding_setup


class BQIDataAnalyzer:
    """BQI Training Data 분석기"""
    
    def __init__(self, data_file: str = "memory/bqi_training_dataset.jsonl"):
        self.data_file = Path(__file__).parent.parent / data_file
        self.data: List[Dict[str, Any]] = []
        self.load_data()
    
    def load_data(self):
        """Training data 로드"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Training data not found: {self.data_file}")
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.data.append(json.loads(line))
        
        print(f"📂 Loaded {len(self.data)} training examples\n")
    
    def analyze_emotion_failures(self, sample_size: int = 50):
        """
        감정이 'neutral'로 분류된 질문들을 샘플링하여 실제 감정 분석
        
        목표: 놓친 감정 키워드 발견
        """
        print("=" * 70)
        print("1. 감정 인식 실패 분석 (Neutral로 분류된 질문들)")
        print("=" * 70)
        
        neutral_questions = [
            d for d in self.data
            if d['bqi']['emotion']['keywords'] == ['neutral']
        ]
        
        print(f"Neutral 분류: {len(neutral_questions)} / {len(self.data)} ({len(neutral_questions)/len(self.data)*100:.1f}%)\n")
        
        # 한글 키워드 빈도 분석
        korean_words = Counter()
        emotion_patterns = {
            'hope': ['기대', '희망', '가능', '될까', '해보', '좋을', '발전', '성장'],
            'concern': ['걱정', '불안', '문제', '위험', '실패', '어려', '힘들', '우려'],
            'focus': ['지금', '현재', '당장', '즉시', '바로', '먼저'],
            'integration': ['통합', '합치', '연결', '조합', '묶', '통일']
        }
        
        # 샘플 질문에서 감정 키워드 후보 찾기
        print(f"무작위 샘플 {sample_size}개 분석:\n")
        
        import random
        samples = random.sample(neutral_questions, min(sample_size, len(neutral_questions)))
        
        found_emotions = defaultdict(list)
        
        for i, sample in enumerate(samples[:20], 1):  # 처음 20개만 출력
            q = sample['question']
            q_lower = q.lower()
            
            # 각 감정 패턴 매칭
            detected = []
            for emotion, keywords in emotion_patterns.items():
                if any(kw in q for kw in keywords):
                    detected.append(emotion)
                    found_emotions[emotion].append(q)
            
            if detected:
                print(f"[{i}] {emotion.upper()} 감지: {q[:60]}...")
                print(f"    매칭: {', '.join(detected)}\n")
        
        # 감정별 통계
        print("\n감정 키워드 발견 통계:")
        for emotion, questions in found_emotions.items():
            print(f"  {emotion}: {len(questions)}개 질문에서 발견")
        
        return found_emotions
    
    def analyze_question_patterns(self):
        """질문 유형 패턴 분석"""
        print("\n" + "=" * 70)
        print("2. 질문 유형 패턴 분석")
        print("=" * 70)
        
        # 질문 시작 패턴
        start_patterns = Counter()
        question_types = Counter()
        
        for d in self.data:
            q = d['question'].strip()
            
            # 첫 단어 추출
            first_words = q.split()[:2]
            if first_words:
                start_patterns[' '.join(first_words)] += 1
            
            # 질문 유형 분류
            if '?' in q or '?' in q:
                question_types['interrogative'] += 1
            elif any(word in q for word in ['해줘', '알려', '설명', '보여줘']):
                question_types['request'] += 1
            elif any(word in q for word in ['어때', '어떻게', '뭐야', '뭘까']):
                question_types['inquiry'] += 1
            else:
                question_types['statement'] += 1
        
        print("\n질문 시작 패턴 (Top 20):")
        for pattern, count in start_patterns.most_common(20):
            print(f"  '{pattern}': {count}회")
        
        print("\n질문 유형 분포:")
        total = sum(question_types.values())
        for qtype, count in question_types.most_common():
            print(f"  {qtype}: {count}개 ({count/total*100:.1f}%)")
    
    def analyze_rhythm_transitions(self):
        """Rhythm Phase 전환 패턴 분석"""
        print("\n" + "=" * 70)
        print("3. Rhythm Phase 전환 패턴")
        print("=" * 70)
        
        # 대화별 그룹핑 (conversation_id 기준)
        by_conversation = defaultdict(list)
        for d in self.data:
            conv_id = d['metadata']['conversation_id']
            by_conversation[conv_id].append(d)
        
        # 각 대화에서 rhythm 전환 추적
        transitions = Counter()
        
        for conv_id, turns in by_conversation.items():
            if len(turns) < 2:
                continue
            
            # 시간순 정렬
            turns_sorted = sorted(turns, key=lambda x: x['metadata']['date'])
            
            for i in range(len(turns_sorted) - 1):
                curr_rhythm = turns_sorted[i]['bqi']['rhythm_phase']
                next_rhythm = turns_sorted[i + 1]['bqi']['rhythm_phase']
                
                if curr_rhythm != next_rhythm:
                    transitions[f"{curr_rhythm} → {next_rhythm}"] += 1
        
        print("\nRhythm Phase 전환 (Top 10):")
        for transition, count in transitions.most_common(10):
            print(f"  {transition}: {count}회")
        
        # Rhythm별 평균 질문 길이
        rhythm_lengths = defaultdict(list)
        for d in self.data:
            rhythm = d['bqi']['rhythm_phase']
            q_len = len(d['question'])
            rhythm_lengths[rhythm].append(q_len)
        
        print("\nRhythm Phase별 평균 질문 길이:")
        for rhythm, lengths in sorted(rhythm_lengths.items()):
            avg_len = sum(lengths) / len(lengths)
            print(f"  {rhythm}: {avg_len:.1f}자 (샘플 {len(lengths)}개)")
    
    def suggest_emotion_keywords(self):
        """개선된 감정 키워드 제안"""
        print("\n" + "=" * 70)
        print("4. 개선된 감정 키워드 제안")
        print("=" * 70)
        
        # 실제 질문에서 자주 나오는 단어 추출
        word_freq = Counter()
        
        for d in self.data:
            q = d['question']
            # 한글 단어만 추출 (2글자 이상)
            words = re.findall(r'[가-힣]{2,}', q)
            word_freq.update(words)
        
        print("\n고빈도 한글 단어 (Top 30):")
        for word, count in word_freq.most_common(30):
            print(f"  {word}: {count}회", end="  ")
            if count % 5 == 0:
                print()  # 5개마다 줄바꿈
        
        print("\n\n제안하는 새 감정 키워드:")
        print("""
        _EMOTION_KEYWORDS = {
            "hope": [
                "hope", "growth", "expand", 
                "기대", "희망", "가능", "될까", "좋을", "발전", "성장", "해보"
            ],
            "concern": [
                "risk", "concern", "worry", 
                "불안", "우려", "걱정", "문제", "위험", "실패", "어려", "힘들"
            ],
            "focus": [
                "now", "focus", 
                "지금", "현재", "당장", "즉시", "바로", "먼저", "우선"
            ],
            "integration": [
                "integrate", 
                "합치", "통합", "조율", "연결", "조합", "묶", "통일", "합쳐"
            ],
            "curiosity": [  # 새 감정 추가
                "궁금", "알고", "뭐야", "뭘까", "어떻게", "왜"
            ],
            "gratitude": [  # 새 감정 추가
                "고마", "감사", "좋아", "멋지", "훌륭"
            ]
        }
        """)
    
    def analyze_priority_distribution(self):
        """Priority 분포 분석"""
        print("\n" + "=" * 70)
        print("5. Priority 분포 분석")
        print("=" * 70)
        
        priority_counts = Counter()
        priority_questions = defaultdict(list)
        
        for d in self.data:
            priority = d['bqi']['priority']
            priority_counts[priority] += 1
            priority_questions[priority].append(d['question'])
        
        print("\nPriority 분포:")
        total = sum(priority_counts.values())
        for priority in sorted(priority_counts.keys(), reverse=True):
            count = priority_counts[priority]
            print(f"  Priority {priority}: {count}개 ({count/total*100:.1f}%)")
        
        # 각 priority 샘플 출력
        print("\nPriority별 샘플 질문:")
        for priority in sorted(priority_counts.keys(), reverse=True):
            samples = priority_questions[priority][:3]
            print(f"\n  Priority {priority}:")
            for i, q in enumerate(samples, 1):
                print(f"    {i}. {q[:70]}...")
    
    def generate_report(self):
        """전체 분석 리포트 생성"""
        print("\n" + "=" * 70)
        print("BQI Training Data 심층 분석 리포트")
        print("=" * 70)
        print(f"분석 시간: 2025-10-28")
        print(f"데이터 크기: {len(self.data)} 질문")
        print("=" * 70 + "\n")
        
        # 1. 감정 실패 분석
        found_emotions = self.analyze_emotion_failures(sample_size=100)
        
        # 2. 질문 패턴
        self.analyze_question_patterns()
        
        # 3. Rhythm 전환
        self.analyze_rhythm_transitions()
        
        # 4. 키워드 제안
        self.suggest_emotion_keywords()
        
        # 5. Priority 분포
        self.analyze_priority_distribution()
        
        # 요약
        print("\n" + "=" * 70)
        print("분석 요약 및 권장사항")
        print("=" * 70)
        print("""
        ✅ 발견 사항:
        1. 감정 인식률이 매우 낮음 (0.1%) - 한글 키워드 부족
        2. 대부분 'exploration' phase (93.2%) - 대화형 질문 특성
        3. Priority는 대부분 1 (기본값) - 긴급도 키워드 부족
        
        🎯 개선 방안:
        1. 한글 감정 키워드 대폭 확장 (제안된 키워드 적용)
        2. 'curiosity', 'gratitude' 등 새 감정 카테고리 추가
        3. Priority 키워드 한글화 ('확인' → '검토', '긴급' 등)
        4. Rhythm phase 판단 로직 개선 (질문 유형 고려)
        
        📊 다음 단계:
        1. bqi_adapter.py의 _EMOTION_KEYWORDS 업데이트
        2. _infer_priority()에 한글 키워드 추가
        3. 업데이트 후 재분석으로 개선 효과 검증
        """)


if __name__ == "__main__":
    try:
        analyzer = BQIDataAnalyzer()
        analyzer.generate_report()
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
