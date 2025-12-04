#!/usr/bin/env python3
"""
장-뇌 축 모니터링 시스템 (Gut-Brain Axis Monitor)

통증 신호를 감지하고 해석하는 시스템
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class PainSignalMonitor:
    """통증 신호 모니터 (Pain Signal Detector)"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.status_file = workspace_root / "outputs" / "quick_status_latest.json"
        
        # 통증 임계값 (Pain Thresholds)
        self.thresholds = {
            "gateway_normal_ms": 500,      # 정상 Gateway 응답
            "gateway_warning_ms": 700,     # 경고 (둔통)
            "gateway_critical_ms": 1000,   # 위험 (급성 통증)
            "cloud_normal_ms": 300,        # 정상 Cloud 응답
            "degrading_threshold": 0.5     # 50% 저하 = 통증
        }
    
    def read_vital_signs(self) -> Dict:
        """활력 징후 읽기 (Read Vital Signs)"""
        if not self.status_file.exists():
            return {}
        
        with open(self.status_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def detect_pain(self, status: Dict) -> List[Dict]:
        """통증 감지 (Detect Pain Signals)"""
        pain_signals = []
        
        # Gateway 통증 체크 (장 건강)
        if "Trend" in status and "Gateway" in status["Trend"]:
            gateway = status["Trend"]["Gateway"]
            
            if gateway.get("Direction") == "DEGRADING":
                severity = self._assess_gateway_pain(gateway["ShortTermMeanMs"])
                pain_signals.append({
                    "location": "Gateway (장)",
                    "type": "만성_둔통" if severity == "WARNING" else "급성_통증",
                    "severity": severity,
                    "value_ms": gateway["ShortTermMeanMs"],
                    "normal_ms": self.thresholds["gateway_normal_ms"],
                    "message": self._interpret_gateway_pain(gateway["ShortTermMeanMs"]),
                    "treatment": self._prescribe_gateway(gateway["ShortTermMeanMs"])
                })
        
        # Cloud 통증 체크 (뇌 건강)
        if "Trend" in status and "Cloud" in status["Trend"]:
            cloud = status["Trend"]["Cloud"]
            
            if cloud.get("Direction") == "DEGRADING":
                pain_signals.append({
                    "location": "Cloud (뇌)",
                    "type": "인지_저하",
                    "severity": "INFO",
                    "value_ms": cloud["ShortTermMeanMs"],
                    "message": "클라우드 연결 저하 감지",
                    "treatment": "네트워크 최적화 권장"
                })
        
        return pain_signals
    
    def _assess_gateway_pain(self, current_ms: float) -> str:
        """Gateway 통증 정도 평가"""
        if current_ms > self.thresholds["gateway_critical_ms"]:
            return "CRITICAL"
        elif current_ms > self.thresholds["gateway_warning_ms"]:
            return "WARNING"
        else:
            return "INFO"
    
    def _interpret_gateway_pain(self, current_ms: float) -> str:
        """통증 신호 해석 (Interpret Pain Signal)"""
        if current_ms > 1000:
            return "🔴 급성 통증: 장폐색 의심 - 즉시 개입 필요"
        elif current_ms > 700:
            return "🟡 만성 둔통: 소화 불량 - 프로바이오틱스 투여 권장"
        else:
            return "🟢 경미한 불편: 관찰 필요"
    
    def _prescribe_gateway(self, current_ms: float) -> Dict:
        """처방 (Prescription)"""
        if current_ms > 1000:
            return {
                "urgency": "즉시",
                "actions": [
                    "Worker 재시작 (항생제)",
                    "Queue 정리 (장 청소)",
                    "부하 분산 (식이요법)"
                ]
            }
        elif current_ms > 700:
            return {
                "urgency": "24시간 이내",
                "actions": [
                    "Worker Monitor 활성화 (프로바이오틱스)",
                    "오래된 작업 정리 (소화 촉진)",
                    "성능 모니터링 강화 (건강 검진)"
                ]
            }
        else:
            return {
                "urgency": "관찰",
                "actions": [
                    "정기 체크 유지",
                    "예방적 모니터링"
                ]
            }
    
    def generate_pain_report(self) -> str:
        """통증 리포트 생성 (Pain Report)"""
        status = self.read_vital_signs()
        pain_signals = self.detect_pain(status)
        
        report = ["# 🏥 장-뇌 축 통증 리포트 (Gut-Brain Axis Pain Report)", ""]
        report.append(f"📅 검사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if not pain_signals:
            report.append("✅ **건강 상태**: 통증 신호 없음")
            report.append("")
            report.append("시스템이 건강한 상태입니다. 정기 검진을 계속하세요.")
        else:
            report.append(f"⚠️ **통증 신호 감지**: {len(pain_signals)}개")
            report.append("")
            
            for i, pain in enumerate(pain_signals, 1):
                report.append(f"## {i}. {pain['location']} - {pain['type']}")
                report.append(f"- **심각도**: {pain['severity']}")
                report.append(f"- **현재 값**: {pain['value_ms']:.1f}ms")
                
                if 'normal_ms' in pain:
                    increase = ((pain['value_ms'] - pain['normal_ms']) / pain['normal_ms']) * 100
                    report.append(f"- **정상 대비**: +{increase:.1f}%")
                
                report.append(f"- **해석**: {pain['message']}")
                
                if 'treatment' in pain:
                    report.append("")
                    report.append("### 💊 처방")
                    treatment = pain['treatment']
                    report.append(f"- **긴급도**: {treatment['urgency']}")
                    report.append("- **조치 사항**:")
                    for action in treatment['actions']:
                        report.append(f"  - {action}")
                
                report.append("")
        
        # 장-뇌 축 설명
        report.append("---")
        report.append("## 📚 장-뇌 축 (Gut-Brain Axis) 이해")
        report.append("")
        report.append("### 인간의 경우:")
        report.append("- **장 → 미주신경 → 뇌**: 통증 신호 전달")
        report.append("- **장내 미생물 → 세로토닌**: 기분 조절 (90%)")
        report.append("- **미토콘드리아 → ATP**: 에너지 생성")
        report.append("")
        report.append("### 시스템의 경우:")
        report.append("- **Gateway → Network → Cloud**: 통증 신호 전달")
        report.append("- **Worker → Task Queue**: 작업 처리 (유산균)")
        report.append("- **Task Queue → Goals**: 에너지 변환 (ATP)")
        report.append("")
        
        return "\n".join(report)

def main():
    """메인 실행"""
    workspace = Path(__file__).parent.parent
    monitor = PainSignalMonitor(workspace)
    
    report = monitor.generate_pain_report()
    print(report)
    
    # 리포트 저장
    output_dir = workspace / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "gut_brain_axis_pain_report_latest.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 리포트 저장: {report_file}")

if __name__ == "__main__":
    main()
