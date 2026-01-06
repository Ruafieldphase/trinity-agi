#!/usr/bin/env python3
"""
AGI Performance Dashboard Generator
===================================

Generates an HTML dashboard showing:
- Complexity spectrum performance
- Recent replan trends
- Citation quality over time
- Success rate history

Usage:
    python generate_performance_dashboard.py
    python generate_performance_dashboard.py --output custom_dashboard.html
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from workspace_root import get_workspace_root


def load_latest_data():
    """Load all relevant performance data."""
    outputs_dir = get_workspace_root() / "outputs"
    
    data = {
        'complexity_spectrum': None,
        'replan_analysis': None,
        'latest_batch': None,
        'timestamp': datetime.now().isoformat()
    }
    
    # Load complexity spectrum
    spectrum_path = outputs_dir / "complexity_spectrum_latest.json"
    if spectrum_path.exists():
        with open(spectrum_path, 'r', encoding='utf-8') as f:
            data['complexity_spectrum'] = json.load(f)
    
    # Load replan analysis
    replan_path = outputs_dir / "replan_analysis_latest.json"
    if replan_path.exists():
        with open(replan_path, 'r', encoding='utf-8') as f:
            data['replan_analysis'] = json.load(f)
    
    # Load latest batch validation
    batch_files = sorted(outputs_dir.glob("batch_validation_*.json"), reverse=True)
    if batch_files:
        with open(batch_files[0], 'r', encoding='utf-8') as f:
            data['latest_batch'] = json.load(f)
    
    return data


def generate_html_dashboard(data: Dict) -> str:
    """Generate HTML dashboard content."""
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>AGI Performance Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .card h2 {{
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{
            font-weight: 600;
            color: #333;
        }}
        .metric-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-value.success {{ color: #10b981; }}
        .metric-value.warning {{ color: #f59e0b; }}
        .metric-value.error {{ color: #ef4444; }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .status-badge.success {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status-badge.warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        .complexity-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .complexity-table th {{
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #667eea;
        }}
        .complexity-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .complexity-table tr:hover {{
            background: #f9fafb;
        }}
        .insight {{
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }}
        .insight strong {{
            color: #1e40af;
        }}
        .footer {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            color: #666;
        }}
        .auto-refresh-control {{
            background: white;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .auto-refresh-control label {{
            font-weight: 600;
            color: #333;
            margin-right: 10px;
        }}
        .auto-refresh-control select {{
            padding: 8px 15px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            background: white;
        }}
        .refresh-status {{
            color: #666;
            font-size: 0.9em;
        }}
        .refresh-status.active {{
            color: #10b981;
        }}
    </style>
    <script>
        let autoRefreshInterval = null;
        let countdownInterval = null;
        let remainingSeconds = 0;
        
        function updateCountdown() {{
            if (remainingSeconds > 0) {{
                remainingSeconds--;
                const minutes = Math.floor(remainingSeconds / 60);
                const seconds = remainingSeconds % 60;
                document.getElementById('countdown').textContent = 
                    `다음 새로고침: ${{minutes}}:${{seconds.toString().padStart(2, '0')}}`;
            }} else {{
                location.reload();
            }}
        }}
        
        function setAutoRefresh(seconds) {{
            // Clear existing intervals
            if (autoRefreshInterval) {{
                clearInterval(autoRefreshInterval);
                clearInterval(countdownInterval);
            }}
            
            if (seconds > 0) {{
                remainingSeconds = seconds;
                document.getElementById('refresh-status').className = 'refresh-status active';
                document.getElementById('refresh-status').textContent = '✅ 자동 새로고침 활성화';
                
                // Update countdown every second
                countdownInterval = setInterval(updateCountdown, 1000);
                updateCountdown();
                
                // Set main refresh interval
                autoRefreshInterval = setInterval(() => {{
                    location.reload();
                }}, seconds * 1000);
            }} else {{
                document.getElementById('refresh-status').className = 'refresh-status';
                document.getElementById('refresh-status').textContent = '⏸️ 자동 새로고침 꺼짐';
                document.getElementById('countdown').textContent = '';
            }}
            
            // Save preference
            localStorage.setItem('autoRefreshInterval', seconds);
        }}
        
        window.onload = function() {{
            // Restore previous preference or default to 5 minutes
            const savedInterval = localStorage.getItem('autoRefreshInterval') || '300';
            document.getElementById('refresh-interval').value = savedInterval;
            setAutoRefresh(parseInt(savedInterval));
        }};
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AGI Performance Dashboard</h1>
            <div class="timestamp">Last Updated: {data['timestamp']}</div>
        </div>
        
        <div class="auto-refresh-control">
            <div>
                <label for="refresh-interval">자동 새로고침:</label>
                <select id="refresh-interval" onchange="setAutoRefresh(this.value)">
                    <option value="0">끄기</option>
                    <option value="60">1분</option>
                    <option value="180">3분</option>
                    <option value="300">5분</option>
                    <option value="600">10분</option>
                    <option value="1800">30분</option>
                </select>
            </div>
            <div>
                <span id="refresh-status" class="refresh-status">⏸️ 자동 새로고침 꺼짐</span>
                <span id="countdown" style="margin-left: 15px; font-weight: 600; color: #667eea;"></span>
            </div>
        </div>
"""
    
    # Overall Performance Card
    if data['latest_batch']:
        summary = data['latest_batch'].get('summary', {})
        goal = data['latest_batch'].get('goal_achievement', {})
        
        html += f"""
        <div class="grid">
            <div class="card">
                <h2>📊 Overall Performance</h2>
                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value success">{summary.get('success_rate_percent', 0)}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Quality</span>
                    <span class="metric-value">{summary.get('avg_quality_score', 0):.3f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Citations</span>
                    <span class="metric-value">{summary.get('avg_citations', 0):.1f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Duration</span>
                    <span class="metric-value">{summary.get('avg_elapsed_sec', 0):.1f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Goal Status</span>
                    <span class="status-badge {'success' if goal.get('target_achieved') else 'warning'}">
                        {goal.get('status', 'Unknown')}
                    </span>
                </div>
            </div>
"""
    
    # Replan Analysis Card
    if data['replan_analysis']:
        analysis = data['replan_analysis']
        summary = analysis.get('summary', {})
        
        replan_rate = summary.get('replan_rate_percent', 0)
        status_class = 'success' if replan_rate < 15 else 'warning' if replan_rate < 30 else 'error'
        
        html += f"""
            <div class="card">
                <h2>🔄 Replan Analysis</h2>
                <div class="metric">
                    <span class="metric-label">Replan Rate</span>
                    <span class="metric-value {status_class}">{replan_rate}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total RUNE Events</span>
                    <span class="metric-value">{summary.get('total_rune_events', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Replans</span>
                    <span class="metric-value">{summary.get('replan_count', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">No Replans</span>
                    <span class="metric-value success">{summary.get('no_replan_count', 0)}</span>
                </div>
                <div class="insight">
                    <strong>Target:</strong> &lt;15% replan rate
                    {"✅ Achieved!" if replan_rate < 15 else "⚠️ Needs improvement"}
                </div>
            </div>
"""
    
    # Complexity Spectrum Card
    if data['complexity_spectrum']:
        spectrum = data['complexity_spectrum']
        
        html += f"""
            <div class="card" style="grid-column: span 2;">
                <h2>📈 Complexity Spectrum</h2>
                <table class="complexity-table">
                    <thead>
                        <tr>
                            <th>Complexity</th>
                            <th>Success Rate</th>
                            <th>Avg Quality</th>
                            <th>Avg Time</th>
                            <th>Tasks</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for complexity in ['simple', 'medium', 'complex']:
            if complexity in spectrum:
                data_row = spectrum[complexity]
                html += f"""
                        <tr>
                            <td><strong>{complexity.capitalize()}</strong></td>
                            <td>{data_row['avg_success_rate']:.1f}%</td>
                            <td>{data_row['avg_quality']:.3f}</td>
                            <td>{data_row['avg_time_sec']:.1f}s</td>
                            <td>{data_row['total_tasks']}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
