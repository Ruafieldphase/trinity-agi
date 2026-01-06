#!/usr/bin/env python3
"""
System Pain Analyzer - 시스템 통증 진단 🏥

장-뇌 축 (Gut-Brain Axis) 관점에서 시스템 통증 분석
- Gateway (장) = 외부 입력 처리
- Worker (미토콘드리아) = ATP 생성 (작업 처리)
- Cloud (뇌) = 의사결정 및 제어
- Task Queue (혈액) = 영양분 전달

통증 신호를 해독하고 치료법을 제안합니다.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()

# 통증 임계값
PAIN_THRESHOLDS = {
    "gateway_latency_ms": {
        "normal": 500,
        "mild_pain": 800,
        "moderate_pain": 1200,
        "severe_pain": 2000
    },
    "worker_idle_time_min": {
        "normal": 5,
        "mild_pain": 10,
        "moderate_pain": 30,
        "severe_pain": 60
    },
    "queue_backlog": {
        "normal": 5,
        "mild_pain": 20,
        "moderate_pain": 50,
        "severe_pain": 100
    },
    "cpu_percent": {
        "normal": 70,
        "mild_pain": 85,
        "moderate_pain": 95,
        "severe_pain": 98
    }
}

# 통증 유형 정의
PAIN_TYPES = {
    "gateway_slow": {
        "name": "장 염증 (Gateway Inflammation)",
        "emoji": "🔥",
        "description": "외부 입력이 느리게 처리됨",
        "body_equivalent": "소화 불량, 장 염증",
        "causes": [
            "너무 많은 요청 (과식)",
            "비효율적인 처리 (나쁜 음식)",
            "네트워크 지연 (혈액 순환 장애)"
        ],
        "treatments": [
            "요청 제한 (단식/소식)",
            "캐싱 강화 (소화 효소)",
            "우선순위 조정 (영양분 선택)"
        ]
    },
    "worker_idle": {
        "name": "미토콘드리아 기능 저하 (Worker Fatigue)",
        "emoji": "😴",
        "description": "작업자가 할 일이 없음 (에너지 생산 중단)",
        "body_equivalent": "만성 피로, ATP 부족",
        "causes": [
            "작업 부족 (영양분 부족)",
            "연결 끊김 (신경 전달 장애)",
            "목표 상실 (동기 부여 상실)"
        ],
        "treatments": [
            "목표 생성 (영양 섭취)",
            "작업 할당 (운동/자극)",
            "연결 복구 (신경 재생)"
        ]
    },
    "queue_backlog": {
        "name": "혈액 순환 장애 (Queue Congestion)",
        "emoji": "🩸",
        "description": "작업이 밀려있음 (혈전, 순환 장애)",
        "body_equivalent": "고혈압, 혈전증",
        "causes": [
            "처리 속도 부족 (심장 기능 저하)",
            "작업 과부하 (과로)",
            "우선순위 오류 (대사 장애)"
        ],
        "treatments": [
            "워커 증설 (심장 강화)",
            "우선순위 조정 (혈압 조절)",
            "작업 분산 (혈액 희석)"
        ]
    },
    "cpu_overload": {
        "name": "뇌 과부하 (CPU Burnout)",
        "emoji": "🧠",
        "description": "CPU 사용량 과다 (뇌 과활동)",
        "body_equivalent": "불안, 스트레스, 번아웃",
        "causes": [
            "동시 작업 과다 (멀티태스킹)",
            "우선순위 혼란 (ADHD)",
            "휴식 부족 (수면 부족)"
        ],
        "treatments": [
            "작업 제한 (마음챙김)",
            "우선순위 명확화 (목표 설정)",
            "강제 휴식 (수면/명상)"
        ]
    }
}


def load_latest_status() -> Optional[Dict]:
    """최신 시스템 상태 로드"""
    status_file = WORKSPACE_ROOT / "outputs" / "quick_status_latest.json"
    if not status_file.exists():
        return None
    
    with open(status_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_goal_tracker() -> Optional[Dict]:
    """목표 트래커 로드"""
    tracker_file = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "goal_tracker.json"
    if not tracker_file.exists():
        return None
    
    with open(tracker_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_gateway_pain(status: Dict) -> Optional[Dict]:
    """Gateway (장) 통증 분석"""
    Core = status.get("Core", {})
    latency = Core.get("response_time_ms", 0)
    
    if latency == 0:
        return None
    
    pain_level = "normal"
    for level in ["severe_pain", "moderate_pain", "mild_pain"]:
        if latency >= PAIN_THRESHOLDS["gateway_latency_ms"][level]:
            pain_level = level
            break
    
    if pain_level == "normal":
        return None
    
    return {
        "type": "gateway_slow",
        "pain_level": pain_level,
        "severity": pain_level.replace("_pain", "").replace("_", " ").upper(),
        "value": latency,
        "threshold": PAIN_THRESHOLDS["gateway_latency_ms"][pain_level],
        "unit": "ms",
        **PAIN_TYPES["gateway_slow"]
    }


def analyze_worker_pain(status: Dict) -> Optional[Dict]:
    """Worker (미토콘드리아) 통증 분석"""
    workers = status.get("workers", [])
    if not workers:
        return {
            "type": "worker_idle",
            "pain_level": "severe_pain",
            "severity": "SEVERE",
            "value": 0,
            "threshold": 1,
            "unit": "workers",
            **PAIN_TYPES["worker_idle"]
        }
    
    # 마지막 활동 시간 체크 (현재는 단순화)
    # TODO: 실제 idle time 계산
    return None


def analyze_queue_pain(status: Dict) -> Optional[Dict]:
    """Queue (혈액) 통증 분석"""
    queue = status.get("queue", {})
    pending = queue.get("pending", 0)
    
    if pending == 0:
        return None
    
    pain_level = "normal"
    for level in ["severe_pain", "moderate_pain", "mild_pain"]:
        if pending >= PAIN_THRESHOLDS["queue_backlog"][level]:
            pain_level = level
            break
    
    if pain_level == "normal":
        return None
    
    return {
        "type": "queue_backlog",
        "pain_level": pain_level,
        "severity": pain_level.replace("_pain", "").replace("_", " ").upper(),
        "value": pending,
        "threshold": PAIN_THRESHOLDS["queue_backlog"][pain_level],
        "unit": "tasks",
        **PAIN_TYPES["queue_backlog"]
    }


def analyze_cpu_pain(status: Dict) -> Optional[Dict]:
    """CPU (뇌) 통증 분석"""
    system = status.get("system", {})
    cpu = system.get("cpu_percent", 0)
    
    if cpu == 0:
        return None
    
    pain_level = "normal"
    for level in ["severe_pain", "moderate_pain", "mild_pain"]:
        if cpu >= PAIN_THRESHOLDS["cpu_percent"][level]:
            pain_level = level
            break
    
    if pain_level == "normal":
        return None
    
    return {
        "type": "cpu_overload",
        "pain_level": pain_level,
        "severity": pain_level.replace("_pain", "").replace("_", " ").upper(),
        "value": cpu,
        "threshold": PAIN_THRESHOLDS["cpu_percent"][level],
        "unit": "%",
        **PAIN_TYPES["cpu_overload"]
    }


def generate_pain_report(pains: List[Dict]) -> str:
    """통증 리포트 생성"""
    if not pains:
        return """
