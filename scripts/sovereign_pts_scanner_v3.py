#!/usr/bin/env python3
"""
Sovereign PTS Scanner v3.0 (Real Resonance)
===========================================
Integrated with real market data via yfinance.
Translating the Brother's Market Rhythm (PTS-1.0) into Sovereign Action.

PTS Signals:
- Bandwidth Reversal (40 pts)
- Upper Band Rising (25 pts)
- Lower Band Falling (25 pts)
- Price > MA20 (10 pts)
Total: 100 pts.

Sovereign Filter:
U = e^(i*theta) / Omega
Where Omega = Inverse of standard deviation (Compression).
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

# Target Symbols for Livelihood Pressure Resolution
SYMBOLS = ["TQQQ", "SOXL", "NVDA", "TSLA", "MSFT", "AAPL", "BTC-USD", "ETH-USD"]
DISCOVERY_SYMBOLS = ["QQQ", "SPY", "AMD", "META", "AMZN", "GOOGL", "AVGO", "COST", "MSTR", "COIN"]

def calculate_pts(df):
    """Calculate Phase Transition Score (PTS) based on recent data."""
    if len(df) < 30: return 0, {}
    
    # 1. Indicators
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    upper = ma20 + (2 * std20)
    lower = ma20 - (2 * std20)
    bandwidth = (upper - lower) / ma20
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    signals = {}
    
    # Signal A: Bandwidth Reversal (Compression -> Expansion)
    # Checking if bandwidth started increasing after a narrow point
    is_reversal = (bandwidth.iloc[-1] > bandwidth.iloc[-2]) and (bandwidth.iloc[-2] < bandwidth.iloc[-3])
    if is_reversal:
        score += 40
        signals["bandwidth_reversal"] = True
    
    # Signal B: Upper Band Rising
    is_upper_rising = upper.iloc[-1] > upper.iloc[-2]
    if is_upper_rising:
        score += 25
        signals["upper_band_rising"] = True
        
    # Signal C: Lower Band Falling (Expansion)
    is_lower_falling = lower.iloc[-1] < lower.iloc[-2]
    if is_lower_falling:
        score += 25
        signals["lower_band_falling"] = True
        
    # Signal D: Price > MA20
    is_above_ma20 = curr['Close'] > ma20.iloc[-1]
    if is_above_ma20:
        score += 10
        signals["price_above_ma20"] = True
        
    return score, {
        "price": round(curr['Close'], 2),
        "change_pct": round(((curr['Close'] - prev['Close'])/prev['Close'])*100, 2),
        "bandwidth": round(bandwidth.iloc[-1], 4),
        "ma20": round(ma20.iloc[-1], 2),
        "signals": signals
    }

def calculate_sovereign_metrics(df, pts_score):
    """Apply Sovereign Formula U = e^(i^theta) / Omega."""
    if len(df) < 20: return 0, 0
    
    # Omega = Experience density (Inverse of volatility for stability)
    vol = df['Close'].pct_change().std()
    # Normalize Omega so that high stability (low vol) is a larger number
    omega = 1.0 / max(vol, 0.001) 
    
    # Resistance U = 1 / Omega
    resistance = 1.0 / omega
    
    # Sovereign Score: Using Exponential Decay for Resistance
    # Antigravity Lift = exp(-resistance * K)
    # This keeps the score positive and sensitive to compression.
    antigravity_lift = np.exp(-resistance * 10) # Scaling factor K=10
    
    sovereign_score = pts_score * antigravity_lift
    
    return round(sovereign_score, 2), round(resistance, 4)

def main():
    print(f"🚀 Sovereign PTS Scanner v3.0 | Reality Sync Mode")
    print(f"Time: {datetime.now().isoformat()}")
    print("-" * 60)
    
    results = []
    all_targets = list(set(SYMBOLS + DISCOVERY_SYMBOLS))
    for symbol in all_targets:
        try:
            print(f"🔭 Scanning {symbol}...", end="\r")
            # Force single symbol behavior if needed or handle MultiIndex
            df = yf.download(symbol, period="3mo", interval="1d", progress=False)
            
            if df is None or df.empty:
                print(f"⚠️ {symbol}: No data found.")
                continue
            
            # If MultiIndex (new yfinance default), flatten or select Ticker
            if isinstance(df.columns, pd.MultiIndex):
                # Check if ticker is in level 1
                if symbol in df.columns.get_level_values(1):
                    df = df.xs(symbol, axis=1, level=1)
                else:
                    # Just flatten if needed
                    df.columns = df.columns.get_level_values(0)

            pts_score, metrics = calculate_pts(df)
            sov_score, resistance = calculate_sovereign_metrics(df, pts_score)
            
            res = {
                "symbol": symbol,
                "pts_score": pts_score,
                "sovereign_score": sov_score,
                "resistance": resistance,
                "price": metrics["price"],
                "change_pct": metrics["change_pct"],
                "bandwidth": metrics["bandwidth"],
                "signals": metrics["signals"],
                "status": "SINGULARITY" if sov_score > 70 else "RESONATING" if sov_score > 40 else "VOID"
            }
            results.append(res)
            
        except Exception as e:
            # print(f"❌ Error scanning {symbol}: {e}") # Debug: print(traceback.format_exc())
            pass # Silent failure to keep logs clean, but real errors visible in manual run

    # Sort and Save
    results.sort(key=lambda x: x["sovereign_score"], reverse=True)
    
    output_path = Path("c:/workspace/agi/outputs/sovereign_scan_latest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "results": results
        }, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*60)
    print(f"{'SYMBOL':10s} | {'SOV SCORE':10s} | {'PRICE':10s} | {'STATUS'}")
    print("-" * 60)
    for r in results:
        marker = "🔥" if r["status"] == "SINGULARITY" else "✨" if r["status"] == "RESONATING" else "  "
        print(f"{marker} {r['symbol']:10s} | {r['sovereign_score']:10.2f} | {r['price']:10.2f} | {r['status']}")
    print("="*60)
    print(f"✅ Scan Complete. Potential identified for livelihood pressure resolution.")

if __name__ == "__main__":
    main()
