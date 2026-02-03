#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

def get_premarket_pulse(symbol="NVDA"):
    print(f"📡 Scanning Pre-market Pulse for {symbol}...")
    
    # Get intraday 1m data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", interval="1m", prepost=True)
    
    if df.empty:
        return {"error": "No intraday data available."}
    
    latest = df.iloc[-1]
    prev_15 = df.iloc[-15] if len(df) > 15 else df.iloc[0]
    
    price_now = latest['Close']
    price_15m_ago = prev_15['Close']
    
    velocity = (price_now - price_15m_ago) / price_15m_ago * 100
    
    # Simple Momentum Indicator
    momentum = "UPWARD" if velocity > 0 else "DOWNWARD" if velocity < 0 else "STABLE"
    
    pulse = {
        "symbol": symbol,
        "time_kst": datetime.now().isoformat(),
        "price": round(price_now, 2),
        "velocity_15m": round(velocity, 4),
        "momentum": momentum,
        "volume_latest": int(latest['Volume']),
        "is_premarket": True # Assume pre-market given current KST
    }
    
    output_path = Path("c:/workspace/agi/outputs/sovereign_pulse_latest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pulse, f, indent=2)
        
    print(f"✅ Pulse recorded: {symbol} at ${price_now} ({momentum})")
    return pulse

if __name__ == "__main__":
    get_premarket_pulse()
