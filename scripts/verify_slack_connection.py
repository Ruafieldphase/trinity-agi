import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

CONFIG_PATH = 'c:/workspace/agi/config/slack_config.json'

def verify():
    if not os.path.exists(CONFIG_PATH):
        print(f"Config not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    token = config.get('SLACK_BOT_TOKEN')
    channel = config.get('SLACK_CHANNEL_ID')

    if not token or token.startswith('xoxb-your'):
        print("Invalid or placeholder token.")
        return

    client = WebClient(token=token)

    try:
        auth_test = client.auth_test()
        print(f"✅ Authenticated as: {auth_test['user']} (Team: {auth_test['team']})")
        
        if channel:
            try:
                client.chat_postMessage(channel=channel, text="🤖 Core System Verification: Slack Connection Active.")
                print(f"✅ Successfully sent test message to {channel}")
            except SlackApiError as e:
                print(f"❌ Failed to send message: {e.response['error']}")
        else:
            print("⚠️ No Channel ID configured.")

    except SlackApiError as e:
        print(f"❌ Authentication Failed: {e.response['error']}")

if __name__ == "__main__":
    verify()
