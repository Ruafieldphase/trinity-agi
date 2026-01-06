"""
Failure Loop Detector
감지: 같은 오류가 3회 반복되면 자동으로 Ask-First Protocol 발동
"""
import json
from datetime import datetime
from pathlib import Path

class FailureLoopDetector:
    def __init__(self, state_file="outputs/failure_loop_state.json"):
        self.state_file = Path(state_file)
        self.attempts = self._load_state()
        self.threshold = 3  # 3회 반복 시 차단

    def _load_state(self):
        """이전 실패 기록 로드"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except:
                return {}
        return {}

    def _save_state(self):
        """실패 기록 저장"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.attempts, indent=2, ensure_ascii=False), encoding='utf-8')

    def record_failure(self, error_signature, context=None):
        """
        실패 기록 및 Ask-First 판단

        Args:
            error_signature: 오류 식별자 (예: "API_KEY_INVALID", "VERTEX_AI_403")
            context: 추가 맥락 정보

        Returns:
            dict: {"action": "ASK_USER" | "CONTINUE", "count": int, "message": str}
        """
        if error_signature not in self.attempts:
            self.attempts[error_signature] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": None,
                "contexts": []
            }

        self.attempts[error_signature]["count"] += 1
        self.attempts[error_signature]["last_seen"] = datetime.now().isoformat()

        if context:
            self.attempts[error_signature]["contexts"].append({
                "timestamp": datetime.now().isoformat(),
                "detail": str(context)
            })

        count = self.attempts[error_signature]["count"]

        self._save_state()

        if count >= self.threshold:
            return {
                "action": "ASK_USER",  # Gate 2 HOLD 발동
                "count": count,
                "message": f"⚠️ 같은 오류({error_signature})가 {count}회 반복되었습니다. 비노체님께 확인이 필요합니다.",
                "gate": "HOLD",
                "reason": f"반복 실패 감지: {error_signature}"
            }

        return {
            "action": "CONTINUE",
            "count": count,
            "message": f"실패 {count}회 기록됨. {self.threshold - count}회 더 반복되면 Ask-First 발동."
        }

    def reset_failure(self, error_signature):
        """성공 시 해당 오류 카운터 리셋"""
        if error_signature in self.attempts:
            del self.attempts[error_signature]
            self._save_state()

    def get_status(self):
        """현재 실패 상태 요약"""
        critical = {k: v for k, v in self.attempts.items() if v["count"] >= self.threshold}
        warning = {k: v for k, v in self.attempts.items() if v["count"] >= 2 and v["count"] < self.threshold}

        return {
            "critical_failures": critical,  # 즉시 Ask 필요
            "warning_failures": warning,    # 주의 필요
            "total_tracked": len(self.attempts)
        }


# 전역 인스턴스 (싱글톤)
_detector = None

def get_failure_detector():
    global _detector
    if _detector is None:
        _detector = FailureLoopDetector()
    return _detector
