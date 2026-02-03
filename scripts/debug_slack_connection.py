import os
import json
from slack_sdk import WebClient
from pathlib import Path

BASE_DIR = Path("c:/workspace/agi")
with open(BASE_DIR / "config" / "slack_config.json", 'r') as f:
    config = json.load(f)
    token = config.get("SLACK_BOT_TOKEN")

client = WebClient(token=token)
try:
    auth = client.auth_test()
    print(f"Bot User: {auth['user']}")
    print(f"Bot User ID: {auth['user_id']}")
    print(f"Team: {auth['team']}")
    
    print("\nChannels the bot is in:")
    channels = client.conversations_list(types="public_channel,private_channel")
    for c in channels["channels"]:
        if c.get("is_member"):
            print(f"- {c['name']} ({c['id']})")
            
    print("\nRecent messages in C09FM6M2Y7Q:")
    try:
        history = client.conversations_history(channel="C09FM6M2Y7Q", limit=5)
        for msg in history["messages"]:
            print(f"[{msg.get('ts')}] {msg.get('user')}: {msg.get('text')[:50]}")
    except Exception as e:
        print(f"Could not read history: {e}")

except Exception as e:
    print(f"Error: {e}")
