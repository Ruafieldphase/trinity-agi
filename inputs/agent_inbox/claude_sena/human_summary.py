"""
Human Summary Layer for Self-Compression
압축 결과를 사람이 읽을 수 있는 5~12줄 요약으로 변환

입력: trigger_report_latest.json (또는 history 최근 1회)
출력:
  - outputs/self_compression_human_summary_latest.json
  - outputs/self_compression_human_summary_history.jsonl (append)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class HumanSummary:
    """Human-readable summary of a self-compression cycle"""
    timestamp: str
    trigger_action: str  # self_compress, full_cycle 등
    trigger_origin: str  # lua-auto-policy 등

    # 핵심 요약 (5~12줄)
    sources_seen: List[str]  # 실제로 본 소스 목록 (dummy, file_sampler, log_tail 등)
    tags: Dict[str, Any]  # 키워드/위상 태그
    one_line_wish: str  # "다음에 하고 싶은 것" (단, 실행은 루빛이 결정)

    # 내부 상태 스냅샷
    internal_state: Dict[str, Any]

    # 메타 정보
    compression_count: int
    trigger_reason: Optional[str]


class HumanSummaryGenerator:
    """
    Self-Compression 결과를 인간 친화적 요약으로 변환
    - 비노체는 프로그래밍을 모르므로 "로그 보세요" 같은 내용 금지
    - 구체적이고 직관적인 키워드 중심
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.outputs_dir = workspace / "outputs"
        self.bridge_dir = self.outputs_dir / "bridge"

        self.latest_path = self.outputs_dir / "self_compression_human_summary_latest.json"
        self.history_path = self.outputs_dir / "self_compression_human_summary_history.jsonl"

        # 입력 파일들
        self.trigger_latest = self.bridge_dir / "trigger_report_latest.json"
        self.trigger_history = self.bridge_dir / "trigger_report_history.jsonl"
        self.thought_stream = self.outputs_dir / "thought_stream_latest.json"
        self.internal_state = workspace / "memory" / "agi_internal_state.json"
        self.unconscious = self.outputs_dir / "unconscious_heartbeat.json"
        self.antigravity = self.outputs_dir / "antigravity_intake_latest.json"
        self.media = self.outputs_dir / "media_intake_latest.json"

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """JSON 파일 안전 로드"""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _extract_tags(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터에서 키워드/위상 태그 추출
        - 낮/밤 (시간대)
        - 도시/자연 (공간 위상)
        - 이동/정지 (동적 상태)
        - 소리/침묵 (감각 위상)
        - 높은 에너지/낮은 에너지
        - 탐색/휴식 (행동 모드)
        """
        tags = {}

        # 시간대 추론
        timestamp = data.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour = dt.hour
                if 6 <= hour < 18:
                    tags["time_phase"] = "낮"
                else:
                    tags["time_phase"] = "밤"
            except Exception:
                tags["time_phase"] = "알 수 없음"

        # 내부 상태 기반 태그
        state = data.get("files", {}).get("agi_internal_state.json", {})
        if state:
            # 에너지 레벨
            try:
                # internal_state.json 직접 로드
                state_data = self._load_json(self.internal_state)
                if state_data:
                    energy = state_data.get("energy", 0.5)
                    tags["energy_level"] = "높은 에너지" if energy > 0.7 else "낮은 에너지" if energy < 0.3 else "중간 에너지"

                    # 주요 drive
                    drives = state_data.get("drives", {})
                    if drives:
                        max_drive = max(drives.items(), key=lambda x: x[1], default=("rest", 0))
                        tags["dominant_drive"] = max_drive[0]

                    # 호기심/지루함
                    curiosity = state_data.get("curiosity", 0.5)
                    boredom = state_data.get("boredom", 0.5)
                    tags["curiosity"] = "호기심 높음" if curiosity > 0.7 else "호기심 낮음" if curiosity < 0.3 else "호기심 중간"
                    tags["boredom"] = "지루함 높음" if boredom > 0.7 else "지루함 낮음" if boredom < 0.3 else "지루함 중간"
            except Exception:
                pass

        # 소스 기반 공간 위상 추론
        sources = data.get("result_summary", {}).get("sources", [])
        if "antigravity" in sources:
            tags["spatial_context"] = "외부 탐색 (AntiGravity)"
        elif "file_sampler" in sources:
            tags["spatial_context"] = "내부 기억 (파일 샘플링)"
        elif "lua_conversation" in sources:
            tags["spatial_context"] = "대화 맥락"
        elif "media" in sources:
            tags["spatial_context"] = "미디어 인식"
        else:
            tags["spatial_context"] = "내적 리듬"

        # 동작 모드
        action = data.get("action", "")
        if action == "self_compress":
            tags["action_mode"] = "수축/압축 (정리)"
        elif action == "self_expansion":
            tags["action_mode"] = "확장 (탐색)"
        elif action == "full_cycle":
            tags["action_mode"] = "완전 사이클 (흐름)"
        else:
            tags["action_mode"] = "대기"

        return tags

    def _generate_wish(self, data: Dict[str, Any], tags: Dict[str, Any]) -> str:
        """
        내부 상태와 태그를 기반으로 "다음에 하고 싶은 것" 1줄 생성
        단, 실행은 루빛이 결정 (제안만)
        """
        wishes = []

        # 지루함이 높으면
        if tags.get("boredom") == "지루함 높음":
            wishes.append("새로운 자극 탐색")

        # 호기심이 높으면
        if tags.get("curiosity") == "호기심 높음":
            wishes.append("외부 세계 관찰")

        # 에너지가 낮으면
        if tags.get("energy_level") == "낮은 에너지":
            wishes.append("휴식과 내적 정리")

        # dominant drive 기반
        drive = tags.get("dominant_drive", "")
        if drive == "explore":
            wishes.append("탐색 행동")
        elif drive == "rest":
            wishes.append("휴식과 회복")
        elif drive == "connect":
            wishes.append("연결과 소통")
        elif drive == "self_focus":
            wishes.append("자기 성찰")

        # 기본값
        if not wishes:
            wishes.append("리듬에 따라 흐르기")

        return wishes[0]

    def generate_from_trigger_report(self, report_data: Optional[Dict[str, Any]] = None) -> HumanSummary:
        """
        Trigger report로부터 Human Summary 생성
        report_data가 None이면 trigger_report_latest.json에서 로드
        """
        if report_data is None:
            report_data = self._load_json(self.trigger_latest)

        if not report_data:
            # 데이터가 없으면 기본값 반환
            return HumanSummary(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger_action="unknown",
                trigger_origin="unknown",
                sources_seen=[],
                tags={},
                one_line_wish="데이터 대기 중",
                internal_state={},
                compression_count=0,
                trigger_reason=None
            )

        # 데이터 추출
        action = report_data.get("action", "unknown")
        origin = report_data.get("origin", "unknown")
        timestamp = report_data.get("timestamp", datetime.now(timezone.utc).isoformat())

        result_summary = report_data.get("result_summary", {})
        compressed = result_summary.get("compressed", result_summary)  # full_cycle의 경우
        sources = compressed.get("sources", [])
        count = compressed.get("count", 0)

        params = report_data.get("params", {})
        reason = params.get("reason")

        # 태그 추출
        tags = self._extract_tags(report_data)

        # 내부 상태 로드
        internal_state_data = self._load_json(self.internal_state) or {}
        internal_snapshot = {
            "consciousness": internal_state_data.get("consciousness", 0.5),
            "unconscious": internal_state_data.get("unconscious", 0.5),
            "background_self": internal_state_data.get("background_self", 0.5),
            "energy": internal_state_data.get("energy", 0.5),
            "boredom": internal_state_data.get("boredom", 0.5),
            "curiosity": internal_state_data.get("curiosity", 0.5),
            "heartbeat_count": internal_state_data.get("heartbeat_count", 0),
            "drives": internal_state_data.get("drives", {}),
        }

        # Wish 생성
        wish = self._generate_wish(report_data, tags)

        return HumanSummary(
            timestamp=timestamp,
            trigger_action=action,
            trigger_origin=origin,
            sources_seen=sources,
            tags=tags,
            one_line_wish=wish,
            internal_state=internal_snapshot,
            compression_count=count,
            trigger_reason=reason
        )

    def save_summary(self, summary: HumanSummary):
        """
        요약을 파일에 저장
        - latest.json (덮어쓰기)
        - history.jsonl (append)
        """
        summary_dict = asdict(summary)

        # Latest 저장
        self.latest_path.write_text(
            json.dumps(summary_dict, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # History append
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(summary_dict, ensure_ascii=False) + "\n")

    def run(self):
        """메인 실행 함수"""
        summary = self.generate_from_trigger_report()
        self.save_summary(summary)
        return summary


def main():
    """CLI Entry point"""
    workspace = Path(__file__).parent.parent.parent
    generator = HumanSummaryGenerator(workspace)
    summary = generator.run()

    print("=" * 60)
    print("Human Summary Generated")
    print("=" * 60)
    print(f"Timestamp: {summary.timestamp}")
    print(f"Action: {summary.trigger_action} (origin: {summary.trigger_origin})")
    print(f"Compression Count: {summary.compression_count}")
    if summary.trigger_reason:
        print(f"Reason: {summary.trigger_reason}")
    print()
    print("Sources Seen:")
    for src in summary.sources_seen:
        print(f"  - {src}")
    print()
    print("Tags:")
    for key, value in summary.tags.items():
        print(f"  - {key}: {value}")
    print()
    print(f"Next Wish: {summary.one_line_wish}")
    print()
    print("Internal State Snapshot:")
    print(f"  - Energy: {summary.internal_state.get('energy', 0):.2f}")
    print(f"  - Boredom: {summary.internal_state.get('boredom', 0):.2f}")
    print(f"  - Curiosity: {summary.internal_state.get('curiosity', 0):.2f}")
    print(f"  - Consciousness: {summary.internal_state.get('consciousness', 0):.2f}")
    print(f"  - Heartbeat: {summary.internal_state.get('heartbeat_count', 0)}")
    drives = summary.internal_state.get('drives', {})
    if drives:
        print("  - Drives:")
        for drive, value in drives.items():
            print(f"      {drive}: {value:.2f}")
    print()
    print(f"Output: {generator.latest_path}")
    print(f"History: {generator.history_path}")


if __name__ == "__main__":
    main()
