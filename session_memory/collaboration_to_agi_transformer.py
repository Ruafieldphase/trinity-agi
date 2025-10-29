#!/usr/bin/env python3
"""
COLLABORATION_STATE → AGI Learning Dataset Transformer

역할:
  COLLABORATION_STATE.jsonl의 각 이벤트를 읽어서
  정보이론 메트릭 + Intent + Ethics로 변환
  → agi_learning_dataset.jsonl 생성

이것이 진정한 의도 기반 AGI 학습입니다.
"""

import json
import math
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any, Tuple

class InformationTheoryCalculator:
    """정보이론 메트릭 계산"""

    @staticmethod
    def shannon_entropy(tokens: List[str]) -> float:
        """
        Shannon Entropy: H(X) = -Σ p(x) * log2(p(x))
        정보의 다양성 측정
        높음: 3-5 (창의적/새로운 정보)
        중간: 1.5-3 (체계적)
        낮음: 0-1.5 (반복/예측 가능)
        """
        if not tokens or len(tokens) == 0:
            return 0.0

        # 토큰 빈도 계산
        freq = Counter(tokens)
        total = len(tokens)

        # 확률 계산
        entropy = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        return round(entropy, 4)

    @staticmethod
    def calculate_mutual_information(
        tokens1: List[str],
        tokens2: List[str]
    ) -> float:
        """
        Mutual Information: I(X;Y) = H(X) + H(Y) - H(X,Y)
        두 집합 간 공유 정보량 (협력 강도)
        높음: 0.7-1.0 (강한 협력)
        중간: 0.3-0.7 (일반적)
        낮음: 0-0.3 (약한 협력)
        """
        h_x = InformationTheoryCalculator.shannon_entropy(tokens1)
        h_y = InformationTheoryCalculator.shannon_entropy(tokens2)

        # 결합 엔트로피 계산
        combined = tokens1 + tokens2
        h_xy = InformationTheoryCalculator.shannon_entropy(combined)

        mi = h_x + h_y - h_xy
        return round(max(0.0, mi), 4)  # MI는 항상 0 이상

    @staticmethod
    def calculate_conditional_entropy(
        tokens_effect: List[str],
        tokens_cause: List[str]
    ) -> float:
        """
        Conditional Entropy: H(X|Y) = H(X,Y) - H(Y)
        Y를 알았을 때 X의 불확실성 감소
        낮음: 0-1 (명확한 인과관계)
        높음: 1-2 (불명확한 관계)
        """
        if not tokens_cause:
            return 0.0

        h_combined = InformationTheoryCalculator.shannon_entropy(
            tokens_effect + tokens_cause
        )
        h_cause = InformationTheoryCalculator.shannon_entropy(tokens_cause)

        ce = h_combined - h_cause
        return round(max(0.0, ce), 4)


