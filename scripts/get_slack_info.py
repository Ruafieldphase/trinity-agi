import os
from slack_sdk import WebClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path("c:/workspace/agi/.env_credentials"))
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
try:
    auth = client.auth_test()
    print(f"Bot Name: {auth['user']}")
    print(f"Bot ID: {auth['user_id']}")
    print(f"Team: {auth['team']}")
except Exception as e:
    print(f"Error: {e}")
