import sys
from pathlib import Path

# Make 'ion-mentoring' directory importable as a flat module root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from orchestrator.intent_router import plan_from_prompt  # type: ignore


def test_deploy_canary_percent_parsing():
    plan = plan_from_prompt("카나리 10% 배포 시작")
    kinds = [a.kind for a in plan.actions]
    assert "deploy_canary" in kinds
    deploy = next(a for a in plan.actions if a.kind == "deploy_canary")
    assert deploy.args.get("percentage") == 10


def test_rollback_parsing():
    plan = plan_from_prompt("롤백 해줘")
    kinds = [a.kind for a in plan.actions]
    assert "rollback_canary" in kinds


def test_probe_profiles():
    assert any(a.args.get("profile") == "gentle" for a in plan_from_prompt("프로브 젠틀").actions if a.kind == "probe")
    assert any(a.args.get("profile") == "normal" for a in plan_from_prompt("probe normal").actions if a.kind == "probe")
    assert any(a.args.get("profile") == "aggressive" for a in plan_from_prompt("프로브 강하게").actions if a.kind == "probe")


def test_tests_and_status_defaults():
    plan = plan_from_prompt("전체 테스트 실행")
    assert any(a.kind == "run_tests" and a.args.get("scope") == "all" for a in plan.actions)

    # default fallback adds status when unknown
    plan2 = plan_from_prompt("무슨 말인지 몰라도 응답은 해줘")
    assert any(a.kind == "check_status" for a in plan2.actions)
