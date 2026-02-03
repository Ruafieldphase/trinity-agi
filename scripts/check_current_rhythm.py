import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fdo_agi_repo.orchestrator.rhythm_controller import estimate_signals, map_to_params
import json

signals = estimate_signals()
params, hint = map_to_params(signals)

print(json.dumps({
    "signals": signals,
    "params": params,
    "hint": hint
}, indent=2))
