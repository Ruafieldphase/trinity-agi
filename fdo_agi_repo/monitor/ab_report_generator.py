#!/usr/bin/env python3
"""
A/B Test Report Generator
시각적 비교 리포트 생성
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class ABReportGenerator:
    """A/B 테스트 리포트 생성"""

    @staticmethod
    def generate_markdown_report(result: Dict[str, Any], output_path: Path):
        """Markdown 리포트 생성"""

        stats_a = result['stats_a']
        stats_b = result['stats_b']
        diff = result['difference']
        iterations = result['iterations']

        # Config 이름 추출
        config_a_name = f"Config A ({result['config_a'].get('SYNTHESIS_SECTION_MAX_CHARS', '?')})"
        config_b_name = f"Config B ({result['config_b'].get('SYNTHESIS_SECTION_MAX_CHARS', '?')})"

        report = f"""# A/B 테스트 결과 리포트

**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**반복 횟수**: {iterations}회 (총 {iterations * 2}회 실행)

---

## 📊 설정 비교

| 항목 | {config_a_name} | {config_b_name} |
|------|---------|---------|
| **SYNTHESIS_SECTION_MAX_CHARS** | {result['config_a'].get('SYNTHESIS_SECTION_MAX_CHARS', 'N/A')} | {result['config_b'].get('SYNTHESIS_SECTION_MAX_CHARS', 'N/A')} |

---

## 📈 메트릭 비교

### 1. Confidence (높을수록 좋음)

| 통계 | {config_a_name} | {config_b_name} | 차이 |
|------|---------|---------|------|
| **평균** | {stats_a['confidence']['mean']:.3f} | {stats_b['confidence']['mean']:.3f} | {diff['confidence']['absolute']:+.3f} ({diff['confidence']['percentage']:+.1f}%) |
| **표준편차** | {stats_a['confidence']['stdev']:.3f} | {stats_b['confidence']['stdev']:.3f} | - |
| **최소값** | {stats_a['confidence']['min']:.3f} | {stats_b['confidence']['min']:.3f} | - |
| **최대값** | {stats_a['confidence']['max']:.3f} | {stats_b['confidence']['max']:.3f} | - |

**원시 데이터**:
- {config_a_name}: {stats_a['confidence']['values']}
- {config_b_name}: {stats_b['confidence']['values']}

---

### 2. Quality (높을수록 좋음)

| 통계 | {config_a_name} | {config_b_name} | 차이 |
|------|---------|---------|------|
| **평균** | {stats_a['quality']['mean']:.3f} | {stats_b['quality']['mean']:.3f} | {diff['quality']['absolute']:+.3f} ({diff['quality']['percentage']:+.1f}%) |
| **표준편차** | {stats_a['quality']['stdev']:.3f} | {stats_b['quality']['stdev']:.3f} | - |
| **최소값** | {stats_a['quality']['min']:.3f} | {stats_b['quality']['min']:.3f} | - |
| **최대값** | {stats_a['quality']['max']:.3f} | {stats_b['quality']['max']:.3f} | - |

**원시 데이터**:
- {config_a_name}: {stats_a['quality']['values']}
- {config_b_name}: {stats_b['quality']['values']}

---

### 3. Second Pass Rate (낮을수록 좋음)

| 통계 | {config_a_name} | {config_b_name} | 차이 |
|------|---------|---------|------|
| **평균** | {stats_a['second_pass_rate']['mean']:.3f} | {stats_b['second_pass_rate']['mean']:.3f} | {diff['second_pass_rate']['absolute']:+.3f} ({diff['second_pass_rate']['percentage']:+.1f}%) |
| **표준편차** | {stats_a['second_pass_rate']['stdev']:.3f} | {stats_b['second_pass_rate']['stdev']:.3f} | - |
| **최소값** | {stats_a['second_pass_rate']['min']:.3f} | {stats_b['second_pass_rate']['min']:.3f} | - |
| **최대값** | {stats_a['second_pass_rate']['max']:.3f} | {stats_b['second_pass_rate']['max']:.3f} | - |

**원시 데이터**:
- {config_a_name}: {stats_a['second_pass_rate']['values']}
- {config_b_name}: {stats_b['second_pass_rate']['values']}

---

### 4. Duration (빠를수록 좋음)

| 통계 | {config_a_name} | {config_b_name} | 차이 |
|------|---------|---------|------|
| **평균** | {stats_a['duration']['mean']:.1f}s | {stats_b['duration']['mean']:.1f}s | {diff['duration']['absolute']:+.1f}s ({diff['duration']['percentage']:+.1f}%) |
| **표준편차** | {stats_a['duration']['stdev']:.1f}s | {stats_b['duration']['stdev']:.1f}s | - |
| **최소값** | {stats_a['duration']['min']:.1f}s | {stats_b['duration']['min']:.1f}s | - |
| **최대값** | {stats_a['duration']['max']:.1f}s | {stats_b['duration']['max']:.1f}s | - |