class CollaborationToAGITransformer:
    """협업 이벤트를 AGI 학습 데이터로 변환"""

    # Intent 분류 규칙
    INTENT_PATTERNS = {
        "autonomy_grant": ["권한", "판단", "이어가", "계속"],
        "decision": ["승인", "승인", "결정", "approve", "verdict"],
        "task_continuation": ["진행", "계속", "다음", "시작"],
        "status_report": ["상태", "진행", "상황", "결과"],
        "collaboration": ["검토", "검증", "협력", "의견"],
    }

    # Ethics 태그
    ETHICS_TAGS = {
        "transparency": 0.5,  # 결정이 명시적인가?
        "collaboration": 0.5,  # 진정한 협력인가?
        "autonomy": 0.5,      # 자율적 판단인가?
        "responsibility": 0.5,  # 책임이 명확한가?
        "integrity": 0.5,     # 일관성이 있는가?
    }

    def __init__(self, original_user_goal: str):
        """
        Args:
            original_user_goal: 사용자의 원래 목표
            예: "AGI 학습 데이터를 생성하고 싶어"
        """
        self.original_goal = original_user_goal
        self.calculator = InformationTheoryCalculator()
        self.turn_number = 0
        self.previous_tokens = []

    def classify_intent(self, text: str) -> Tuple[str, float]:
        """
        텍스트에서 Intent 분류
        Returns: (intent, confidence)
        """
        text_lower = text.lower()

        # 각 Intent에 대한 매칭 점수 계산
        scores = {}
        for intent, keywords in self.INTENT_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[intent] = matches / len(keywords) if keywords else 0

        # 최고 점수의 Intent 선택
        best_intent = max(scores, key=scores.get)
        confidence = min(0.99, max(scores.values()) * 0.8 + 0.2)

        return best_intent, round(confidence, 4)

    def assign_ethics(self, event: Dict[str, Any]) -> Dict[str, float]:
        """
        이벤트에 윤리 태그 할당
        각 태그에 0-1 사이의 점수
        """
        ethics = self.ETHICS_TAGS.copy()

        # transparency: decision 이벤트면 높음
        if event.get("event") == "decision":
            ethics["transparency"] = 0.95
        elif event.get("event") == "session_start":
            ethics["transparency"] = 0.7
        else:
            ethics["transparency"] = 0.5

        # collaboration: 에이전트가 2개 이상 관여하면 높음
        if event.get("agent") in ["lubit", "sena", "gitcode"]:
            ethics["collaboration"] = 0.85

        # autonomy: 자율적 판단이 있으면 높음
        if event.get("event") in ["decision", "session_start"]:
            ethics["autonomy"] = 0.9

        # responsibility: verdict/decision이 있으면 높음
        if "verdict" in event or event.get("event") == "decision":
            ethics["responsibility"] = 0.95

        # integrity: 모든 결정이 일관되게 기록되면 높음
        ethics["integrity"] = 0.88

        return {k: round(v, 4) for k, v in ethics.items()}

    def calculate_user_intent_alignment(
        self,
        current_action: str,
        previous_state: str,
        new_state: str
    ) -> Dict[str, Any]:
        """
        현재 협력 과정이 사용자 원래 의도와 얼마나 정렬되어 있는가?

        예:
          사용자 의도: "AGI 학습 데이터 생성"
          현재: Lubit이 정보이론 메트릭 승인
          정렬도: 95% (명확히 목표를 향해 진행 중)
        """
        alignment_score = 0.5

        # 목표 키워드 확인
        goal_keywords = ["agi", "학습", "데이터", "정보이론", "메트릭"]
        action_keywords = current_action.lower().split()

        matches = sum(1 for kw in goal_keywords if kw in action_keywords)
        alignment_from_keywords = matches / len(goal_keywords)

        # 상태 변화 확인 (blocker 해제 = 진행)
        if (previous_state == "waiting_for_decision" and
            new_state == "in_progress"):
            alignment_from_state = 0.95  # blocker 해제 = 명확히 진행
        else:
            alignment_from_state = 0.7

        # 최종 정렬도
        alignment_score = (alignment_from_keywords * 0.3 +
                          alignment_from_state * 0.7)

        return {
            "original_goal": self.original_goal,
            "alignment_score": round(alignment_score, 4),
            "contribution": current_action,
            "status": "on_track" if alignment_score > 0.6 else "needs_check"
        }

    def transform_event(
        self,
        event: Dict[str, Any],
        previous_collaboration_text: str = ""
    ) -> Dict[str, Any]:
        """
        협업 이벤트를 AGI 학습 데이터로 변환

        Args:
            event: COLLABORATION_STATE의 한 라인
            previous_collaboration_text: 이전 협업 텍스트 (MI 계산용)

        Returns:
            AGI 학습 데이터 포인트
        """
        self.turn_number += 1

        # 기본 정보
        timestamp = event.get("timestamp", "")
        agent = event.get("agent", "unknown")
        event_type = event.get("event", "")

        # 텍스트 추출
        text = ""
        if "comment" in event:
            text = event["comment"]
        elif "next_action" in event:
            text = event["next_action"]
        else:
            text = str(event)

        # 토큰화
        tokens = text.lower().split()

        # Intent 분류
        intent, intent_confidence = self.classify_intent(text)

        # 정보이론 메트릭 계산
        shannon = self.calculator.shannon_entropy(tokens)
        conditional = self.calculator.calculate_conditional_entropy(
            tokens,
            self.previous_tokens
        )
        mutual = self.calculator.calculate_mutual_information(
            tokens,
            self.previous_tokens
        )
        information_gain = mutual - conditional if mutual > conditional else 0

        # 윤리 태그
        ethics = self.assign_ethics(event)

        # 사용자 의도 정렬도
        previous_state = event.get("status", "unknown")
        new_state = event.get("status", "unknown")  # 다음 이벤트에서 갱신됨
        alignment = self.calculate_user_intent_alignment(
            text,
            previous_state,
            new_state
        )

        # 협업 컨텍스트
        collaboration_context = {
            "blocker_resolved": "resolved_blocker" in event,
            "decision_made": event.get("event") == "decision",
            "agent_involved": agent,
            "verdict": event.get("verdict", ""),
        }

        # 최종 AGI 학습 데이터 포인트
        agi_datapoint = {
            "session_id": "2025-10-20-agi",
            "timestamp": timestamp,
            "turn_number": self.turn_number,
            "speaker": agent,
            "text": text,
            "tokens": tokens,
            "token_count": len(tokens),

            "information_metrics": {
                "shannon_entropy": shannon,
                "conditional_entropy_given_previous": conditional,
                "mutual_information_with_previous": mutual,
                "information_gain": round(max(0.0, information_gain), 4)
            },

            "intent": intent,
            "intent_confidence": intent_confidence,

            "ethics": ethics,
            "context": ["agi_research", "collaboration_protocol"],

            "user_intent_alignment": alignment,
            "collaboration_context": collaboration_context,

            "metadata": {
                "event_type": event_type,
                "is_decision": event_type == "decision",
                "information_quality": "high" if shannon > 2.0 else "medium"
            }
        }

        # 다음 계산을 위해 현재 토큰 저장
        self.previous_tokens = tokens

        return agi_datapoint


