#!/usr/bin/env python3
"""
통합 운영 대시보드
AGI + Lumen + Proxy + System 상태를 한눈에 표시
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# monitor 모듈 import를 위한 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from monitor.metrics_collector import MetricsCollector


class OpsDashboard:
    """운영 대시보드 생성"""

    def __init__(self):
        self.collector = MetricsCollector()
        self.colors = {
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'cyan': '\033[96m',
            'bold': '\033[1m',
            'reset': '\033[0m',
        }

    def _colorize(self, text: str, color: str) -> str:
        """텍스트에 색상 적용"""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def _status_icon(self, ok: bool) -> str:
        """상태 아이콘"""
        if ok:
            return self._colorize("✅", "green")
        else:
            return self._colorize("❌", "red")

    def print_dashboard(self, hours: float = 1.0):
        """대시보드 출력 (터미널)"""
        print(self._colorize("\n" + "="*60, "cyan"))
        print(self._colorize("🚀 AGI 운영 대시보드", "bold"))
        print(self._colorize("="*60 + "\n", "cyan"))

        # 헬스 상태 가져오기
        health = self.collector.get_health_status()
        metrics_snapshot = self.collector.get_realtime_metrics(hours=hours)
        event_counts = metrics_snapshot.get('event_counts', {})
        metrics_values = metrics_snapshot.get('metrics', {})

        # 전체 상태
        overall_icon = self._status_icon(health['healthy'])
        print(f"{overall_icon} {self._colorize('전체 상태:', 'bold')} " +
              (self._colorize("HEALTHY", "green") if health['healthy'] else self._colorize("UNHEALTHY", "red")))
        print()

        # AGI 메트릭 with Policy Info
        policy = health.get('policy', {})
        recent_hrs = policy.get('recent_hours', 1.0)
        samples = policy.get('samples', {})
        notes = policy.get('notes', {})
        
        print(self._colorize(f"📊 AGI 메트릭 (최근 {recent_hrs}시간, min samples={policy.get('min_samples', {}).get('confidence', 5)})", "bold"))
        
        # Confidence
        conf_note = notes.get('confidence', '')
        conf_samples = samples.get('confidence', 0)
        print(f"  • Confidence: {health['current_values']['confidence']:.3f} " +
              f"(min: {health['thresholds']['min_confidence']}, samples: {conf_samples}) " +
              self._status_icon(health['checks']['confidence_ok']))
        if conf_note:
            print(f"    ℹ️  {conf_note}")
        
        # Quality
        qual_note = notes.get('quality', '')
        qual_samples = samples.get('quality', 0)
        print(f"  • Quality:    {health['current_values']['quality']:.3f} " +
              f"(min: {health['thresholds']['min_quality']}, samples: {qual_samples}) " +
              self._status_icon(health['checks']['quality_ok']))
        if qual_note:
            print(f"    ℹ️  {qual_note}")
        
        # Second Pass
        sp_rate = health['current_values']['second_pass_rate']
        print(f"  • 2nd Pass:   {sp_rate:.3f} " +
              f"(max: {health['thresholds']['max_second_pass_rate']}) " +
              self._status_icon(health['checks']['second_pass_ok']))
        print()

        # Evidence & RAG 메트릭 표시
        evidence_metrics = metrics_values.get('evidence_correction', {})
        if evidence_metrics.get('attempts', 0) > 0:
            print(self._colorize(f"🔍 Evidence & RAG 메트릭 (최근 {hours}h)", "bold"))
            
            attempts = evidence_metrics.get('attempts', 0)
            avg_hits = evidence_metrics.get('avg_hits', 0.0)
            avg_added = evidence_metrics.get('avg_added', 0.0)
            avg_relevance = evidence_metrics.get('avg_relevance', 0.0)
            success_rate = evidence_metrics.get('success_rate', 0.0)
            
            # Success rate에 따른 색상
            if success_rate >= 0.5:
                rate_color = "green"
            elif success_rate >= 0.2:
                rate_color = "yellow"
            else:
                rate_color = "red"
            
            print(f"  • 시도 횟수:    {attempts}")
            print(f"  • 성공률:       {self._colorize(f'{success_rate:.1%}', rate_color)}")
            print(f"  • 평균 hits:    {avg_hits:.2f}")
            print(f"  • 평균 추가:    {avg_added:.2f} citations")
            print(f"  • 평균 관련도:  {avg_relevance:.3f}")
            # Optional: Fallback rate
            fb_rate = evidence_metrics.get('fallback_rate')
            if fb_rate is not None:
                print(f"  • 폴백 비율:    {fb_rate:.1%}")
            print()

        # Second Pass 상세 분석 (second_pass_analysis.json 있으면 표시)
        sp_analysis_path = repo_root / "outputs" / "second_pass_analysis.json"
        if sp_analysis_path.exists():
            try:
                with open(sp_analysis_path, 'r', encoding='utf-8') as f:
                    sp_data = json.load(f)
                
                print(self._colorize("🔍 Second Pass 분석 (24h)", "bold"))
                
                total_cases = sp_data.get('total_cases', 0)
                cases = sp_data.get('cases', [])
                
                # Evidence failure rate 계산
                evidence_failures = sum(1 for c in cases if not c.get('evidence_ok', True))
                evidence_failure_rate = evidence_failures / total_cases if total_cases > 0 else 0
                
                # Quality gap 평균 계산
                quality_gaps = [c.get('quality_gap', 0) for c in cases]
                avg_quality_gap = sum(quality_gaps) / len(quality_gaps) if quality_gaps else 0
                
                # Top recommendations 집계
                all_recs = {}
                for c in cases:
                    for rec in c.get('recommendations', []):
                        all_recs[rec] = all_recs.get(rec, 0) + 1
                
                print(f"  • Total cases: {total_cases}")
                print(f"  • Evidence failure: {int(evidence_failure_rate * 100)}%")
                print(f"  • Avg quality gap: {avg_quality_gap:.3f}")
                
                if all_recs:
                    top_rec = max(all_recs.items(), key=lambda x: x[1])
                    print(f"  • Top issue: {top_rec[0]} ({top_rec[1]} cases)")
                print()
            except Exception as e:
                # 파일 읽기 실패 시 조용히 넘어감
                pass

        # Replan 상세 분석 (replan_analysis.json 있으면 표시)
        replan_analysis_path = repo_root / "outputs" / "replan_analysis.json"
        if replan_analysis_path.exists():
            try:
                with open(replan_analysis_path, 'r', encoding='utf-8') as f:
                    rp_data = json.load(f)

                print(self._colorize("🔄 Replan 분석 (24h)", "bold"))

                total_cases = rp_data.get('total_cases', 0)
                cases = rp_data.get('cases', [])
                stats = rp_data.get('statistics', {})

                # Evidence failure rate
                evidence_fail_rate = stats.get('evidence_failure_rate')
                if evidence_fail_rate is None and cases:
                    failures = sum(1 for c in cases if not c.get('evidence_ok', True))
                    evidence_fail_rate = failures / total_cases if total_cases else 0

                # Avg quality gap
                avg_quality_gap = stats.get('avg_quality_gap')
                if avg_quality_gap is None:
                    qgaps = [c.get('quality_gap', 0) for c in cases]
                    avg_quality_gap = (sum(qgaps) / len(qgaps)) if qgaps else 0

                # Top recommendations
                all_recs = {}
                for c in cases:
                    for rec in c.get('recommendations', []):
                        all_recs[rec] = all_recs.get(rec, 0) + 1

                print(f"  • Total cases: {total_cases}")
                print(f"  • Evidence failure: {int((evidence_fail_rate or 0) * 100)}%")
                print(f"  • Avg quality gap: {float(avg_quality_gap or 0):.3f}")

                if all_recs:
                    top_rec = max(all_recs.items(), key=lambda x: x[1])
                    print(f"  • Top issue: {top_rec[0]} ({top_rec[1]} cases)")
                print()
            except Exception:
                pass


        # 메타인지/위임 시그널
        low_conf_count = int(event_counts.get('low_confidence_warning', 0))
        meta_eval_count = int(event_counts.get('meta_cognition', 0))
        warning_ratio = (low_conf_count / meta_eval_count) if meta_eval_count else None
        total_tasks = int(metrics_values.get('total_tasks', 0))
        replan_count = int(metrics_values.get('replan_count', 0))
        second_pass_count = int(metrics_values.get('second_pass_count', 0))

        print(self._colorize("\U0001f9e0 Meta-Cognition Signals", "bold"))
        print(f"  {self._status_icon(low_conf_count == 0)} Low confidence warnings: {low_conf_count}")
        if warning_ratio is not None:
            print(f"  \u2022 Warning ratio: {warning_ratio:.2f} ({low_conf_count}/{meta_eval_count} evaluations)")
        else:
            print("  \u2022 Warning ratio: N/A (no meta-cognition events)")
        if low_conf_count:
            print("  \u26a0\ufe0f  Investigate disabled tools or delegate as suggested")
        print()

        print(self._colorize("\U0001f4dd Task Flow", "bold"))
        print(f"  \u2022 Tasks processed: {total_tasks}")
        print(f"  \u2022 Replans: {replan_count}")
        print(f"  \u2022 Second passes: {second_pass_count}")
        print()

        # Canary Monitoring
        print(self._colorize("🚀 Canary Deployment", "bold"))
        try:
            # 최근 로그 파일 확인으로 루프 작동 여부 판단
            import glob
            from datetime import datetime, timedelta
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from workspace_utils import find_workspace_root
            
            workspace = find_workspace_root(Path(__file__).parent)
            log_pattern = str(workspace / "LLM_Unified" / "ion-mentoring" / "logs" / "monitor_loop_*.log")
            log_files = glob.glob(log_pattern)
            
            canary_loop_running = False
            if log_files:
                latest_log = max(log_files, key=lambda p: Path(p).stat().st_mtime)
                log_age_mins = (datetime.now().timestamp() - Path(latest_log).stat().st_mtime) / 60
                canary_loop_running = log_age_mins < 35  # 30분 간격 + 5분 여유
                
                print(f"  {self._status_icon(canary_loop_running)} Monitoring Loop: " +
                      ("Running (30min intervals)" if canary_loop_running else f"Idle ({log_age_mins:.0f}m ago)"))
            else:
                print(f"  {self._status_icon(False)} Monitoring Loop: No logs found")
            
            # 최근 probe 결과 읽기 시도
            probe_pattern = str(workspace / \"LLM_Unified\" / \"ion-mentoring\" / \"logs\" / \"probe_iter_*.json\")
            probe_files = glob.glob(probe_pattern)
            if probe_files:
                latest_probe = max(probe_files, key=lambda p: Path(p).stat().st_mtime)
                probe_data = json.loads(Path(latest_probe).read_text(encoding='utf-8'))
                probe_time = datetime.fromisoformat(probe_data.get('timestamp', ''))
                # Make timezone-naive for comparison
                probe_time = probe_time.replace(tzinfo=None)
                age_mins = (datetime.now() - probe_time).total_seconds() / 60
                
                if age_mins < 60:  # 최근 1시간 이내 데이터만 표시
                    legacy = probe_data.get('legacy', {})
                    canary = probe_data.get('canary', {})
                    legacy_rate = legacy.get('success_rate', 0)
                    canary_rate = canary.get('success_rate', 0)
                    legacy_ms = legacy.get('avg_response_ms', 0)
                    canary_ms = canary.get('avg_response_ms', 0)
                    print(f"  • Latest Probe ({age_mins:.0f}m ago):")
                    print(f"    Legacy: {legacy_rate:.0f}% success, {legacy_ms:.0f}ms avg")
                    print(f"    Canary: {canary_rate:.0f}% success, {canary_ms:.0f}ms avg")
                else:
                    print(f"  ℹ️  Probe data stale ({age_mins:.0f}m old)")
            else:
                print("  ℹ️  No probe data yet (first run pending)")
        except Exception as e:
            print(f"  ⚠️  Canary status check failed: {str(e)[:50]}")
        print()

        # Lumen Gateway
        print(self._colorize("🌐 Lumen Gateway", "bold"))
        lumen = health['external_services']['lumen']
        print(f"  {self._status_icon(lumen['ok'])} Gateway: " +
              (lumen.get('response_preview', lumen.get('error', 'unknown'))[:80]))
        print()

        # Local Proxy (with resolved port)
        print(self._colorize("🔌 Local Proxy", "bold"))
        proxy = health['external_services']['proxy']
        resolved_port = policy.get('resolved_proxy_port', proxy.get('port', 8090))
        print(f"  {self._status_icon(proxy['ok'])} Port {resolved_port}: {proxy.get('status', proxy.get('error', 'unknown'))}")
        if resolved_port != proxy.get('port', 8090):
            print(f"    ℹ️  Resolved from proxy_info.json (configured: {proxy.get('port', 8090)})")
        print()

        # System Resources
        print(self._colorize("💻 System Resources", "bold"))
        system = health['external_services']['system']
        if 'note' in system:
            print(f"  ℹ️  {system['note']}")
        elif 'error' in system:
            print(f"  {self._status_icon(False)} Error: {system['error']}")
        else:
            print(f"  • CPU:    {system['cpu_percent']}% " +
                  ("⚠️" if system['warnings']['cpu'] else "✅"))
            print(f"  • Memory: {system['memory_percent']}% " +
                  ("⚠️" if system['warnings']['memory'] else "✅"))
            print(f"  • Disk:   {system['disk_percent']}% " +
                  ("⚠️" if system['warnings']['disk'] else "✅"))
        print()

        # Timeline 미리보기
        print(self._colorize("📈 Timeline (최근 6시간)", "bold"))
        timeline = self.collector.get_timeline_data(hours=6.0, interval_minutes=30)
        for entry in timeline[-3:]:  # 마지막 3개 구간
            ts = entry['timestamp'].split('T')[1][:5]  # HH:MM만 추출
            print(f"  {ts}: {entry['event_count']:3d} events, " +
                  f"Q={entry['avg_quality'] or 'N/A'}, C={entry['avg_confidence'] or 'N/A'}")

        print(self._colorize("\n" + "="*60 + "\n", "cyan"))

    def generate_json_report(self, hours: float = 1.0) -> Dict[str, Any]:
        """JSON 리포트 생성"""
        health = self.collector.get_health_status()
        realtime = self.collector.get_realtime_metrics(hours=hours)
        timeline = self.collector.get_timeline_data(hours=6.0, interval_minutes=30)

        return {
            'timestamp': realtime['timestamp'],
            'healthy': health['healthy'],
            'health_checks': health['checks'],
            'policy': health.get('policy', {}),  # Policy 정보 추가
            'metrics': realtime['metrics'],
            'external_services': health['external_services'],
            'timeline': timeline[-6:],  # 마지막 6개 구간
        }


def main():
    """CLI 엔트리 포인트"""
    import argparse
    import sys
    import io

    # UTF-8 출력 강제 설정 (Windows cp949 인코딩 문제 해결)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='AGI 통합 운영 대시보드')
    parser.add_argument('--json', action='store_true', help='JSON 포맷으로 출력')
    parser.add_argument('--hours', type=float, default=1.0, help='메트릭 수집 시간 범위 (기본: 1시간)')
    args = parser.parse_args()

    dashboard = OpsDashboard()

    if args.json:
        report = dashboard.generate_json_report(hours=args.hours)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        dashboard.print_dashboard(hours=args.hours)


if __name__ == '__main__':
    main()