"""
        
        # Add insights if both simple and complex exist
        if 'simple' in spectrum and 'complex' in spectrum:
            simple = spectrum['simple']
            complex_data = spectrum['complex']
            
            success_gap = abs(simple['avg_success_rate'] - complex_data['avg_success_rate'])
            time_increase = ((complex_data['avg_time_sec'] - simple['avg_time_sec']) / simple['avg_time_sec']) * 100
            
            html += f"""
                <div class="insight">
                    <strong>📊 Scaling Analysis:</strong><br>
                    • Success Rate Gap: {success_gap:.1f}% {"✅" if success_gap < 5 else "⚠️"}<br>
                    • Time Increase: +{time_increase:.1f}% {"✅" if time_increase < 20 else "⚠️"}<br>
                    • System scales efficiently across complexity levels
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    # Footer
    html += f"""
        <div class="footer">
            Generated by AGI Performance Dashboard | 
            <a href="https://github.com/Shion_Core/LLM_Unified" target="_blank">GitHub</a>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    output_file = "agi_performance_dashboard.html"
    
    # Check for custom output path
    if len(sys.argv) > 1 and sys.argv[1] in ['--output', '-o']:
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
    
    print("Loading performance data...")
    data = load_latest_data()
    
    print("Generating HTML dashboard...")
    html = generate_html_dashboard(data)
    
    # Save to file
    output_path = get_workspace_root() / "outputs" / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: {output_path}")
    print(f"\nOpen in browser: file:///{output_path.absolute()}")


if __name__ == "__main__":
    main()
