#!/usr/bin/env python3
"""
YouTube Live auto-reply bot.
- Polls live chat messages for the current active broadcast, generates answers via AI backend, and posts replies.
- Requires OAuth token; set up via scripts/youtube_oauth_setup.py

ENV/CLI config:
- GOOGLE_OAUTH_TOKEN_FILE (default: ./credentials/youtube_token.json)
- AI backend preference (checked in order):
  1) OPENAI_API_KEY -> uses OpenAI Chat Completions
  2) GEMINI_API_KEY or GOOGLE_API_KEY -> uses Google Generative AI
  3) AI_GATEWAY_URL -> POST {"prompt": str} expects {"output": str}
- Optional: BOT_NAME (default: GitkoBot)

Usage examples:
  py -3 scripts/youtube_live_bot.py --dry-run
  py -3 scripts/youtube_live_bot.py --poll-interval 3
"""
import os
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import backoff  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv(override=False)

# Add emoji filter
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "fdo_agi_repo"))
from utils.emoji_filter import remove_emojis

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

class BotError(Exception):
    pass


def load_creds(token_file: Optional[str] = None):
    try:
        from google.oauth2.credentials import Credentials  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except Exception:
        raise BotError("Missing google-auth libraries. Run setup_youtube_bot_env.ps1")

    token_path = token_file or os.environ.get("GOOGLE_OAUTH_TOKEN_FILE")
    if not token_path:
        token_path = str(Path(__file__).resolve().parents[1] / "credentials" / "youtube_token.json")
    p = Path(token_path)
    if not p.exists():
        raise BotError(f"OAuth token not found: {p}. Run youtube_oauth_setup.py")

    creds = Credentials.from_authorized_user_file(str(p), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def build_youtube(creds):
    try:
        from googleapiclient.discovery import build  # type: ignore
    except Exception:
        raise BotError("Missing google-api-python-client. Run setup_youtube_bot_env.ps1")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def get_live_chat_id(youtube) -> Tuple[str, Optional[str]]:
    # Returns (liveChatId, broadcastId) for the currently active broadcast
    resp = youtube.liveBroadcasts().list(part="snippet", broadcastStatus="active").execute()
    items = resp.get("items", [])
    if not items:
        raise BotError("No active live broadcast found. Start a stream first.")
    b = items[0]
    live_chat_id = b.get("snippet", {}).get("liveChatId")
    if not live_chat_id:
        raise BotError("Active broadcast has no liveChatId (chat disabled?)")
    return live_chat_id, b.get("id")


def list_messages(youtube, live_chat_id: str, page_token: Optional[str] = None):
    req = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet,authorDetails",
        pageToken=page_token,
    )
    return req.execute()


def post_message(youtube, live_chat_id: str, text: str):
    body = {
        "snippet": {
            "liveChatId": live_chat_id,
            "type": "textMessageEvent",
            "textMessageDetails": {"messageText": text},
        }
    }
    return youtube.liveChatMessages().insert(part="snippet", body=body).execute()


# ---------------- AI backends -----------------

def answer_with_openai(prompt: str) -> Optional[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None
    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": "You are a concise, helpful assistant."},
                     {"role": "user", "content": prompt}],
            temperature=float(os.environ.get("AI_TEMPERATURE", 0.2)),
            max_tokens=int(os.environ.get("AI_MAX_TOKENS", 300))
        )
        return remove_emojis(resp.choices[0].message.content)
    except Exception:
        return None


def answer_with_gemini(prompt: str) -> Optional[str]:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return None
    genai.configure(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    try:
        resp = genai.GenerativeModel(model).generate_content(prompt)
        return remove_emojis(resp.text)
    except Exception:
        return None


def answer_with_gateway(prompt: str) -> Optional[str]:
    url = os.environ.get("AI_GATEWAY_URL")
    if not url:
        return None
    import json as _json
    import urllib.request as rq
    req = rq.Request(url, data=_json.dumps({"prompt": prompt}).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with rq.urlopen(req, timeout=15) as r:
            data = _json.loads(r.read().decode("utf-8"))
            return remove_emojis(data.get("output"))
    except Exception:
        return None


def generate_answer(prompt: str) -> str:
    for fn in (answer_with_openai, answer_with_gemini, answer_with_gateway):
        ans = fn(prompt)
        if ans:
            return ans.strip()
    return "(자동응답 준비 중입니다. AI 백엔드 설정이 필요합니다.)"


# ---------------- Main loop -----------------

def is_from_self(msg: Dict[str, Any], bot_name: str) -> bool:
    ad = msg.get("authorDetails", {})
    dn = ad.get("displayName", "").lower()
    return bot_name.lower() in dn


def format_prompt_from_message(msg: Dict[str, Any]) -> Optional[str]:
    snip = msg.get("snippet", {})
    if snip.get("type") != "textMessageEvent":
        return None
    txt = snip.get("textMessageDetails", {}).get("messageText", "")
    author = msg.get("authorDetails", {}).get("displayName", "viewer")
    if not txt:
        return None
    return f"Viewer {author} asked: {txt}\nProvide a concise, accurate answer suitable for a live stream."


def parse_args():
    import argparse
    p = argparse.ArgumentParser(description="YouTube Live auto-reply bot")
    p.add_argument("--dry-run", action="store_true", help="Don't post messages; log only")
    p.add_argument("--poll-interval", type=float, default=float(os.environ.get("BOT_POLL_INTERVAL", 3.0)))
    p.add_argument("--token-file", default=os.environ.get("GOOGLE_OAUTH_TOKEN_FILE"))
    p.add_argument("--bot-name", default=os.environ.get("BOT_NAME", "GitkoBot"))
    return p.parse_args()


@backoff.on_exception(backoff.expo, Exception, max_time=60)
def safe_list_messages(youtube, live_chat_id: str, token: Optional[str]):
    return list_messages(youtube, live_chat_id, token)


def main():
    args = parse_args()

    # If dry-run and no OAuth, allow a friendly pass
    try:
        creds = load_creds(args.token_file)
    except BotError as e:
        if args.dry_run:
            print(f"[DryRun] OAuth not ready: {e}")
            sys.exit(0)
        print(str(e), file=sys.stderr)
        sys.exit(2)

    youtube = build_youtube(creds)

    try:
        live_chat_id, broadcast_id = get_live_chat_id(youtube)
        print(f"LiveChatID: {live_chat_id} (broadcast: {broadcast_id})")
    except BotError as e:
        if args.dry_run:
            print(f"[DryRun] {e}")
            sys.exit(0)
        print(str(e), file=sys.stderr)
        sys.exit(2)

    page_token = None
    seen_ids: set = set()

    print("Bot started. Press Ctrl+C to stop.")
    while True:
        try:
            resp = safe_list_messages(youtube, live_chat_id, page_token)
            page_token = resp.get("nextPageToken")
            items = resp.get("items", [])
            for m in items:
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                if is_from_self(m, args.bot_name):
                    continue
                prompt = format_prompt_from_message(m)
                if not prompt:
                    continue
                answer = generate_answer(prompt)
                print(json.dumps({"q": prompt, "a": answer}, ensure_ascii=False))
                if not args.dry_run:
                    try:
                        post_message(youtube, live_chat_id, answer[:198])  # keep it short
                    except Exception:
                        traceback.print_exc()
            time.sleep(args.poll_interval)
        except KeyboardInterrupt:
            print("Stopped by user")
            break
        except Exception:
            traceback.print_exc()
            time.sleep(3)


if __name__ == "__main__":
    main()
