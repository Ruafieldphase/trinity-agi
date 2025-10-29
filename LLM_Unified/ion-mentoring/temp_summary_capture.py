import json
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

from persona_system.pipeline_optimized import get_optimized_pipeline
from persona_system.models import ChatContext

pipeline = get_optimized_pipeline()

ctx = ChatContext(
    user_id="demo-user",
    session_id="sess-123",
    message_history=[
        {"role": "user", "content": "어제 회의에서 정리한 액션 아이템을 다시 확인하고 싶어."},
        {"role": "assistant", "content": "좋아요. 주요 액션 아이템은 일정 재조정과 리스크 점검이었어요."},
    ],
    custom_context={},
)

prompt_options = {"max_bullets": 6, "max_chars": 400}

records = []


def run_call(label, user_input, mutate_history=True):
    if mutate_history:
        ctx.add_message("user", user_input)
    resp = pipeline.process(
        user_input=user_input,
        resonance_key="calm-medium-learning",
        context=ctx,
        prompt_mode="summary_light",
        prompt_options=prompt_options,
        use_cache=True,
    )
    running_info = resp.metadata.get("running_summary", {})
    records.append({
        "label": label,
        "user_input": user_input,
        "cached": resp.metadata.get("cached"),
        "execution_time_ms": resp.execution_time_ms,
        "running_summary_len": running_info.get("running_summary_len"),
        "running_summary_bullets": running_info.get("running_summary_bullets"),
        "cache_key": resp.metadata.get("cache_key"),
    })
    if mutate_history:
        ctx.add_message("assistant", resp.content[:160])


run_call("initial", "프로젝트 진행 상황을 3줄로 요약해줄래?", mutate_history=True)
run_call("cached-repeat", "프로젝트 진행 상황을 3줄로 요약해줄래?", mutate_history=False)
run_call("follow-up", "어제 결정된 일정 변경 사항까지 반영해서 5줄로 정리해줘.", mutate_history=True)

output_path = "summary_light_sample_metrics.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"records": records}, f, ensure_ascii=False, indent=2)

print(output_path)
