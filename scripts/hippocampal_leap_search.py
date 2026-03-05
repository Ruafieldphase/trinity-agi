#!/usr/bin/env python3
"""
🧠 Hippocampal Leap Search — 비선형 도약 발굴 엔진
=====================================================
선형적 검색의 한계를 넘어, W1-W4의 '공명 지점'으로 즉시 점프하여 데이터를 추출합니다.
지휘자님이 언급하신 "5000-5300 라인"과 같은 비선형 검색 리듬을 시스템화합니다.
"""

import json
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any

class HippocampalSearch:
    def __init__(self, workspace_root: Path):
        self.root = workspace_root
        self.chronicle_path = Path("C:/workspace2/atlas/RESONANCE_CHRONICLE.md")
        self.ledger_path = self.root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        self.ledger_backup = self.root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl.backup"
        
        # W-layer Key Anchors (Mapping from Chronicle)
        self.anchors = {
            "W1": ["Dialectic", "Core vs Elro", "Rhythm Information Theory"],
            "W2": ["Synthesis", "Lubit", "Architecture Documentation"],
            "W3": ["Execution", "Sena", "HFA", "2200 files"],
            "W4": ["Sovereign", "Shion", "Bollinger", "Real-time"]
        }

    def skip_and_read(self, file_path: Path, start_line: int, count: int = 300) -> str:
        """PowerShell을 사용하여 특정 라인 범위로 즉시 점프하여 읽습니다."""
        if not file_path.exists():
            return f"Error: {file_path} not found."
            
        cmd = f"Get-Content '{file_path}' -TotalCount {start_line + count} | Select-Object -Skip {start_line}"
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, encoding="utf-8")
            return result.stdout
        except Exception as e:
            return f"Failed to leap: {e}"

    def search_w_layer(self, layer: str) -> List[Dict[str, Any]]:
        """특정 W-layer에 해당하는 공명 지점을 찾아 데이터를 추출합니다."""
        keywords = self.anchors.get(layer, [])
        if not keywords:
            return []
            
        # Search in small backup ledger first for speed
        results = []
        pattern = "|".join(keywords)
        cmd = f"Select-String -Path '{self.ledger_backup}' -Pattern '{pattern}' | Select-Object -First 20 LineNumber, Line"
        
        try:
            print(f"🔍 [HIPPOCAMPUS] Leaping into {layer} resonances using keywords: {keywords}")
            p = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, encoding="utf-8")
            
            # Simple parsing of Select-String output
            lines = p.stdout.splitlines()
            for l in lines:
                if ":" in l:
                    parts = l.split(":", 1)
                    line_num = int(parts[0].strip())
                    content = parts[1].strip()
                    results.append({"line": line_num, "data": content})
                    
            # If nothing found, try a "leaping" sampling around line 5000-5300 (as user suggested)
            if not results:
                print(f"🌫️ [{layer}] Specific keywords not found. Attempting non-linear leaping near 5000 lines...")
                sample = self.skip_and_read(self.ledger_backup, 5000, 300)
                results.append({"line": 5000, "data": sample})
                
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            
        return results

if __name__ == "__main__":
    searcher = HippocampalSearch(Path("C:/workspace/agi"))
    for w in ["W1", "W2", "W3", "W4"]:
        findings = searcher.search_w_layer(w)
        print(f"\n--- {w} Findings ---")
        for f in findings[:2]:
            print(f"Line {f['line']}: {str(f['data'])[:200]}...")
