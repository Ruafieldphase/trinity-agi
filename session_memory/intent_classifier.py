#!/usr/bin/env python3
"""
Intent Classifier for AGI Learning Data

대화에서 사용자/에이전트의 Intent를 자동으로 분류합니다.

Intent 종류:
  1. autonomy_grant: 사용자가 에이전트에 자율권 부여
  2. task_continuation: 작업 계속 진행
  3. decision: 기술적 의사결정
  4. status_report: 상태 보고
  5. collaboration: 협력/피드백
  6. information_request: 정보 요청
  7. clarification: 명확히 하기
  8. error_handling: 오류 처리
  9. planning: 계획 수립
  10. acknowledgment: 인정/동의

Sena의 판단으로 구현됨 (2025-10-20)
"""

from typing import Dict, List, Tuple, Set
from collections import Counter


class IntentClassifier:
    """Intent 자동 분류기"""

    # Intent별 키워드 (가중치 포함)
    INTENT_KEYWORDS = {
        "autonomy_grant": {
            "keywords": [
                "decision", "autonomy", "judge", "proceed", "continue",
                "handle", "manage", "discretion", "yourself", "grant", "let"
            ],
            "weight": 1.0
        },
        "task_continuation": {
            "keywords": [
                "continue", "proceed", "next", "start", "resume", "restart",
                "next_step", "final", "complete", "finish", "remaining", "todo"
            ],
            "weight": 0.9
        },
        "decision": {
            "keywords": [
                "approve", "approved", "decision", "judge", "choose", "method",
                "how", "what", "decided", "decide", "set", "determined"
            ],
            "weight": 0.95
        },
        "status_report": {
            "keywords": [
                "status", "progress", "situation", "result", "complete", "done",
                "report", "update", "current", "finished", "completed", "finished"
            ],
            "weight": 0.85
        },
        "collaboration": {
            "keywords": [
                "review", "validate", "check", "feedback", "opinion", "suggest",
                "together", "cooperate", "help", "support", "verify", "examine"
            ],
            "weight": 0.9
        },
        "information_request": {
            "keywords": [
                "what", "why", "how", "when", "where", "who", "which",
                "ask", "explain", "tell", "describe", "info", "information"
            ],
            "weight": 0.8
        },
        "clarification": {
            "keywords": [
                "clarify", "understand", "explain", "detail", "precise", "again",
                "again", "correct", "check", "verify", "accurate", "precise"
            ],
            "weight": 0.85
        },
        "error_handling": {
            "keywords": [
                "error", "problem", "issue", "fail", "failure", "cant", "unable",
                "bug", "wrong", "incorrect", "fix", "correct", "resolve"
            ],
            "weight": 0.92
        },
        "planning": {
            "keywords": [
                "plan", "schedule", "prepare", "design", "architecture", "structure",
                "strategy", "timeline", "goal", "objective", "direction", "outline"
            ],
            "weight": 0.88
        },
        "acknowledgment": {
            "keywords": [
                "understand", "yes", "ok", "okay", "good", "agree", "correct",
                "agree", "understand", "got", "acknowledge", "affirm", "confirm"
            ],
            "weight": 0.8
        }
    }

    # 부정 키워드 (점수 감소)
    NEGATION_KEYWORDS = [
        "not", "no", "dont", "wont", "cannot", "cant", "unable",
        "ignore", "skip", "exclude", "remove", "delete", "unnecessary"
    ]

    # 강조 키워드 (점수 증가)
    EMPHASIS_KEYWORDS = [
        "must", "should", "very", "really", "definitely", "certainly",
        "obviously", "clearly", "important", "urgent", "critical", "essential"
    ]

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """텍스트를 토큰화"""
        return text.lower().split()

    @staticmethod
    def calculate_intent_scores(
        tokens: List[str]
    ) -> Dict[str, float]:
        """
        토큰 리스트에 대해 각 Intent의 점수 계산

        Args:
            tokens: 토큰 리스트

        Returns:
            Intent별 점수 딕셔너리
        """
        scores = {}

        for intent, info in IntentClassifier.INTENT_KEYWORDS.items():
            keywords = info["keywords"]
            weight = info["weight"]

            # 기본 점수 계산
            matches = sum(1 for token in tokens if token in keywords)
            score = matches * weight

            # 부정 키워드 확인
            negations = sum(1 for token in tokens if token in IntentClassifier.NEGATION_KEYWORDS)
            score *= max(0.5, 1 - negations * 0.1)  # 부정이 있으면 감소

            # 강조 키워드 확인
            emphasis = sum(1 for token in tokens if token in IntentClassifier.EMPHASIS_KEYWORDS)
            score *= (1 + emphasis * 0.1)  # 강조가 있으면 증가

            scores[intent] = round(score, 4)

        return scores

    @staticmethod
    def classify(text: str) -> Tuple[str, float]:
        """
        텍스트의 Intent를 분류

        Args:
            text: 분류할 텍스트

        Returns:
            (intent, confidence) 튜플
        """
        if not text or len(text.strip()) == 0:
            return ("unknown", 0.0)

        tokens = IntentClassifier.tokenize(text)
        scores = IntentClassifier.calculate_intent_scores(tokens)

        # 최고 점수 선택
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        # Confidence 계산
        # 점수가 높거나 토큰이 많으면 높은 confidence
        token_factor = min(1.0, len(tokens) / 20)  # 토큰이 20개일 때 1.0
        confidence = min(0.99, best_score * 0.3 + token_factor * 0.7)

        # 점수가 너무 낮으면 unknown
        if best_score == 0 or confidence < 0.3:
            return ("unknown", 0.0)

        return (best_intent, round(confidence, 4))

    @staticmethod
    def classify_batch(texts: List[str]) -> List[Tuple[str, float]]:
        """
        여러 텍스트를 한 번에 분류

        Args:
            texts: 텍스트 리스트

        Returns:
            (intent, confidence) 튜플 리스트
        """
        return [IntentClassifier.classify(text) for text in texts]

    @staticmethod
    def get_intent_description(intent: str) -> str:
        """Intent의 설명 제공"""
        descriptions = {
            "autonomy_grant": "사용자가 에이전트에 자율권 부여",
            "task_continuation": "이전 작업을 계속 진행",
            "decision": "기술적 의사결정 및 판단",
            "status_report": "진행 상황 및 결과 보고",
            "collaboration": "피드백, 검증, 협력 요청",
            "information_request": "정보 조회 및 설명 요청",
            "clarification": "명확히 하기 및 재확인",
            "error_handling": "오류 처리 및 문제 해결",
            "planning": "계획 수립 및 설계",
            "acknowledgment": "동의, 인정, 이해",
            "unknown": "의도를 분류할 수 없음"
        }
        return descriptions.get(intent, "알 수 없는 의도")


def demo():
    """데모: Intent 분류"""
    print("="*70)
    print("Intent Classifier - Demo")
    print("="*70)

    test_cases = [
        # autonomy_grant
        "Continue with your discretion and judgment",
        # task_continuation
        "Please continue implementing the information theory metrics",
        # decision
        "I approve the metrics design",
        # status_report
        "Parsing of 61,129 messages is completed",
        # collaboration
        "Can we review this part together?",
        # information_request
        "What exactly is AGI learning data?",
        # clarification
        "Can you explain this more clearly?",
        # error_handling
        "An error occurred during parsing",
        # planning
        "Let me design the architecture for the next step",
        # acknowledgment
        "Understood. I will proceed.",
    ]

    print("\n[TEST CASES]\n")

    for i, text in enumerate(test_cases, 1):
        intent, confidence = IntentClassifier.classify(text)
        description = IntentClassifier.get_intent_description(intent)

        print(f"{i}. Text: {text}")
        print(f"   Intent: {intent}")
        print(f"   Confidence: {confidence}")
        print(f"   Description: {description}\n")

    print("="*70)
    print("[SUCCESS] Intent Classifier Ready!")
    print("="*70)


if __name__ == "__main__":
    demo()