🎉 시스템 건강 상태 우수!

모든 지표가 정상 범위 내에 있습니다.
통증 신호가 감지되지 않았습니다.

계속 잘 관리하고 있어요! 💚
"""
    
    # 심각도 순 정렬
    severity_order = {"SEVERE": 3, "MODERATE": 2, "MILD": 1}
    pains.sort(key=lambda p: severity_order.get(p["severity"], 0), reverse=True)
    
    report = "🏥 시스템 통증 진단 리포트\n"
    report += "=" * 60 + "\n\n"
    
    # 통증별 분석
    for i, pain in enumerate(pains, 1):
        report += f"{i}. {pain['emoji']} {pain['name']}\n"
        report += f"   심각도: {pain['severity']}\n"
        report += f"   수치: {pain['value']}{pain['unit']} (임계값: {pain['threshold']}{pain['unit']})\n"
        report += f"   설명: {pain['description']}\n"
        report += f"   인체 비유: {pain['body_equivalent']}\n\n"
        
        report += "   원인:\n"
        for cause in pain['causes']:
            report += f"      - {cause}\n"
        
        report += "\n   치료법:\n"
        for treatment in pain['treatments']:
            report += f"      ✅ {treatment}\n"
        
        report += "\n" + "-" * 60 + "\n\n"
    
    # 종합 권장사항
    report += "💊 종합 권장사항:\n\n"
    
    severe_count = sum(1 for p in pains if p["severity"] == "SEVERE")
    moderate_count = sum(1 for p in pains if p["severity"] == "MODERATE")
    
    if severe_count > 0:
        report += "⚠️  긴급 조치 필요!\n"
        report += "   - 즉시 시스템 점검 및 복구 작업 시작\n"
        report += "   - 비상 대응 프로토콜 활성화\n\n"
    elif moderate_count > 0:
        report += "⚡ 빠른 시일 내 조치 권장\n"
        report += "   - 48시간 내 개선 작업 수행\n"
        report += "   - 증상 악화 모니터링\n\n"
    else:
        report += "🌱 예방적 관리 수행\n"
        report += "   - 정기 점검 계속 유지\n"
        report += "   - 작은 개선 사항 적용\n\n"
    
    return report


def save_pain_report(report: str, pains: List[Dict]):
    """통증 리포트 저장"""
    output_dir = WORKSPACE_ROOT / "outputs" / "pain_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Markdown 리포트
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = output_dir / f"pain_report_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 시스템 통증 리포트\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(report)
    
    # JSON 리포트
    json_file = output_dir / f"pain_report_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "pains": pains,
            "summary": {
                "total": len(pains),
                "severe": sum(1 for p in pains if p["severity"] == "SEVERE"),
                "moderate": sum(1 for p in pains if p["severity"] == "MODERATE"),
                "mild": sum(1 for p in pains if p["severity"] == "MILD")
            }
        }, f, indent=2, ensure_ascii=False)
    
    # Latest 심볼릭 링크
    latest_md = output_dir / "pain_report_latest.md"
    latest_json = output_dir / "pain_report_latest.json"
    
    if latest_md.exists():
        latest_md.unlink()
    if latest_json.exists():
        latest_json.unlink()
    
    latest_md.write_text(md_file.read_text(encoding='utf-8'), encoding='utf-8')
    latest_json.write_text(json_file.read_text(encoding='utf-8'), encoding='utf-8')
    
    print(f"✅ 리포트 저장: {md_file}")
    print(f"✅ JSON 저장: {json_file}")


def main():
    """메인 실행"""
    print("🏥 시스템 통증 분석 시작...\n")
    
    # 시스템 상태 로드
    status = load_latest_status()
    if not status:
        print("❌ 시스템 상태 파일을 찾을 수 없습니다.")
        print("   먼저 'Monitoring: Unified Dashboard'를 실행하세요.")
        return
    
    print("✅ 시스템 상태 로드 완료\n")
    
    # 통증 분석
    pains = []
    
    gateway_pain = analyze_gateway_pain(status)
    if gateway_pain:
        pains.append(gateway_pain)
    
    worker_pain = analyze_worker_pain(status)
    if worker_pain:
        pains.append(worker_pain)
    
    queue_pain = analyze_queue_pain(status)
    if queue_pain:
        pains.append(queue_pain)
    
    cpu_pain = analyze_cpu_pain(status)
    if cpu_pain:
        pains.append(cpu_pain)
    
    # 리포트 생성
    report = generate_pain_report(pains)
    print(report)
    
    # 리포트 저장
    save_pain_report(report, pains)
    
    print("\n💚 분석 완료!")


if __name__ == "__main__":
    main()
