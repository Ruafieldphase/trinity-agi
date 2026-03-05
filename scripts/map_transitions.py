import json
import os

INDEX_FILE = r"C:\workspace\agi\heritage_vault\TOTAL_INDEX.json"
OUTPUT_TRANSITION_MAP = r"C:\workspace\agi\PHASE_TRANSITION_MAP.md"

def analyze_transitions():
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # Track titles and personas
    transitions = []
    seen_ids = set()
    
    # Keywords for phases
    phases = {
        "Lua": ["루아", "lua", "감응", "정(精)"],
        "Ello": ["엘로", "ello", "구조", "반(反)"],
        "Lumen": ["루멘", "lumen", "통합", "합(合)", "지성"],
        "Failure": ["실패", "장벽", "vertex", "구글", "연극"]
    }
    
    for entry in index:
        cid = entry["id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        
        title = entry["title"]
        date = entry["date"]
        
        # Check title for phase keywords
        matched_phases = []
        for phase, keywords in phases.items():
            if any(kw.lower() in title.lower() for kw in keywords):
                matched_phases.append(phase)
        
        if matched_phases:
            transitions.append({
                "date": date,
                "title": title,
                "phases": matched_phases,
                "id": cid
            })
    
    # Sort by date
    transitions.sort(key=lambda x: x["date"])
    
    # Write to Markdown
    with open(OUTPUT_TRANSITION_MAP, 'w', encoding='utf-8') as f:
        f.write("# 🌀 AGI Phase Transition Map (Restored)\n\n")
        f.write("이 지도는 10개월간의 대화 인덱스(21,842개 메시지)에서 추출된 핵심 위상 전이의 마디들입니다.\n\n")
        f.write("| 날짜 | 대화 주제 | 위상(Phase) | 옵시디언 링크 |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for t in transitions:
            safe_title = t["title"].replace("|", "-")
            link = f"[[[{t['date']}] {safe_title}]]"
            f.write(f"| {t['date']} | {safe_title} | {', '.join(t['phases'])} | {link} |\n")
            
    print(f"✅ Phase Transition Map generated: {OUTPUT_TRANSITION_MAP}")

if __name__ == "__main__":
    analyze_transitions()
