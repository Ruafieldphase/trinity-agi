#!/usr/bin/env python3
"""
Lumen Gateway Metrics Analyzer

Analyzes metrics.csv data and generates comprehensive reports
with statistics, anomaly detection, and visualizations.

Usage:
    python analyze_metrics.py --input logs/metrics.csv --output report.html
    python analyze_metrics.py --input logs/metrics.csv --format json
    python analyze_metrics.py --input logs/metrics.csv --anomalies
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import statistics
import json

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️  Warning: numpy not installed. Some features will be limited.", file=sys.stderr)

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  Warning: matplotlib not installed. Charts will not be generated.", file=sys.stderr)


def load_metrics(csv_path: Path) -> List[Dict]:
    """Load metrics from CSV file"""
    metrics = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamp (column name is 'ts')
            ts = datetime.fromisoformat(row['ts'])
            
            # Parse numeric fields
            metric = {
                'timestamp': ts,
                'ion_health': int(row['ion_health']),
                'ion_response_time_ms': float(row['ion_response_time_ms']),
                'ion_mock_mode': int(row['ion_mock_mode']),
                'ion_confidence': float(row['ion_confidence']),
                'ion_persona': row['ion_persona'],
                'phase_diff': float(row['phase_diff']),
                'entropy_rate': float(row['entropy_rate']),
                'creative_band': float(row['creative_band']),
                'risk_band': float(row['risk_band'])
            }
            metrics.append(metric)
    
    return metrics


def calculate_statistics(values: List[float]) -> Dict:
    """Calculate statistics for a metric"""
    if not values:
        return {}
    
    stats = {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0.0
    }
    
    if HAS_NUMPY:
        arr = np.array(values)
        stats['p25'] = np.percentile(arr, 25)
        stats['p75'] = np.percentile(arr, 75)
        stats['p95'] = np.percentile(arr, 95)
        stats['p99'] = np.percentile(arr, 99)
    
    return stats


def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[int]:
    """Detect outliers using z-score method"""
    if len(values) < 3:
        return []
    
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    
    if stdev == 0:
        return []
    
    anomalies = []
    for i, val in enumerate(values):
        z_score = abs((val - mean) / stdev)
        if z_score > threshold:
            anomalies.append(i)
    
    return anomalies


def analyze_metrics(metrics: List[Dict]) -> Dict:
    """Analyze metrics and generate report data"""
    if not metrics:
        return {'error': 'No metrics to analyze'}
    
    # Extract time series
    timestamps = [m['timestamp'] for m in metrics]
    
    # Numeric metrics
    numeric_fields = [
        'ion_response_time_ms',
        'ion_confidence',
        'phase_diff',
        'entropy_rate',
        'creative_band',
        'risk_band'
    ]
    
    analysis = {
        'summary': {
            'total_records': len(metrics),
            'time_range': {
                'start': timestamps[0].isoformat(),
                'end': timestamps[-1].isoformat(),
                'duration_seconds': (timestamps[-1] - timestamps[0]).total_seconds()
            }
        },
        'statistics': {},
        'anomalies': {},
        'health': {}
    }
    
    # Calculate statistics for each metric
    for field in numeric_fields:
        values = [m[field] for m in metrics]
        analysis['statistics'][field] = calculate_statistics(values)
        
        # Detect anomalies
        anomaly_indices = detect_anomalies(values)
        if anomaly_indices:
            analysis['anomalies'][field] = {
                'count': len(anomaly_indices),
                'indices': anomaly_indices[:10],  # First 10
                'values': [values[i] for i in anomaly_indices[:10]]
            }
    
    # Health analysis
    ion_health_values = [m['ion_health'] for m in metrics]
    mock_mode_values = [m['ion_mock_mode'] for m in metrics]
    
    analysis['health'] = {
        'uptime_percent': (sum(ion_health_values) / len(ion_health_values)) * 100,
        'mock_mode_percent': (sum(mock_mode_values) / len(mock_mode_values)) * 100,
        'total_downtime_records': ion_health_values.count(0),
        'total_mock_records': mock_mode_values.count(1)
    }
    
    # Persona distribution
    personas = [m['ion_persona'] for m in metrics]
    persona_counts = {}
    for p in set(personas):
        persona_counts[p] = personas.count(p)
    
    analysis['personas'] = persona_counts
    
    return analysis


def generate_html_report(analysis: Dict, metrics: List[Dict], output_path: Path):
    """Generate HTML report with charts"""
    html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lumen Gateway Metrics Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 14px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .warning {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .danger {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .success {{
            background: #d4edda;
            border-left-color: #28a745;
        }}
        .chart-container {{
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌙 Lumen Gateway Metrics Report</h1>
        
        <div class="stat-grid">
            <div class="stat-card">
                <h3>Total Records</h3>
                <div class="stat-value">{total_records}</div>
                <div class="stat-label">Collected</div>
            </div>
            <div class="stat-card {uptime_class}">
                <h3>ION API Uptime</h3>
                <div class="stat-value">{uptime:.1f}%</div>
                <div class="stat-label">{downtime_records} downtime records</div>
            </div>
            <div class="stat-card {mock_class}">
                <h3>Real AI Mode</h3>
                <div class="stat-value">{real_ai:.1f}%</div>
                <div class="stat-label">{mock_records} mock records</div>
            </div>
            <div class="stat-card">
                <h3>Duration</h3>
                <div class="stat-value">{duration_min:.0f}</div>
                <div class="stat-label">minutes</div>
            </div>
        </div>
        
        <h2>📊 Performance Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Min</th>
                <th>Max</th>
                <th>Mean</th>
                <th>Median</th>
                <th>StdDev</th>
            </tr>
            {stats_rows}
        </table>
        
        <h2>⚠️ Anomalies Detected</h2>
        {anomalies_section}
        
        <h2>👥 Persona Distribution</h2>
        <table>
            <tr>
                <th>Persona</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            {persona_rows}
        </table>
        
        <div class="footer">
            Generated: {timestamp}<br>
            Lumen Gateway v1.0 | ION API Integration
        </div>
    </div>
</body>
</html>
    """
    
    # Format statistics rows
    stats_rows = []
    for field, stats in analysis['statistics'].items():
        row = f"""
            <tr>
                <td><strong>{field}</strong></td>
                <td>{stats['min']:.2f}</td>
                <td>{stats['max']:.2f}</td>
                <td>{stats['mean']:.2f}</td>
                <td>{stats['median']:.2f}</td>
                <td>{stats['stdev']:.2f}</td>
            </tr>
        """
        stats_rows.append(row)
    
    # Format anomalies
    if analysis['anomalies']:
        anomalies_html = "<ul>"
        for field, anom in analysis['anomalies'].items():
            anomalies_html += f"<li><strong>{field}</strong>: {anom['count']} anomalies detected</li>"
        anomalies_html += "</ul>"
    else:
        anomalies_html = "<p>✅ No anomalies detected</p>"
    
    # Format persona rows
    persona_rows = []
    total = analysis['summary']['total_records']
    for persona, count in analysis['personas'].items():
        pct = (count / total) * 100
        persona_rows.append(f"""
            <tr>
                <td>{persona}</td>
                <td>{count}</td>
                <td>{pct:.1f}%</td>
            </tr>
        """)
    
    # Determine classes
    uptime = analysis['health']['uptime_percent']
    uptime_class = 'success' if uptime >= 99 else 'warning' if uptime >= 95 else 'danger'
    
    mock_pct = analysis['health']['mock_mode_percent']
    mock_class = 'success' if mock_pct == 0 else 'warning' if mock_pct < 5 else 'danger'
    
    # Render HTML
    html = html_template.format(
        total_records=analysis['summary']['total_records'],
        uptime=uptime,
        uptime_class=uptime_class,
        downtime_records=analysis['health']['total_downtime_records'],
        real_ai=100 - mock_pct,
        mock_class=mock_class,
        mock_records=analysis['health']['total_mock_records'],
        duration_min=analysis['summary']['time_range']['duration_seconds'] / 60,
        stats_rows=''.join(stats_rows),
        anomalies_section=anomalies_html,
        persona_rows=''.join(persona_rows),
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze Lumen Gateway metrics')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file path')
    parser.add_argument('--output', '-o', default='report.html', help='Output file path')
    parser.add_argument('--format', '-f', choices=['html', 'json'], default='html', help='Output format')
    parser.add_argument('--anomalies', '-a', action='store_true', help='Show only anomalies')
    
    args = parser.parse_args()
    
    # Load metrics
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📂 Loading metrics from: {input_path}")
    metrics = load_metrics(input_path)
    print(f"✅ Loaded {len(metrics)} records")
    
    # Analyze
    print("📊 Analyzing metrics...")
    analysis = analyze_metrics(metrics)
    
    # Output
    output_path = Path(args.output)
    
    if args.format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ JSON report generated: {output_path}")
    else:
        generate_html_report(analysis, metrics, output_path)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Analysis Summary")
    print("=" * 50)
    print(f"Total Records:    {analysis['summary']['total_records']}")
    print(f"ION API Uptime:   {analysis['health']['uptime_percent']:.1f}%")
    print(f"Real AI Mode:     {100 - analysis['health']['mock_mode_percent']:.1f}%")
    print(f"Duration:         {analysis['summary']['time_range']['duration_seconds'] / 60:.1f} minutes")
    print("=" * 50)


if __name__ == '__main__':
    main()
