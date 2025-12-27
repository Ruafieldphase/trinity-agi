import json
from pathlib import Path

try:
    p = Path("outputs/bohm_analysis_latest.json")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    interp = data.get("interpretation", {})
    balance = interp.get("implicate_explicate_balance", "UNKNOWN")
    
    print(f"Balance String: '{balance}'")
    print(f"Contains 'Explicate 우세': {'Explicate 우세' in balance}")
    
except Exception as e:
    print(e)
