#!/usr/bin/env python3
"""
Phase 9: Full-Stack Integration Dashboard Generator

전체 시스템 상태를 실시간으로 시각화하는 HTML 대시보드 생성
- Resonance 정책 상태
- BQI 학습 모델 상태
- Gateway 최적화 메트릭
- YouTube 학습 현황
- 실시간 피드백 루프 상태
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Workspace root
WORKSPACE = Path(__file__).parent.parent.parent
OUTPUTS = WORKSPACE / "outputs"


def load_json_safe(path: Path, default: Any = None) -> Any:
    """JSON 파일 안전하게 로드"""
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return default or {}
    except Exception as e:
        print(f"⚠️  {path.name} 로드 실패: {e}")
        return default or {}


def load_orchestrator_state() -> Dict[str, Any]:
    """오케스트레이터 상태 로드"""
    state = load_json_safe(OUTPUTS / "full_stack_orchestrator_state.json")
    return {
        "status": state.get("status", "unknown"),
        "last_update": state.get("last_update", "N/A"),
        "events_processed": len(state.get("events_processed", [])),
        "components": state.get("components", {}),
    }


def load_feedback_loop_state() -> Dict[str, Any]:
    """피드백 루프 상태 로드"""
    # 최근 24시간 로그 분석
    log_path = OUTPUTS / "realtime_feedback_loop.jsonl"
    if not log_path.exists():
        return {"status": "not_started", "cycles": 0}
    
    lines = []
    try:
        with open(log_path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"⚠️  피드백 루프 로그 파싱 실패: {e}")
    
    # 최근 1시간 데이터만
    now = datetime.now()
    recent = [
        l for l in lines
        if (now - datetime.fromisoformat(l.get("timestamp", "2000-01-01"))).total_seconds() < 3600
    ]
    
    return {
        "status": "active" if recent else "idle",
        "cycles": len(recent),
        "last_cycle": recent[-1] if recent else None,
    }


def load_bqi_models() -> Dict[str, Any]:
    """BQI 모델 상태 로드"""
    patterns = load_json_safe(OUTPUTS / "bqi_pattern_model.json")
    persona = load_json_safe(OUTPUTS / "binoche_persona.json")
    weights = load_json_safe(OUTPUTS / "ensemble_weights.json")
    
    return {
        "patterns_loaded": bool(patterns.get("patterns")),
        "persona_loaded": bool(persona.get("traits")),
        "weights_loaded": bool(weights.get("weights")),
        "last_update": max(
            patterns.get("last_updated", ""),
            persona.get("last_updated", ""),
            weights.get("last_updated", ""),
        ),
    }


def load_gateway_metrics() -> Dict[str, Any]:
    """Gateway 최적화 메트릭 로드"""
    log_path = OUTPUTS / "gateway_optimization_log.jsonl"
    if not log_path.exists():
        return {"status": "not_running", "samples": 0}
    
    lines = []
    try:
        with open(log_path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
    except Exception:
        pass
    
    if not lines:
        return {"status": "no_data", "samples": 0}
    
    recent = lines[-100:]  # 최근 100개
    avg_latency = sum(s.get("latency_ms", 0) for s in recent) / len(recent) if recent else 0
    
    return {
        "status": "active",
        "samples": len(lines),
        "avg_latency_ms": round(avg_latency, 1),
        "last_check": lines[-1].get("timestamp", "N/A"),
    }


def load_youtube_index() -> Dict[str, Any]:
    """YouTube 학습 인덱스 로드"""
    index = load_json_safe(OUTPUTS / "youtube_learner_index.json")
    return {
        "videos_learned": len(index.get("videos", [])),
        "last_update": index.get("generated_at", "N/A"),
        "status": "active" if index.get("videos") else "empty",
    }


def load_resonance_policy() -> Dict[str, Any]:
    """Resonance 정책 상태 로드"""
    config_path = WORKSPACE / "fdo_agi_repo" / "config" / "resonance_config.json"
    config = load_json_safe(config_path)
    
    return {
        "mode": config.get("mode", "unknown"),
        "policy": config.get("policy", "unknown"),
        "status": "active" if config.get("enabled") else "inactive",
    }


def generate_html_dashboard() -> str:
    """HTML 대시보드 생성"""
    # 모든 컴포넌트 상태 로드
    orch = load_orchestrator_state()
    feedback = load_feedback_loop_state()
    bqi = load_bqi_models()
    gateway = load_gateway_metrics()
    youtube = load_youtube_index()
    resonance = load_resonance_policy()
    
    # 전체 시스템 상태 판단
    all_ok = all([
        orch["status"] == "initialized",
        feedback["status"] == "active",
        bqi["patterns_loaded"],
        gateway["status"] == "active",
    ])
    system_status = "🟢 ALL GREEN" if all_ok else "🟡 PARTIAL"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 9: Full-Stack Integration Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            font-size: 1.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }}
        .card h2 {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{
            color: #aaa;
            font-size: 0.9em;
        }}
        .metric-value {{
            font-weight: bold;
            color: #fff;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .status-active {{ background: #10b981; color: white; }}
        .status-idle {{ background: #f59e0b; color: white; }}
        .status-error {{ background: #ef4444; color: white; }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        .flow-diagram {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            margin-top: 20px;
        }}
        .flow-node {{
            text-align: center;
            padding: 20px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 10px;
            border: 2px solid #667eea;
        }}
        .flow-arrow {{
            font-size: 2em;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Phase 9: Full-Stack Integration</h1>
            <div class="status">{system_status}</div>
            <div class="timestamp">생성 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")}</div>
            <div class="timestamp">통합 컴포넌트: Resonance + BQI + Gateway + YouTube</div>
        </header>

        <div class="grid">
            <!-- Orchestrator -->
            <div class="card">
                <h2>🎯 통합 오케스트레이터</h2>
                <div class="metric">
                    <span class="metric-label">상태</span>
                    <span class="status-badge status-{orch['status']}">{orch['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">처리된 이벤트</span>
                    <span class="metric-value">{orch['events_processed']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">마지막 업데이트</span>
                    <span class="metric-value">{orch['last_update']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">활성 컴포넌트</span>
                    <span class="metric-value">{len(orch['components'])}</span>
                </div>
            </div>

            <!-- Feedback Loop -->
            <div class="card">
                <h2>🔄 실시간 피드백 루프</h2>
                <div class="metric">
                    <span class="metric-label">상태</span>
                    <span class="status-badge status-{feedback['status']}">{feedback['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">최근 1시간 사이클</span>
                    <span class="metric-value">{feedback['cycles']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">마지막 사이클</span>
                    <span class="metric-value">{feedback.get('last_cycle', {}).get('timestamp', 'N/A') if feedback.get('last_cycle') else 'N/A'}</span>
                </div>
            </div>

            <!-- BQI Models -->
            <div class="card">
                <h2>🧠 BQI 학습 모델</h2>
                <div class="metric">
                    <span class="metric-label">패턴 모델</span>
                    <span class="status-badge status-{'active' if bqi['patterns_loaded'] else 'idle'}">
                        {'✓ LOADED' if bqi['patterns_loaded'] else '✗ NOT LOADED'}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Persona 모델</span>
                    <span class="status-badge status-{'active' if bqi['persona_loaded'] else 'idle'}">
                        {'✓ LOADED' if bqi['persona_loaded'] else '✗ NOT LOADED'}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Ensemble 가중치</span>
                    <span class="status-badge status-{'active' if bqi['weights_loaded'] else 'idle'}">
                        {'✓ LOADED' if bqi['weights_loaded'] else '✗ NOT LOADED'}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">마지막 업데이트</span>
                    <span class="metric-value">{bqi['last_update']}</span>
                </div>
            </div>

            <!-- Gateway Optimizer -->
            <div class="card">
                <h2>⚡ Gateway 최적화</h2>
                <div class="metric">
                    <span class="metric-label">상태</span>
                    <span class="status-badge status-{gateway['status']}">{gateway['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">수집된 샘플</span>
                    <span class="metric-value">{gateway['samples']:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">평균 레이턴시</span>
                    <span class="metric-value">{gateway.get('avg_latency_ms', 0)} ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">마지막 체크</span>
                    <span class="metric-value">{gateway['last_check']}</span>
                </div>
            </div>

            <!-- YouTube Learner -->
            <div class="card">
                <h2>📺 YouTube 학습</h2>
                <div class="metric">
                    <span class="metric-label">상태</span>
                    <span class="status-badge status-{youtube['status']}">{youtube['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">학습된 동영상</span>
                    <span class="metric-value">{youtube['videos_learned']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">마지막 업데이트</span>
                    <span class="metric-value">{youtube['last_update']}</span>
                </div>
            </div>

            <!-- Resonance Policy -->
            <div class="card">
                <h2>🌀 Resonance 정책</h2>
                <div class="metric">
                    <span class="metric-label">상태</span>
                    <span class="status-badge status-{resonance['status']}">{resonance['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">모드</span>
                    <span class="metric-value">{resonance['mode']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">정책</span>
                    <span class="metric-value">{resonance['policy']}</span>
                </div>
            </div>
        </div>

        <!-- Data Flow Diagram -->
        <div class="card full-width">
            <h2>📊 데이터 흐름</h2>
            <div class="flow-diagram">
                <div class="flow-node">
                    <div style="font-size: 2em;">⚡</div>
                    <div>Gateway</div>
                    <div style="font-size: 0.8em; color: #aaa;">레이턴시 측정</div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div style="font-size: 2em;">🧠</div>
                    <div>BQI</div>
                    <div style="font-size: 0.8em; color: #aaa;">패턴 학습</div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div style="font-size: 2em;">🌀</div>
                    <div>Resonance</div>
                    <div style="font-size: 0.8em; color: #aaa;">정책 조정</div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div style="font-size: 2em;">🔄</div>
                    <div>Feedback</div>
                    <div style="font-size: 0.8em; color: #aaa;">자동 최적화</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 5분마다 자동 새로고침
        setTimeout(() => location.reload(), 5 * 60 * 1000);
    </script>
</body>
</html>"""
    
    return html


def main():
    """메인 실행"""
    print("\n🚀 Phase 9: Full-Stack Integration Dashboard 생성 중...\n")
    
    # HTML 생성
    html = generate_html_dashboard()
    
    # 저장
    output_path = OUTPUTS / "fullstack_integration_dashboard.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 대시보드 생성 완료: {output_path}")
    print(f"\n📊 브라우저에서 열기:")
    print(f"   {output_path.as_uri()}\n")


if __name__ == "__main__":
    main()
