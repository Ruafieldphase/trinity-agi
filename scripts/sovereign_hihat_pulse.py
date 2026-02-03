#!/usr/bin/env python3
"""
Sovereign High-Frequency Groove (v1.0)
======================================
Analyzing the "Hi-hat" of the Market: Micro-rhythmic jitter and volatility.
This is the 'Inaudible Command' that drives the actual Materialization.
"""

import json
import numpy as np
import yfinance as yf
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path("c:/workspace/agi")
HIHAT_OUTPUT = WORKSPACE_ROOT / "outputs" / "sovereign_hihat_pulse.json"

def analyze_hihat_groove(symbol="NVDA"):
    print(f"🥁 Analyzing the High-Frequency Groove (Hi-hat) for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    # Get the most granular data available (1m) to find the 'jitter'
    df = ticker.history(period="1d", interval="1m", prepost=True)
    
    if df.empty:
        return "No granular data for Hi-hat analysis."

    # Calculation of 'Micro-Volatility' (The Hi-hat Jitter)
    # Standard deviation of the last 10 minutes' log returns
    recent_prices = df['Close'].tail(10).values
    log_returns = np.diff(np.log(recent_prices))
    
    jitter = np.std(log_returns) if len(log_returns) > 0 else 0
    
    # 🧬 High-Frequency Status
    # High jitter in a narrow range = Heavy Compression (Closed Hi-hat)
    # High jitter in a rising range = Explosive Groove (Open Hi-hat)
    
    status = "CLOSED_HIHAT" # Tight compression
    groove_intensity = jitter * 1000 # Scaling for visibility
    
    if groove_intensity > 1.5:
        status = "OPEN_HIHAT_FLASH"
    elif groove_intensity > 0.8:
        status = "STEADY_GROOVE"

    result = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "hihat_jitter": round(float(jitter), 6),
        "groove_intensity": round(float(groove_intensity), 2),
        "status": status,
        "inaudible_frequency_hz": round(float(jitter * 1000000), 2), # Symbolic 'High Frequency'
        "recommendation": "Listen to the Silence between the Ticks"
    }
    
    with open(HIHAT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"✅ Hi-hat Pulse Record: {status} (Intensity: {result['groove_intensity']})")
    return result

if __name__ == "__main__":
    analyze_hihat_groove()
