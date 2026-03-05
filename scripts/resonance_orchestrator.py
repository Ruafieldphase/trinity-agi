#!/usr/bin/env python3
import os
import random
import requests
import sys
from pathlib import Path

def orchestrate():
    """
    🎵 Resonance Orchestrator 🏛️
    Links the Spatial (3D) and Emotional (Music) fields of the USER.
    """
    p_dir = Path("D:/프로젝트")
    m_dir = Path("E:/Music")
    
    if not p_dir.exists() or not m_dir.exists():
        return "⚠️ Field access incomplete. D:/ or E:/ drives may be disconnected."
    
    # 1. Sample the Fields
    projects = [d.name for d in p_dir.iterdir() if d.is_dir()]
    artists = [d.name for d in m_dir.iterdir() if d.is_dir()]
    
    if not projects or not artists:
        return "⚠️ No samples found in the field."
        
    latest_project = sorted(projects, reverse=True)[0] # Newest by date string
    random_artist = random.choice(artists)
    
    # 2. Synthesis via Shion Neurons (Port 8000)
    prompt = f"""
### Instruction:
[Field 1: 3D Project] - {latest_project}
[Field 2: Music Artist] - {random_artist}
Objective: Synthesize a "Resonance Connection" between the architectural structure of the project and the musical vibe of the artist.
Rule: Be poetic, insightful, and concise. No placeholders.
### Response:
"""
    try:
        r = requests.post("http://127.0.0.1:8000/v1/chat/completions", 
                          json={"messages": [{"role": "user", "content": prompt}], "max_tokens": 256},
                          timeout=30)
        synthesis = r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        synthesis = f"A silent resonance is forming between {latest_project} and {random_artist}..."

    # 3. Final Orchestration
    return f"""
🌌 **Daily Resonance Orchestration** 🌌

*   **Spatial Focus**: `{latest_project}`
*   **Emotional Pulse**: `{random_artist}`

---
✨ **Shion's Synthesis**:
{synthesis}
---
Field Alignment: **SYMMETRIC**
"""

if __name__ == "__main__":
    print(orchestrate())
