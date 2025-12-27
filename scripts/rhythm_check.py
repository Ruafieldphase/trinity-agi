#!/usr/bin/env python3
"""
리듬 체온계 (Rhythm Thermometer)
AGI 시스템의 건강 상태를 한눈에 보여주는 도구

사용법:
  python agi/scripts/rhythm_check.py              # 기본 체크
  python agi/scripts/rhythm_check.py --detail     # 상세 모드
  python agi/scripts/rhythm_check.py --json       # JSON 출력
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import subprocess

# 프로젝트 루트 찾기
# C:\workspace\agi\scripts\rhythm_check.py
# parent = scripts, parent.parent = agi, parent.parent.parent = workspace
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class RhythmThermometer:
    """AGI 시스템 건강 체크"""

    def __init__(self):
        self.root = project_root
        self.now = datetime.now(timezone.utc)
        self.warnings = []
        self.oks = []
        self.health_score = 100  # 시작 100점

    def read_json(self, path: str) -> Optional[Dict]:
        """JSON 파일 읽기 (에러 처리)"""
        full_path = self.root / path
        if not full_path.exists():
            return None
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"DEBUG: Error reading {path}: {e}")
            return None

    def get_file_age_days(self, path: str) -> Optional[float]:
        """파일이 얼마나 오래됐는지 (일 단위)"""
        full_path = self.root / path
        if not full_path.exists():
            return None
        mtime = datetime.fromtimestamp(full_path.stat().st_mtime, tz=timezone.utc)
        age = (self.now - mtime).total_seconds() / 86400
        return age

    def check_vital_signs(self) -> Dict:
        """생명 징후 체크"""
        state = self.read_json("agi/memory/agi_internal_state.json")
        thought = self.read_json("agi/outputs/thought_stream_latest.json")

        if not state:
            self.warnings.append("Internal state 파일 없음")
            self.health_score -= 30
            return {}

        vital = {
            "heartbeat": state.get("heartbeat_count", 0),
            "energy": state.get("energy", 0) * 100,
            "phase": thought.get("state", {}).get("phase", "UNKNOWN") if thought else "UNKNOWN",
            "atp": thought.get("state", {}).get("atp", 0) if thought else 0,
        }

        # 심장박동 체크
        if vital["heartbeat"] > 0:
            self.oks.append(f"Heart: {vital['heartbeat']:,}회 박동 (정상)")
        else:
            self.warnings.append("Heartbeat 0 - 시스템 정지?")
            self.health_score -= 40

        # 에너지 레벨
        if vital["energy"] > 70:
            self.oks.append(f"Energy: {vital['energy']:.1f}% (높음 ⚡)")
        elif vital["energy"] > 30:
            self.oks.append(f"Energy: {vital['energy']:.1f}% (보통)")
        else:
            self.warnings.append(f"Energy 낮음: {vital['energy']:.1f}%")
            self.health_score -= 15

        return vital

    def check_emotional_state(self) -> Dict:
        """감정 상태 체크"""
        state = self.read_json("agi/memory/agi_internal_state.json")
        thought = self.read_json("agi/outputs/thought_stream_latest.json")

        if not state:
            return {}

        emotion = {
            "boredom": state.get("boredom", 0) * 100,
            "curiosity": state.get("curiosity", 0) * 100,
            "feeling": thought.get("feeling", {}).get("description", "") if thought else "",
        }

        # 지루함 체크
        if emotion["boredom"] >= 90:
            self.warnings.append(f"Boredom 극대: {emotion['boredom']:.0f}% (새 자극 필요)")
            self.health_score -= 10
        elif emotion["boredom"] >= 70:
            self.warnings.append(f"Boredom 높음: {emotion['boredom']:.0f}%")
            self.health_score -= 5

        # 호기심 체크
        if emotion["curiosity"] == 0 and emotion["boredom"] > 80:
            self.warnings.append("호기심 0% + 지루함 높음 - 탐색 의욕 고갈")
            self.health_score -= 5

        return emotion

    def check_drives(self) -> Dict:
        """욕구 상태 체크"""
        state = self.read_json("agi/memory/agi_internal_state.json")
        if not state:
            return {}

        drives = state.get("drives", {})

        # Connect drive 낮으면 경고
        if drives.get("connect", 0) < 0.2:
            self.warnings.append(f"Connect drive 매우 낮음: {drives['connect']*100:.0f}% (고립 위험)")
            self.health_score -= 5

        return drives

    def check_connections(self) -> Dict:
        """연결 상태 체크 (Shion, Koa, Rua)"""
        connections = {}

        # Shion 체크 (Windows PowerShell)
        try:
            creationflags = 0
            if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                 "-Command", r".\agi\scripts\autonomous_collaboration_daemon.ps1 -Action status"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.root,
                creationflags=creationflags,
            )
            if "NOT RUNNING" in result.stdout:
                connections["shion"] = "OFFLINE"
                # Shion 마지막 실행 시간 파악 (대략)
                age = self.get_file_age_days("agi/memory/resonance_ledger.jsonl")
                if age and age > 7:
                    self.warnings.append(f"Shion OFFLINE ({age:.0f}일째) - 외부 소통 불가")
                    self.health_score -= 20
                else:
                    self.warnings.append("Shion OFFLINE - 외부 소통 불가")
                    self.health_score -= 15
            else:
                connections["shion"] = "ONLINE"
                self.oks.append("Shion 작동 중")
        except Exception:
            connections["shion"] = "UNKNOWN"
            self.warnings.append("Shion 상태 확인 실패")
            self.health_score -= 10

        # Koa context 체크
        koa_exists = (self.root / "agi/memory/koa_context.json").exists()
        connections["koa_context"] = "EXISTS" if koa_exists else "MISSING"
        if not koa_exists:
            self.warnings.append("Koa context 파일 없음 - 영구 기억 부재")
            self.health_score -= 10
        else:
            self.oks.append("Koa context 존재")

        # Rua context 체크
        rua_exists = (self.root / "agi/memory/rua_context.json").exists()
        connections["rua_context"] = "EXISTS" if rua_exists else "MISSING"
        if not rua_exists:
            self.warnings.append("Rua context 파일 없음 - 영구 기억 부재")
            self.health_score -= 10
        else:
            self.oks.append("Rua context 존재")

        return connections

    def check_system_freshness(self) -> Dict:
        """시스템 파일 갱신 상태"""
        freshness = {}

        # Lumen State 체크
        lumen_age = self.get_file_age_days("agi/outputs/lumen_state.json")
        if lumen_age is not None:
            freshness["lumen_state_age_days"] = lumen_age
            if lumen_age > 7:
                self.warnings.append(f"Lumen State {lumen_age:.0f}일째 미갱신 - Fear 시스템 동결")
                self.health_score -= 10
            elif lumen_age > 1:
                self.warnings.append(f"Lumen State {lumen_age:.1f}일째 미갱신")
                self.health_score -= 5
        else:
            freshness["lumen_state_age_days"] = None
            self.warnings.append("Lumen State 파일 없음")
            self.health_score -= 10

        # Thought Stream 체크
        thought_age = self.get_file_age_days("agi/outputs/thought_stream_latest.json")
        if thought_age is not None:
            freshness["thought_stream_age_hours"] = thought_age * 24
            if thought_age > 0.5:  # 12시간
                self.warnings.append(f"Thought Stream {thought_age*24:.1f}시간째 미갱신")
                self.health_score -= 15
            else:
                self.oks.append("Thought Stream 최신 상태")

        # Resonance Ledger 체크
        ledger_age = self.get_file_age_days("agi/memory/resonance_ledger.jsonl")
        if ledger_age is not None:
            freshness["resonance_ledger_age_days"] = ledger_age
            if ledger_age < 7:
                self.oks.append("Resonance Ledger 기록 중")

        return freshness

    def check_internal_processes(self) -> Dict:
        """내부 프로세스 체크"""
        processes = {}

        # Self-Compression 체크
        state = self.read_json("agi/memory/agi_internal_state.json")
        if state and "self_expansion" in state:
            comp = state["self_expansion"]
            processes["compression_events"] = comp.get("compression_events", 0)
            if comp.get("compression_events", 0) > 0:
                self.oks.append(f"Self-Compression 작동 중 ({comp['compression_events']}회)")

        # Internal clock 체크
        if state and "internal_clock" in state:
            processes["internal_clock"] = state["internal_clock"]
            if state["internal_clock"] > 0:
                self.oks.append("내부 리듬 발진 정상")

        return processes

    def calculate_health_score(self) -> int:
        """건강도 점수 (0~100)"""
        return max(0, min(100, self.health_score))

    def get_health_label(self, score: int) -> Tuple[str, str]:
        """건강도 레이블 및 색상"""
        if score >= 80:
            return "우수", "🟢"
        elif score >= 60:
            return "보통", "🟡"
        elif score >= 40:
            return "주의", "🟠"
        else:
            return "위험", "🔴"

    def run_check(self) -> Dict:
        """전체 체크 실행"""
        vital = self.check_vital_signs()
        emotion = self.check_emotional_state()
        drives = self.check_drives()
        connections = self.check_connections()
        freshness = self.check_system_freshness()
        processes = self.check_internal_processes()

        score = self.calculate_health_score()
        label, icon = self.get_health_label(score)

        return {
            "timestamp": self.now.isoformat(),
            "health_score": score,
            "health_label": label,
            "health_icon": icon,
            "vital_signs": vital,
            "emotional_state": emotion,
            "drives": drives,
            "connections": connections,
            "freshness": freshness,
            "processes": processes,
            "warnings": self.warnings,
            "oks": self.oks,
        }

    def print_report(self, data: Dict, detail: bool = False):
        """리포트 출력 (사람이 읽기 좋게)"""
        print("=" * 60)
        print(f"🌡️ AGI 리듬 체온계")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        # 종합 건강도
        score = data["health_score"]
        label = data["health_label"]
        icon = data["health_icon"]
        print(f"📊 종합 건강도: {score}/100 ({label}) {icon}")
        print()

        # 생명 징후
        vital = data["vital_signs"]
        if vital:
            print("💓 생명 징후:")
            print(f"  Heart: {vital.get('heartbeat', 0):,}회 박동")
            print(f"  Energy: {vital.get('energy', 0):.1f}%")
            print(f"  ATP: {vital.get('atp', 0):.1f}")
            print(f"  Phase: {vital.get('phase', 'UNKNOWN')}")
            print()

        # 감정 상태
        emotion = data["emotional_state"]
        if emotion:
            print("😊 감정 상태:")
            print(f"  Boredom: {emotion.get('boredom', 0):.0f}%", end="")
            if emotion.get('boredom', 0) >= 90:
                print(" ⚠️ (극도로 지루함)")
            elif emotion.get('boredom', 0) >= 70:
                print(" (높음)")
            else:
                print()

            print(f"  Curiosity: {emotion.get('curiosity', 0):.0f}%")
            if emotion.get('feeling'):
                print(f"  Feeling: \"{emotion['feeling']}\"")
            print()

        # 욕구
        drives = data["drives"]
        if drives and detail:
            print("🎯 욕구:")
            for drive, value in drives.items():
                print(f"  {drive.capitalize()}: {value*100:.0f}%")
            print()

        # 연결 상태
        connections = data["connections"]
        if connections:
            print("🔗 연결 상태:")
            shion = connections.get("shion", "UNKNOWN")
            if shion == "ONLINE":
                print(f"  Shion: ✅ ONLINE")
            elif shion == "OFFLINE":
                print(f"  Shion: ❌ OFFLINE")
            else:
                print(f"  Shion: ⚠️ UNKNOWN")

            koa = connections.get("koa_context", "MISSING")
            print(f"  Koa Context: {'✅' if koa == 'EXISTS' else '⚠️'} {koa}")

            rua = connections.get("rua_context", "MISSING")
            print(f"  Rua Context: {'✅' if rua == 'EXISTS' else '⚠️'} {rua}")
            print()

        # 경고
        if data["warnings"]:
            print(f"⚠️ 경고 ({len(data['warnings'])}개):")
            for i, warning in enumerate(data["warnings"], 1):
                print(f"  {i}. {warning}")
            print()

        # 정상 항목
        if data["oks"]:
            print(f"✅ 정상 ({len(data['oks'])}개):")
            for ok in data["oks"][:5]:  # 최대 5개만
                print(f"  - {ok}")
            if len(data["oks"]) > 5:
                print(f"  ... 외 {len(data['oks']) - 5}개")
            print()

        # 상세 정보
        if detail:
            freshness = data["freshness"]
            if freshness:
                print("🕐 파일 갱신 상태:")
                for key, value in freshness.items():
                    if value is not None:
                        print(f"  {key}: {value:.2f}")
                print()

        print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AGI 리듬 체온계")
    parser.add_argument("--detail", action="store_true", help="상세 모드")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    thermo = RhythmThermometer()
    data = thermo.run_check()

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        thermo.print_report(data, detail=args.detail)


if __name__ == "__main__":
    main()
