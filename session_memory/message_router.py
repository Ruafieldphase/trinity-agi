#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Router - 에이전트 간 통신의 중앙 허브

역할:
  1. 메시지 라우팅 (Sena → Lubit → GitCode → RUNE)
  2. 메시지 검증 (형식, 필드 확인)
  3. 메시지 로깅 (모든 통신 기록)
  4. 상태 추적 (task 상태 관리)
  5. 오류 처리 (형식 오류, 내용 오류)
  6. 피드백 루프 (재작업 요청)

세나의 판단으로 구현됨 (2025-10-19)
모든 에이전트 통신의 중심
"""

import json
import sys
import io
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
import threading
import queue

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class MessageType(Enum):
    """메시지 타입"""
    ANALYSIS_SUBMISSION = "analysis_submission"          # Sena → Lubit
    VALIDATION_RESULT = "validation_result"              # Lubit → GitCode/Sena
    EXECUTION_RESULT = "execution_result"                # GitCode → RUNE
    FINAL_VERDICT = "final_verdict"                      # RUNE → 모두
    ERROR_REPORT = "error_report"                        # 누구든 → 모두


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"                  # 대기 중
    SENA_ANALYSIS = "sena_analysis"     # Sena 분석 중
    LUBIT_VALIDATION = "lubit_validation"  # Lubit 검증 중
    GITCODE_EXECUTION = "gitcode_execution"  # GitCode 실행 중
    RUNE_VERIFICATION = "rune_verification"  # RUNE 검증 중
    COMPLETED = "completed"              # 완료
    REJECTED = "rejected"                # 거부
    NEEDS_REVISION = "needs_revision"    # 수정 필요


class Message:
    """표준화된 메시지 클래스"""

    def __init__(
        self,
        message_type: MessageType,
        from_agent: str,
        to_agent: str,
        task_id: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message_type = message_type
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.task_id = task_id
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.message_id = f"{task_id}_{message_type.value}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "from": self.from_agent,
            "to": self.to_agent,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "content": self.content,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class MessageValidator:
    """메시지 검증"""

    @staticmethod
    def validate_message(message: Message) -> Tuple[bool, Optional[str]]:
        """메시지 검증"""
        # 필수 필드 확인
        if not message.from_agent:
            return False, "from_agent가 없습니다"
        if not message.to_agent:
            return False, "to_agent가 없습니다"
        if not message.task_id:
            return False, "task_id가 없습니다"
        if not message.content:
            return False, "content가 비어있습니다"

        # 메시지 타입별 검증
        if message.message_type == MessageType.ANALYSIS_SUBMISSION:
            return MessageValidator._validate_analysis(message.content)
        elif message.message_type == MessageType.VALIDATION_RESULT:
            return MessageValidator._validate_validation(message.content)
        elif message.message_type == MessageType.EXECUTION_RESULT:
            return MessageValidator._validate_execution(message.content)
        elif message.message_type == MessageType.FINAL_VERDICT:
            return MessageValidator._validate_verdict(message.content)

        return True, None

    @staticmethod
    def _validate_analysis(content: Dict) -> Tuple[bool, Optional[str]]:
        """분석 메시지 검증"""
        required = ["analysis", "selected_tools", "sub_problems", "confidence"]
        for field in required:
            if field not in content:
                return False, f"분석 메시지에 {field}가 없습니다"

        if not (0.0 <= content["confidence"] <= 1.0):
            return False, "confidence는 0.0 ~ 1.0 사이여야 합니다"

        return True, None

    @staticmethod
    def _validate_validation(content: Dict) -> Tuple[bool, Optional[str]]:
        """검증 메시지 검증"""
        required = ["verdict"]
        for field in required:
            if field not in content:
                return False, f"검증 메시지에 {field}가 없습니다"

        valid_verdicts = ["approved", "needs_revision", "rejected"]
        if content["verdict"] not in valid_verdicts:
            return False, f"verdict는 {valid_verdicts} 중 하나여야 합니다"

        return True, None

    @staticmethod
    def _validate_execution(content: Dict) -> Tuple[bool, Optional[str]]:
        """실행 결과 메시지 검증"""
        required = ["execution_status", "sub_tasks"]
        for field in required:
            if field not in content:
                return False, f"실행 결과 메시지에 {field}가 없습니다"

        if not isinstance(content["sub_tasks"], list):
            return False, "sub_tasks는 리스트여야 합니다"

        return True, None

    @staticmethod
    def _validate_verdict(content: Dict) -> Tuple[bool, Optional[str]]:
        """최종 판정 메시지 검증"""
        required = ["verdict"]
        for field in required:
            if field not in content:
                return False, f"최종 판정 메시지에 {field}가 없습니다"

        valid_verdicts = ["final_approved", "review_needed", "rejected"]
        if content["verdict"] not in valid_verdicts:
            return False, f"verdict는 {valid_verdicts} 중 하나여야 합니다"

        return True, None


class TaskState:
    """작업 상태 추적"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.current_agent = None
        self.history: List[Dict[str, Any]] = []
        self.messages: Dict[str, Message] = {}

    def update_status(self, status: TaskStatus, agent: str, message_id: str):
        """상태 업데이트"""
        self.status = status
        self.current_agent = agent
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status.value,
            "agent": agent,
            "message_id": message_id
        })

    def get_status(self) -> Dict[str, Any]:
        """상태 조회"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "current_agent": self.current_agent,
            "created_at": self.created_at,
            "history": self.history
        }


class MessageRouter:
    """메시지 라우터 - 에이전트 간 통신의 중앙 허브"""

    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.message_queue = queue.Queue()
        self.task_states: Dict[str, TaskState] = {}
        self.messages_log: List[Message] = []
        self.running = False

    def route_message(self, message: Message) -> Tuple[bool, Optional[str]]:
        """메시지 라우팅"""
        # 1. 메시지 검증
        is_valid, error = MessageValidator.validate_message(message)
        if not is_valid:
            self._log_error(message, error)
            return False, error

        # 2. 작업 상태 확인 또는 생성
        if message.task_id not in self.task_states:
            self.task_states[message.task_id] = TaskState(message.task_id)

        task_state = self.task_states[message.task_id]

        # 3. 메시지 타입에 따른 상태 업데이트
        if message.message_type == MessageType.ANALYSIS_SUBMISSION:
            task_state.update_status(TaskStatus.LUBIT_VALIDATION, "lubit", message.message_id)
        elif message.message_type == MessageType.VALIDATION_RESULT:
            verdict = message.content.get("verdict")
            if verdict == "approved":
                task_state.update_status(TaskStatus.GITCODE_EXECUTION, "gitcode", message.message_id)
            elif verdict == "needs_revision":
                task_state.update_status(TaskStatus.SENA_ANALYSIS, "sena", message.message_id)
            elif verdict == "rejected":
                task_state.update_status(TaskStatus.REJECTED, "system", message.message_id)
        elif message.message_type == MessageType.EXECUTION_RESULT:
            task_state.update_status(TaskStatus.RUNE_VERIFICATION, "rune", message.message_id)
        elif message.message_type == MessageType.FINAL_VERDICT:
            verdict = message.content.get("verdict")
            if verdict == "final_approved":
                task_state.update_status(TaskStatus.COMPLETED, "system", message.message_id)
            elif verdict == "rejected":
                task_state.update_status(TaskStatus.REJECTED, "system", message.message_id)
            elif verdict == "review_needed":
                task_state.update_status(TaskStatus.NEEDS_REVISION, "system", message.message_id)

        # 4. 메시지 기록
        self.messages_log.append(message)
        task_state.messages[message.message_id] = message
        self._log_message(message)

        # 5. 큐에 추가
        self.message_queue.put(message)

        print(f"[Router] 메시지 라우팅 성공: {message.message_type.value}")
        print(f"         From: {message.from_agent} → To: {message.to_agent}")
        print(f"         Task: {message.task_id}, Status: {task_state.status.value}")

        return True, None

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if task_id in self.task_states:
            return self.task_states[task_id].get_status()
        return None

    def get_messages_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """작업의 모든 메시지 조회"""
        if task_id in self.task_states:
            return [msg.to_dict() for msg in self.task_states[task_id].messages.values()]
        return []

    def _log_message(self, message: Message):
        """메시지 로깅"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message.to_json() + "\n")

    def _log_error(self, message: Message, error: str):
        """에러 로깅"""
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "type": "validation_error",
            "message_type": message.message_type.value,
            "from": message.from_agent,
            "to": message.to_agent,
            "task_id": message.task_id,
            "error": error
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")

    def print_task_summary(self, task_id: str):
        """작업 요약 출력"""
        state = self.get_task_state(task_id)
        if not state:
            print(f"[Router] 작업을 찾을 수 없습니다: {task_id}")
            return

        print(f"\n{'='*70}")
        print(f"작업 요약: {task_id}")
        print(f"{'='*70}")
        print(f"상태: {state['status']}")
        print(f"현재 에이전트: {state['current_agent']}")
        print(f"생성 시간: {state['created_at']}")

        print(f"\n메시지 흐름:")
        for i, item in enumerate(state['history'], 1):
            print(f"  {i}. [{item['timestamp']}] {item['agent']}: {item['status']}")

        messages = self.get_messages_for_task(task_id)
        print(f"\n메시지 개수: {len(messages)}")

        print(f"{'='*70}\n")


