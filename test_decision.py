from scripts.rhythm_think import RhythmThinker
import sys

# Mock
thinker = RhythmThinker()
state = {"score": 55, "status": "UNKNOWN", "atp": 100}
feeling = {"tag": "neutral"}
bohm_signal = {
    "interpretation": {
        "implicate_explicate_balance": "Explicate 우세 - 정보가 많이 드러남 (펼침 > 접힘)"
    }
}

print("--- Testing Decision Logic ---")
decision, action = thinker.make_decision(state, feeling, bohm_signal)
print(f"Decision: {decision}")
print(f"Action: {action}")
