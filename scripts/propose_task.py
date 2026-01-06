import sys
import json
import os
from core_slack_adapter import CoreSlackAdapter
from workspace_root import get_workspace_root

def propose_task(proposal_data):
    """
    Formats a proposal and sends it to Slack.
    proposal_data: {
        "file": "path/to/file",
        "type": "REFACTOR",
        "reason": "...",
        "urgency": "LOW",
        "observation": "..."
    }
    """
    slack = CoreSlackAdapter()
    
    file_path = proposal_data.get("file", "Unknown")
    task_type = proposal_data.get("type", "TASK")
    reason = proposal_data.get("reason", "No reason given.")
    observation = proposal_data.get("observation", "...")
    
    # Emoji map
    emoji_map = {
        "REFACTOR": "🛠️",
        "DOCS": "📝",
        "CLEANUP": "🧹"
    }
    emoji = emoji_map.get(task_type, "💡")
    
    # Save to proposals.json
    proposals_file = get_workspace_root() / "outputs" / "proposals.json"
    proposals = []
    if os.path.exists(proposals_file):
        try:
            with open(proposals_file, "r", encoding="utf-8") as f:
                proposals = json.load(f)
        except:
            pass
    
    # Add ID and timestamp if not present
    import time
    if "id" not in proposal_data:
        proposal_data["id"] = int(time.time())
    if "timestamp" not in proposal_data:
        proposal_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
    proposal_data["status"] = "pending"
    proposals.append(proposal_data)
    
    with open(proposals_file, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)
        
    print(f"Saved proposal {proposal_data['id']} to {proposals_file}")

    # Message Format
    msg = f"🌿 **정원에서의 제안 (Proposal from the Garden)**\n"
    msg += f"> *발견한 파일:* `{file_path}`\n"
    msg += f"> *관찰:* \"{observation}\"\n\n"
    msg += f"{emoji} **제안된 작업:** {task_type}\n"
    msg += f"_{reason}_\n\n"
    msg += "승인하시겠습니까? (대시보드를 확인하세요)"
    
    print(f"Sending proposal for {file_path}...")
    slack.send_message(msg)

if __name__ == "__main__":
    # Expecting JSON string or file path as first argument
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            if arg.endswith(".json") and os.path.exists(arg):
                with open(arg, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(arg)
            propose_task(data)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python propose_task.py '<json_string>' or <json_file_path>")