**원시 데이터**:
- {config_a_name}: {[f'{v:.1f}s' for v in stats_a['duration']['values']]}
- {config_b_name}: {[f'{v:.1f}s' for v in stats_b['duration']['values']]}

---

## 🏆 승자 결정

"""

        # 승자 결정
        winners = []

        # Quality (중요도 높음)
        if abs(diff['quality']['absolute']) > 0.05:  # 유의미한 차이
            if diff['quality']['absolute'] > 0:
                winners.append(("**Quality**", config_b_name, f"+{diff['quality']['absolute']:.3f} ({diff['quality']['percentage']:+.1f}%)", "🥇"))
            else:
                winners.append(("**Quality**", config_a_name, f"{diff['quality']['absolute']:.3f} ({diff['quality']['percentage']:+.1f}%)", "🥇"))

        # Confidence
        if abs(diff['confidence']['absolute']) > 0.05:
            if diff['confidence']['absolute'] > 0:
                winners.append(("**Confidence**", config_b_name, f"+{diff['confidence']['absolute']:.3f} ({diff['confidence']['percentage']:+.1f}%)", "🥈"))
            else:
                winners.append(("**Confidence**", config_a_name, f"{diff['confidence']['absolute']:.3f} ({diff['confidence']['percentage']:+.1f}%)", "🥈"))

        # Duration (빠른게 좋음)
        if abs(diff['duration']['absolute']) > 5:  # 5초 이상 차이
            if diff['duration']['absolute'] < 0:  # B가 더 빠름
                winners.append(("**속도**", config_b_name, f"{diff['duration']['absolute']:.1f}s ({diff['duration']['percentage']:+.1f}%)", "🥉"))
            else:
                winners.append(("**속도**", config_a_name, f"+{abs(diff['duration']['absolute']):.1f}s ({abs(diff['duration']['percentage']):.1f}%)", "🥉"))

        if winners:
            report += "| 항목 | 승자 | 개선폭 | 메달 |\n"
            report += "|------|------|--------|------|\n"
            for metric, winner, improvement, medal in winners:
                report += f"| {metric} | {winner} | {improvement} | {medal} |\n"
        else:
            report += "**결과**: 유의미한 차이 없음\n"

        report += "\n---\n\n"

        # 최종 권장사항
        report += "## 💡 권장사항\n\n"

        if diff['quality']['absolute'] > 0.05:
            report += f"✅ **{config_b_name}** 채택 권장\n"
            report += f"- Quality가 {diff['quality']['absolute']:.3f} 향상되었습니다.\n"
        elif diff['quality']['absolute'] < -0.05:
            report += f"✅ **{config_a_name}** 유지 권장\n"
            report += f"- Quality가 {config_b_name}에서 {abs(diff['quality']['absolute']):.3f} 하락했습니다.\n"
        else:
            report += "⚖️ 두 설정 간 유의미한 차이 없음\n"
            report += "- 다른 기준 (속도, 안정성)을 고려하여 선택하세요.\n"

        # 추가 인사이트
        report += "\n### 추가 인사이트\n\n"

        # 안정성 비교 (표준편차 기준)
        if stats_a['quality']['stdev'] < stats_b['quality']['stdev']:
            report += f"- **안정성**: {config_a_name}이 더 안정적 (표준편차 {stats_a['quality']['stdev']:.3f} vs {stats_b['quality']['stdev']:.3f})\n"
        elif stats_b['quality']['stdev'] < stats_a['quality']['stdev']:
            report += f"- **안정성**: {config_b_name}이 더 안정적 (표준편차 {stats_b['quality']['stdev']:.3f} vs {stats_a['quality']['stdev']:.3f})\n"

        # Second Pass 분석
        if diff['second_pass_rate']['absolute'] < -0.1:
            report += f"- **자기교정**: {config_b_name}에서 자기교정 빈도 감소 (좋음)\n"
        elif diff['second_pass_rate']['absolute'] > 0.1:
            report += f"- **자기교정**: {config_b_name}에서 자기교정 빈도 증가 (주의)\n"

        report += "\n---\n\n"
        report += f"**리포트 생성**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**도구**: A/B Testing Automation by 세나\n"

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[Markdown report generated: {output_path}]")


def main():
    """최신 A/B 테스트 결과로 리포트 생성"""
    repo_root = Path(__file__).parent.parent
    outputs_dir = repo_root / "outputs"

    # 최신 ab_test JSON 찾기
    ab_test_files = sorted(outputs_dir.glob("ab_test_*.json"))

    if not ab_test_files:
        print("[ERROR] No A/B test results found")
        return

    latest_file = ab_test_files[-1]
    print(f"[Loading: {latest_file.name}]")

    with open(latest_file, 'r', encoding='utf-8') as f:
        result = json.load(f)

    # 리포트 생성
    report_path = outputs_dir / latest_file.name.replace('.json', '_report.md')

    generator = ABReportGenerator()
    generator.generate_markdown_report(result, report_path)

    print(f"[Report generated: {report_path.name}]")


if __name__ == '__main__':
    main()
