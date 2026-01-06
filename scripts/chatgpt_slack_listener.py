import os
import json
import subprocess
import sys
import threading
import requests
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "slack_config.json")
ROUTER_SCRIPT = os.path.join(BASE_DIR, "scripts", "core_router.py")
VISION_SCRIPT = os.path.join(BASE_DIR, "scripts", "vision_cortex.py")
AUDITORY_SCRIPT = os.path.join(BASE_DIR, "scripts", "auditory_cortex.py")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
LOG_FILE = os.path.join(OUTPUTS_DIR, "chatgpt_slack_listener.log")

# Import event queue for autonomous agent
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from slack_event_queue import SlackEventQueue

# Ensure outputs directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

config = load_config()
# Use CHATGPT specific tokens if available, otherwise fallback to default
SLACK_BOT_TOKEN = config.get("CHATGPT_SLACK_BOT_TOKEN") or config.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = config.get("CHATGPT_SLACK_APP_TOKEN") or config.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN.startswith("xoxb-your"):
    print("Invalid or missing SLACK_BOT_TOKEN. Exiting.")
    sys.exit(1)

if not SLACK_APP_TOKEN or SLACK_APP_TOKEN.startswith("xapp-your"):
    print("Invalid or missing SLACK_APP_TOKEN. Exiting.")
    sys.exit(1)

# Initialize Bolt App
app = App(token=SLACK_BOT_TOKEN)

