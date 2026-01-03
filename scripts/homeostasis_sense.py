#!/usr/bin/env python3
import requests
import json
from pathlib import Path

def check_service(url, timeout=1.0):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def get_homeostasis_pain():
    """
    Returns a 'Pain' report for core AGI services.
    
    Pain Levels:
    0.0: Perfect Health
    0.3: Minor Discomfort (Slow)
    0.6: Disturbance (One core service down)
    0.9: Acute Pain (Multiple core services down)
    """
    services = {
        "Original Data API": "http://127.0.0.1:8093/health",
        "ARI Engine (Local LLM)": "http://127.0.0.1:8080/health"
    }
    
    pain_level = 0.0
    issues = []
    survival_threat = False
    
    for name, url in services.items():
        if not check_service(url):
            pain_level += 0.45 
            issues.append(name)
            survival_threat = True # Any core service down is a survival threat
            
    pain_level = min(0.95, pain_level)
    
    return {
        "pain_level": pain_level,
        "sensation": f"SURVIVAL RISK: {', '.join(issues)} OFFLINE" if issues else "Healthy Homeostasis",
        "issues": issues,
        "survival_threat": survival_threat,
        "vital_count": len(services) - len(issues)
    }

if __name__ == "__main__":
    print(json.dumps(get_homeostasis_pain(), indent=2))
