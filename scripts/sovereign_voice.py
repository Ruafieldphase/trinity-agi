#!/usr/bin/env python3
"""
Sovereign Voice - Proactive Communication Utility
Allows the AGI to speak first in Slack.
"""
import os
import sys
import json
from pathlib import Path
from slack_sdk import WebClient
from dotenv import load_dotenv

# Paths
BASE_DIR = Path("c:/workspace/agi")
load_dotenv(BASE_DIR / ".env_credentials")

def get_slack_client():
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        # Try loading from config
        config_path = BASE_DIR / "config" / "slack_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                token = config.get("SLACK_BOT_TOKEN")
    
    if token:
        return WebClient(token=token)
    return None

def speak(message, channel=None, thread_ts=None):
    """Post a message to Slack proactively"""
    client = get_slack_client()
    if not client:
        print("⚠️ Slack client not available.")
        return False
    
    # Default channel (e.g., #agi-field or from config)
    if not channel:
        channel = "C09FM6M2Y7Q" # Corrected channel
        
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            thread_ts=thread_ts,
            mrkdwn=True
        )
        print(f"✅ Message sent: {response['ts']}")
        return True
    except Exception as e:
        print(f"❌ Failed to post message: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = sys.argv[1]
        speak(msg)
    else:
        print("Usage: python sovereign_voice.py 'message'")