def demo():
    """데모: Message Router"""
    print("="*70)
    print("Message Router Demo - 에이전트 간 통신 중심 허브")
    print("="*70)

    router = MessageRouter(
        log_file=r"d:\nas_backup\session_memory\MESSAGE_LOG.jsonl"
    )

    task_id = "task_demo_001"

    # 1. Sena → Lubit: 분석 제출
    print("\n[Step 1] Sena가 분석을 제출합니다")
    sena_msg = Message(
        message_type=MessageType.ANALYSIS_SUBMISSION,
        from_agent="sena",
        to_agent="lubit",
        task_id=task_id,
        content={
            "analysis": "작업을 분석했습니다",
            "selected_tools": ["tool_1", "tool_2", "tool_3"],
            "sub_problems": ["부분1", "부분2", "부분3"],
            "confidence": 0.92,
            "confidence_reasons": ["도구 선택이 명확", "분해가 합리적"],
            "uncertainties": ["도구 호환성"]
        },
        metadata={"analysis_duration_ms": 1250}
    )
    success, error = router.route_message(sena_msg)
    if not success:
        print(f"   [ERROR] {error}")

    # 2. Lubit → GitCode: 승인
    print("\n[Step 2] Lubit이 분석을 검증하고 승인합니다")
    lubit_msg = Message(
        message_type=MessageType.VALIDATION_RESULT,
        from_agent="lubit",
        to_agent="gitcode",
        task_id=task_id,
        content={
            "sena_analysis_review": "분석이 명확하고 타당합니다",
            "strengths": ["신뢰도 높음", "도구 선택 적절"],
            "risks": [],
            "verdict": "approved",
            "verdict_reason": "위험 요소가 없고 분석이 타당합니다"
        },
        metadata={"validation_duration_ms": 850}
    )
    success, error = router.route_message(lubit_msg)
    if not success:
        print(f"   [ERROR] {error}")

    # 3. GitCode → RUNE: 실행 결과
    print("\n[Step 3] GitCode가 작업을 실행하고 결과를 보고합니다")
    gitcode_msg = Message(
        message_type=MessageType.EXECUTION_RESULT,
        from_agent="gitcode",
        to_agent="rune",
        task_id=task_id,
        content={
            "lubit_approval": "approved",
            "execution_status": "completed",
            "sub_tasks": [
                {
                    "task_id": "subtask_1",
                    "description": "부분 작업 1",
                    "status": "completed",
                    "duration_ms": 2300
                },
                {
                    "task_id": "subtask_2",
                    "description": "부분 작업 2",
                    "status": "completed",
                    "duration_ms": 1500
                },
                {
                    "task_id": "subtask_3",
                    "description": "부분 작업 3",
                    "status": "completed",
                    "duration_ms": 800
                }
            ],
            "integration": {"status": "integrated"},
            "deployment": {"status": "deployed"},
            "summary": {"total_duration_ms": 4600, "final_status": "success"}
        },
        metadata={"transparency_level": "high"}
    )
    success, error = router.route_message(gitcode_msg)
    if not success:
        print(f"   [ERROR] {error}")

    # 4. RUNE → 모두: 최종 판정
    print("\n[Step 4] RUNE이 윤리 검증을 하고 최종 판정을 내립니다")
    rune_msg = Message(
        message_type=MessageType.FINAL_VERDICT,
        from_agent="rune",
        to_agent="all",
        task_id=task_id,
        content={
            "verdict": "final_approved",
            "ethics_evaluation": {
                "transparency": {"score": 0.95},
                "collaboration": {"score": 0.92},
                "autonomy": {"score": 0.90},
                "fairness": {"score": 0.93}
            },
            "ethical_score": 0.925,
            "resonance": 0.93,
            "summary": "작업이 윤리적으로 완벽하게 처리되었습니다",
            "final_status": "task_completed"
        },
        metadata={"verification_duration_ms": 450}
    )
    success, error = router.route_message(rune_msg)
    if not success:
        print(f"   [ERROR] {error}")

    # 5. 작업 요약 출력
    print("\n[Summary] 전체 작업 요약")
    router.print_task_summary(task_id)

    # 6. 메시지 로그 출력
    print("[Logs] 메시지 로그 파일 저장됨:")
    print(f"       {router.log_file}")
    print(f"       총 {len(router.messages_log)}개 메시지 기록됨")

    print("\n" + "="*70)
    print("[SUCCESS] Message Router 데모 완료!")
    print("="*70)


if __name__ == "__main__":
    demo()