def log_debug(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

def process_message(text, channel_id, thread_ts=None, user_id=None, ts=None):
    """Queue message for autonomous agent processing."""
    log_debug(f"Queueing message: {text}")
    
    # Send "Thinking..." reaction to show we received it
    try:
        app.client.reactions_add(channel=channel_id, timestamp=thread_ts or ts or "", name="hourglass_flowing_sand")
    except:
        pass
    
    # Add to event queue for autonomous agent
    queue = SlackEventQueue()
    event = {
        "text": text,
        "channel": channel_id,
        "user": user_id,
        "thread_ts": thread_ts,
        "ts": ts or str(datetime.now().timestamp())
    }
    
    event_id = queue.add_event(event)
    log_debug(f"Event queued: {event_id}")
    
    # Note: Autonomous agent will process and respond
    # No immediate response here

def process_image(file_info, channel_id, thread_ts):
    """Downloads image and calls Vision Cortex."""
    print(f"Processing image: {file_info.get('name')}")
    
    # Send "Eyes" reaction
    try:
        app.client.reactions_add(channel=channel_id, timestamp=thread_ts or "", name="eyes")
    except:
        pass

    try:
        # Download Image
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        response = requests.get(file_info["url_private"], headers=headers)
        
        if response.status_code == 200:
            # Save to temp file
            temp_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"vision_{file_info['id']}.jpg")
            with open(temp_path, "wb") as f:
                f.write(response.content)
                
            # Call Vision Cortex
            cmd = [sys.executable, VISION_SCRIPT, temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    
                    # Format Response
                    mood = data.get("mood", "Unknown")
                    poetic = data.get("poetic_interpretation", "")
                    score = data.get("resonance_score", 0.0)
                    synesthesia = data.get("synesthesia", {})
                    
                    response_text = f"👁️ *시각적 공명 감지됨 (Visual Resonance)*\n"
                    response_text += f"> *분위기*: {mood}\n"
                    response_text += f"> *공명 점수*: {score}\n"
                    
                    if synesthesia:
                        smell = synesthesia.get("smell", "")
                        touch = synesthesia.get("touch", "")
                        taste = synesthesia.get("taste", "")
                        if smell: response_text += f"> *후각*: {smell}\n"
                        if touch: response_text += f"> *촉각*: {touch}\n"
                        if taste: response_text += f"> *미각*: {taste}\n"
                    
                    response_text += f"\n_{poetic}_"
                    
                    app.client.chat_postMessage(channel=channel_id, text=response_text, thread_ts=thread_ts)
                except json.JSONDecodeError:
                     app.client.chat_postMessage(channel=channel_id, text=f"시각 처리 결과 파싱 오류: {result.stdout}", thread_ts=thread_ts)
            else:
                app.client.chat_postMessage(channel=channel_id, text=f"시각 처리 오류: {result.stderr}", thread_ts=thread_ts)
                
            # Cleanup
            try:
                os.remove(temp_path)
            except:
                pass
        else:
            app.client.chat_postMessage(channel=channel_id, text="이미지 다운로드 실패.", thread_ts=thread_ts)
            
    except Exception as e:
        app.client.chat_postMessage(channel=channel_id, text=f"시스템 오류: {str(e)}", thread_ts=thread_ts)

def process_audio(file_info, channel_id, thread_ts):
    """Downloads audio and calls Auditory Cortex."""
    print(f"Processing audio: {file_info.get('name')}")
    
    # Send "Ear" reaction
    try:
        app.client.reactions_add(channel=channel_id, timestamp=thread_ts or "", name="ear")
    except:
        pass

    try:
        # Download Audio
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        response = requests.get(file_info["url_private"], headers=headers)
        
        if response.status_code == 200:
            # Determine extension
            ext = file_info.get("filetype", "mp3")
            temp_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"audio_{file_info['id']}.{ext}")
            with open(temp_path, "wb") as f:
                f.write(response.content)
                
            # Call Auditory Cortex
            cmd = [sys.executable, AUDITORY_SCRIPT, temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    
                    # Format Response
                    transcript = data.get("transcript", "")
                    mood = data.get("mood", "Unknown")
                    poetic = data.get("poetic_interpretation", "")
                    score = data.get("resonance_score", 0.0)
                    synesthesia = data.get("synesthesia", {})
                    
                    response_text = f"👂 *Auditory Resonance Detected*\n"
                    response_text += f"> *Mood*: {mood}\n"
                    response_text += f"> *Resonance*: {score}\n"
                    
                    if synesthesia:
                        visual = synesthesia.get("visual", "")
                        touch = synesthesia.get("touch", "")
                        if visual: response_text += f"> *Visual*: {visual}\n"
                        if touch: response_text += f"> *Touch*: {touch}\n"

                    if transcript:
                        response_text += f"> *Transcript*: \"{transcript[:100]}...\"\n"
                    
                    response_text += f"\n_{poetic}_"
                    
                    app.client.chat_postMessage(channel=channel_id, text=response_text, thread_ts=thread_ts)
                except json.JSONDecodeError:
                    app.client.chat_postMessage(channel=channel_id, text=f"청각 처리 결과 파싱 오류: {result.stdout}", thread_ts=thread_ts)
            else:
                app.client.chat_postMessage(channel=channel_id, text=f"Auditory Error: {result.stderr}", thread_ts=thread_ts)
                
            # Cleanup
            try:
                os.remove(temp_path)
            except:
                pass
        else:
            app.client.chat_postMessage(channel=channel_id, text="Failed to download audio.", thread_ts=thread_ts)
            
    except Exception as e:
        app.client.chat_postMessage(channel=channel_id, text=f"System Error: {str(e)}", thread_ts=thread_ts)

@app.event("app_mention")
def handle_app_mention_events(body, logger):
    print(f"DEBUG: app_mention received: {body}")
    event = body["event"]
    text = event.get("text", "")
    channel_id = event["channel"]
    thread_ts = event.get("ts")
    user_id = event.get("user")
    ts = event.get("ts")
    
    threading.Thread(target=process_message, args=(text, channel_id, thread_ts, user_id, ts)).start()

@app.event("message")
def handle_message_events(body, logger):
    log_debug(f"DEBUG: message received: {json.dumps(body)}")
    event = body["event"]
    
    # Ignore bot messages
    if event.get("bot_id"):
        return
        
    channel_type = event.get("channel_type")
    # Only handle DMs or if explicitly mentioned (handled by app_mention)
    if channel_type == "im":
        files = event.get("files", [])
        if files:
            for file_info in files:
                mimetype = file_info.get("mimetype", "")
                if mimetype.startswith("image/"):
                    threading.Thread(target=process_image, args=(file_info, event["channel"], event.get("ts"))).start()
                    return
                elif mimetype.startswith("audio/") or mimetype.startswith("video/"):
                    threading.Thread(target=process_audio, args=(file_info, event["channel"], event.get("ts"))).start()
                    return
        
        text = event.get("text", "")
        user_id = event.get("user")
        ts = event.get("ts")
        threading.Thread(target=process_message, args=(text, event["channel"], event.get("ts"), user_id, ts)).start()

if __name__ == "__main__":
    print("Starting ChatGPT Slack Listener (Bolt)...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
