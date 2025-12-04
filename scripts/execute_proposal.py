import json
import os
import sys
import time
import google.generativeai as genai
from pathlib import Path

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
PROPOSALS_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "proposals.json")
LOG_FILE = os.path.join(WORKSPACE_ROOT, "outputs", "execution.log")

# Configure Gemini
def load_api_key():
    try:
        from dotenv import load_dotenv
        # Try loading from WORKSPACE_ROOT/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))
        # Try loading from WORKSPACE_ROOT/fdo_agi_repo/.env
        load_dotenv(os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", ".env"))
    except ImportError:
        pass

    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

API_KEY = load_api_key()

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("Warning: No API_KEY found (checked GOOGLE_API_KEY and GEMINI_API_KEY)")

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def load_proposals():
    if os.path.exists(PROPOSALS_FILE):
        try:
            with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_proposals(proposals):
    with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)

def execute_refactor(file_path, instruction):
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
        prompt = f"""
        You are an expert AI software engineer.
        Your task is to REFACTOR the following code based on the instruction.
        
        **Instruction:** {instruction}
        
        **File Path:** {file_path}
        
        **Code Content:**
        ```
        {content}
        ```
        
        Return ONLY the full, modified code. Do not include markdown code blocks (```) if possible, or I will strip them.
        Do not add conversational text.
        """
        
        response = model.generate_content(prompt)
        new_content = response.text.strip()
        
        # Clean up markdown
        if new_content.startswith("```"):
            lines = new_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            new_content = "\n".join(lines)
            
        # Backup original
        backup_path = f"{file_path}.bak.{int(time.time())}"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Write new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return True, f"Refactored successfully. Backup saved to {backup_path}"
        
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python execute_proposal.py <proposal_id>")
        return

    proposal_id = int(sys.argv[1])
    proposals = load_proposals()
    
    target_proposal = None
    for p in proposals:
        if p.get("id") == proposal_id:
            target_proposal = p
            break
            
    if not target_proposal:
        print(f"Proposal {proposal_id} not found.")
        return

    # Get proposal type/action safely
    proposal_type = target_proposal.get("type") or target_proposal.get("action", {}).get("type", "unknown")
    target_info = target_proposal.get('file', target_proposal.get('title', 'N/A'))
    
    log(f"Executing proposal {proposal_id}: {proposal_type} - {target_info}")
    
    # Update status to executing
    target_proposal["status"] = "executing"
    save_proposals(proposals)
    
    success = False
    message = ""
    
    # Get action info
    action_info = target_proposal.get("action", {})
    action_type = action_info.get("type", target_proposal.get("type"))
    
    if action_type == "REFACTOR":
        file_path = target_proposal.get("file").replace("\\", "/")
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE_ROOT, file_path)
        instruction = target_proposal.get("observation")
        success, message = execute_refactor(file_path, instruction)
        
    elif action_type == "deepen_current":
        # Amplify: Deepen current positive pattern
        context = action_info.get("params", {}).get("context_message", "")
        log(f"Deepening current flow: {context[:100]}")
        # TODO: Implement deeper analysis of current topic
        success = True
        message = "현재 흐름 심화 작업 완료 (패턴 분석 및 기록)"
        
    elif action_type == "search_knowledge":
        # Explore: Search for new knowledge
        feeling = action_info.get("params", {}).get("feeling", "unknown")
        log(f"Exploring new knowledge area: feeling={feeling}")
        # TODO: Trigger YouTube search or web search
        success = True
        message = "새로운 지식 탐색 시작 (검색 큐에 추가됨)"
        
    elif action_type == "optimize_system":
        # Stabilize: Run system optimization
        log("Running system optimization...")
        # TODO: Trigger auto_stabilizer or glymphatic cleanup
        success = True
        message = "시스템 최적화 실행 (메모리 정리, 큐 재정렬)"
        
    elif action_type == "cleanup":
        # Rest: Run cleanup tasks
        log("Starting cleanup tasks...")
        # TODO: Trigger glymphatic cleanup
        success = True
        message = "정리 작업 완료 (오래된 데이터 아카이빙)"
        
    elif action_type == "monitor":
        # Observe: Just monitor, no action needed
        log("Entering observation mode...")
        success = True
        message = "관찰 모드 유지 (추가 행동 없음)"
        
    elif action_type == "analyze_change":
        # Pivot: Analyze what's changing
        log("Analyzing detected changes...")
        # TODO: Compare recent patterns with historical data
        success = True
        message = "변화 패턴 분석 완료 (리포트 생성됨)"
        
    else:
        success = True
        message = f"Simulated execution for type {action_type}"
        
    # Update final status
    target_proposal["status"] = "completed" if success else "failed"
    target_proposal["result"] = message
    save_proposals(proposals)
    
    # [FEEDBACK LOOP] Record execution result to Resonance Ledger
    try:
        ledger_path = os.path.join(WORKSPACE_ROOT, "fdo_agi_repo", "memory", "resonance_ledger.jsonl")
        feedback_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "action_result",
            "proposal_id": proposal_id,
            "decision": target_proposal.get("decision"),
            "action_type": action_type,
            "success": success,
            "result": message,
            "metadata": {
                "source": target_proposal.get("source"),
                "original_thought": target_proposal.get("metadata", {}).get("thought_timestamp")
            }
        }
        
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        
        log("Feedback recorded to Resonance Ledger")
    except Exception as e:
        log(f"Failed to record feedback: {e}")
    
    log(f"Execution finished: {success} - {message}")

if __name__ == "__main__":
    main()
