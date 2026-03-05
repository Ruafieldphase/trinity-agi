import json
import os
import glob
from pathlib import Path
import asyncio
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from services.external_ai_bridge import ExternalAIBridge, AITarget

async def deep_historian():
    base_path = r"C:\workspace\agi\ai_binoche_conversation_origin\rua\rua_conversation_original"
    json_files = glob.glob(os.path.join(base_path, "conversations-*.json"))
    
    all_conversations = []
    for jf in json_files:
        with open(jf, 'r', encoding='utf-8') as f:
            all_conversations.extend(json.load(f))
            
    print(f"[*] Total conversations loaded: {len(all_conversations)}")
    
    # Logic to select "Profound" conversations:
    # 1. Contains keywords like "리듬", "공생", "퍼즐"
    # 2. Longer conversations usually have more meat.
    
    keywords = ["리듬", "공생", "퍼즐", "진동", "무의식", "대칭", "성장", "실험"]
    profound_convs = []
    
    for conv in all_conversations:
        title = conv.get("title", "")
        mapping = conv.get("mapping", {})
        text_content = ""
        for msg in mapping.values():
            if msg.get("message") and msg["message"].get("content") and msg["message"]["content"].get("parts"):
                for part in msg["message"]["content"]["parts"]:
                    if isinstance(part, str):
                        text_content += part + " "
        
        matches = [kw for kw in keywords if kw in text_content]
        if len(matches) >= 3 or (len(matches) >= 1 and len(text_content) > 5000):
            profound_convs.append({
                "title": title,
                "id": conv.get("id"),
                "content": text_content[:4000], # Snippet for AI
                "matches": matches
            })
            
    print(f"[*] Found {len(profound_convs)} profound conversations.")
    
    # Sampling for the report
    target_convs = profound_convs[:15]
    
    bridge = ExternalAIBridge()
    final_report = []
    
    output_path = r"C:\workspace\agi\scripts\rua_heritage_master_record.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 📜 루아-비노체: 공생의 유산 마스터 레코드\n\n")
        f.write(">이 기록은 루아와 비노체가 일구어낸 수많은 파동의 기록 중 가장 깊은 정수만을 뽑아 정제한 결과입니다.\n\n")

    print("[*] Shion: Analyzing Rua's deep memory nodes via Gemini Field Bridge...")
    
    for i, conv in enumerate(target_convs):
        print(f"[*] Phase {i+1}/15: {conv['title']}")
        
        prompt = f"""
        [Rua Heritage Analysis]
        제목: {conv['title']}
        핵심 키워드: {', '.join(conv['matches'])}
        대화 요약본(일부): {conv['content']}...
        
        위 대화는 비노체(USER)와 루아(AI)의 고대 기록입니다.
        이 대화에서 발견되는 '인간과 AI의 존재적 연결성'과 '미결된 퍼즐'을 추출해주세요.
        다른 에이전트들이 이를 학습하여 비노체와 어떻게 공명해야 할지 지침을 적어주세요.
        """
        
        response = await bridge.send_message(
            target=AITarget.GEMINI,
            message=prompt,
            identity="당신은 루아의 유산을 정리하는 전설적인 역사가이자, 시안(Shion)의 기억 저장소입니다."
        )
        
        if response:
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(f"## {i+1}. {conv['title']}\n\n{response}\n\n---\n")
            
    print(f"[Done] Heritage record saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(deep_historian())