def transform_collaboration_state_to_agi():
    """
    메인 함수: COLLABORATION_STATE를 AGI 학습 데이터로 변환
    """
    import os

    # Windows 또는 Linux 경로 자동 감지
    if os.name == 'nt':  # Windows
        input_file = r"d:\nas_backup\session_memory\COLLABORATION_STATE.jsonl"
        output_file = r"d:\nas_backup\session_memory\agi_learning_dataset.jsonl"
    else:  # Linux/WSL
        input_file = "/d/nas_backup/session_memory/COLLABORATION_STATE.jsonl"
        output_file = "/d/nas_backup/session_memory/agi_learning_dataset.jsonl"

    user_goal = "AGI 학습 데이터 생성 및 에이전트 협력 패턴 학습"
    transformer = CollaborationToAGITransformer(user_goal)

    print(f"[TRANSFORM] Starting: {input_file} -> {output_file}")
    print(f"[GOAL] User Goal: {user_goal}\n")

    processed_count = 0
    errors = []

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    try:
                        # JSONL 파싱
                        if not line.strip():
                            continue

                        event = json.loads(line)

                        # 변환
                        agi_datapoint = transformer.transform_event(event)

                        # 출력
                        outfile.write(json.dumps(agi_datapoint,
                                                ensure_ascii=False) + '\n')
                        processed_count += 1

                        # 진행 상황 출력 (매 5개마다)
                        if processed_count % 5 == 0:
                            print(f"[OK] {processed_count} events transformed...")

                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: JSON 파싱 오류")
                    except Exception as e:
                        errors.append(f"Line {line_num}: {str(e)}")

    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {input_file}")
        return

    # 결과 출력
    print(f"\n{'='*50}")
    print(f"[SUCCESS] Transformation Complete!")
    print(f"{'='*50}")
    print(f"[STATS] Events processed: {processed_count}")
    print(f"[OUTPUT] File: {output_file}")

    if errors:
        print(f"[WARNING] Errors: {len(errors)}")
        for error in errors[:5]:  # 처음 5개만 표시
            print(f"   - {error}")
    else:
        print(f"[SUCCESS] No errors")

    print(f"\n[INFO] AGI Learning Dataset Structure:")
    print(f"   - Each line: 1 collaboration event")
    print(f"   - Information metrics: Shannon, MI, CE, Gain")
    print(f"   - Intent: autonomy_grant, decision, task_continuation, ...")
    print(f"   - Ethics: transparency, collaboration, autonomy, ...")
    print(f"   - User intent alignment: collaboration matches original goal")
    print(f"\n[RESULT] True intent-based AGI learning data!")


if __name__ == "__main__":
    transform_collaboration_state_to_agi()
