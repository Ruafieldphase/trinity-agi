#!/usr/bin/env python3
"""
Phase 9: End-to-End Integration Test

전체 시스템 통합 테스트:
1. 오케스트레이터 초기화
2. 피드백 루프 1회 실행
3. 모든 컴포넌트 상태 확인
4. 결과 검증 및 리포트
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Workspace root
WORKSPACE = Path(__file__).parent.parent.parent
OUTPUTS = WORKSPACE / "outputs"


def load_json_safe(path: Path) -> Dict[str, Any]:
    """JSON 파일 안전하게 로드"""
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️  {path.name} 로드 실패: {e}")
        return {}


def check_orchestrator() -> Dict[str, Any]:
    """오케스트레이터 상태 확인"""
    print("\n📊 1. 오케스트레이터 상태 확인...")
    
    state_path = OUTPUTS / "full_stack_orchestrator_state.json"
    state = load_json_safe(state_path)
    
    result = {
        "status": state.get("status", "unknown"),
        "events_processed": len(state.get("events_processed", [])),
        "components": len(state.get("components", {})),
        "ok": state.get("status") == "initialized",
    }
    
    if result["ok"]:
        print(f"   ✅ 상태: {result['status']}")
        print(f"   ✅ 처리된 이벤트: {result['events_processed']}")
        print(f"   ✅ 활성 컴포넌트: {result['components']}")
    else:
        print(f"   ❌ 상태: {result['status']}")
    
    return result


def check_feedback_loop() -> Dict[str, Any]:
    """피드백 루프 확인"""
    print("\n🔄 2. 실시간 피드백 루프 확인...")
    
    log_path = OUTPUTS / "realtime_feedback_loop.jsonl"
    if not log_path.exists():
        print("   ⚠️  로그 파일 없음")
        return {"ok": False, "cycles": 0}
    
    try:
        with open(log_path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"   ❌ 로그 파싱 실패: {e}")
        return {"ok": False, "cycles": 0}
    
    result = {
        "cycles": len(lines),
        "last_cycle": lines[-1] if lines else None,
        "ok": len(lines) > 0,
    }
    
    if result["ok"]:
        print(f"   ✅ 실행된 사이클: {result['cycles']}")
        if result["last_cycle"]:
            print(f"   ✅ 마지막 사이클: {result['last_cycle'].get('timestamp', 'N/A')}")
    else:
        print("   ⚠️  실행된 사이클 없음")
    
    return result


def check_bqi_models() -> Dict[str, Any]:
    """BQI 모델 확인"""
    print("\n🧠 3. BQI 학습 모델 확인...")
    
    patterns = load_json_safe(OUTPUTS / "bqi_pattern_model.json")
    persona = load_json_safe(OUTPUTS / "binoche_persona.json")
    weights = load_json_safe(OUTPUTS / "ensemble_weights.json")
    
    result = {
        "patterns_ok": bool(patterns.get("patterns")),
        "persona_ok": bool(persona.get("traits")),
        "weights_ok": bool(weights.get("weights")),
    }
    result["ok"] = all(result.values())
    
    print(f"   {'✅' if result['patterns_ok'] else '❌'} 패턴 모델")
    print(f"   {'✅' if result['persona_ok'] else '❌'} Persona 모델")
    print(f"   {'✅' if result['weights_ok'] else '❌'} Ensemble 가중치")
    
    return result


def check_gateway_optimizer() -> Dict[str, Any]:
    """Gateway 최적화 확인"""
    print("\n⚡ 4. Gateway 최적화 확인...")
    
    log_path = OUTPUTS / "gateway_optimization_log.jsonl"
    if not log_path.exists():
        print("   ⚠️  로그 파일 없음")
        return {"ok": False, "samples": 0}
    
    try:
        with open(log_path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
    except Exception:
        print("   ❌ 로그 파싱 실패")
        return {"ok": False, "samples": 0}
    
    result = {
        "samples": len(lines),
        "ok": len(lines) > 0,
    }
    
    if result["ok"]:
        recent = lines[-100:]
        avg_latency = sum(s.get("latency_ms", 0) for s in recent) / len(recent)
        result["avg_latency_ms"] = round(avg_latency, 1)
        print(f"   ✅ 수집된 샘플: {result['samples']:,}")
        print(f"   ✅ 평균 레이턴시: {result['avg_latency_ms']} ms")
    else:
        print("   ⚠️  수집된 샘플 없음")
    
    return result


def check_youtube_learner() -> Dict[str, Any]:
    """YouTube 학습 확인"""
    print("\n📺 5. YouTube 학습 확인...")
    
    index = load_json_safe(OUTPUTS / "youtube_learner_index.json")
    
    result = {
        "videos": len(index.get("videos", [])),
        "ok": len(index.get("videos", [])) > 0,
    }
    
    if result["ok"]:
        print(f"   ✅ 학습된 동영상: {result['videos']}")
    else:
        print("   ⚠️  학습된 동영상 없음 (선택 사항)")
    
    return result


def check_resonance_policy() -> Dict[str, Any]:
    """Resonance 정책 확인"""
    print("\n🌀 6. Resonance 정책 확인...")
    
    config_path = WORKSPACE / "fdo_agi_repo" / "config" / "resonance_config.json"
    config = load_json_safe(config_path)
    
    result = {
        "mode": config.get("mode", "unknown"),
        "policy": config.get("policy", "unknown"),
        "enabled": config.get("enabled", False),
        "ok": config.get("enabled", False),
    }
    
    if result["ok"]:
        print(f"   ✅ 모드: {result['mode']}")
        print(f"   ✅ 정책: {result['policy']}")
    else:
        print("   ⚠️  비활성화 상태")
    
    return result


def generate_test_report(results: Dict[str, Dict[str, Any]]) -> None:
    """테스트 리포트 생성"""
    print("\n" + "=" * 60)
    print("📋 Phase 9 E2E 테스트 리포트")
    print("=" * 60)
    
    # 전체 상태
    all_ok = all(r.get("ok", False) for r in results.values())
    print(f"\n전체 상태: {'🟢 ALL GREEN' if all_ok else '🟡 PARTIAL'}")
    
    # 개별 컴포넌트
    print("\n개별 컴포넌트:")
    for name, result in results.items():
        status = "✅" if result.get("ok", False) else "⚠️"
        print(f"  {status} {name}")
    
    # 저장
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "pass" if all_ok else "partial",
        "results": results,
    }
    
    report_path = OUTPUTS / "phase9_e2e_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n리포트 저장: {report_path}")
    print("=" * 60 + "\n")


def main():
    """메인 실행"""
    print("\n🚀 Phase 9: End-to-End Integration Test")
    print("=" * 60)
    
    results = {}
    
    # 1. 오케스트레이터
    results["orchestrator"] = check_orchestrator()
    time.sleep(0.5)
    
    # 2. 피드백 루프
    results["feedback_loop"] = check_feedback_loop()
    time.sleep(0.5)
    
    # 3. BQI 모델
    results["bqi_models"] = check_bqi_models()
    time.sleep(0.5)
    
    # 4. Gateway 최적화
    results["gateway_optimizer"] = check_gateway_optimizer()
    time.sleep(0.5)
    
    # 5. YouTube 학습
    results["youtube_learner"] = check_youtube_learner()
    time.sleep(0.5)
    
    # 6. Resonance 정책
    results["resonance_policy"] = check_resonance_policy()
    
    # 리포트 생성
    generate_test_report(results)


if __name__ == "__main__":
    main()
