#!/usr/bin/env python3
"""
YouTube OAuth setup helper for Live Chat bot.
- Looks for client secret JSON in:
  1) env GOOGLE_OAUTH_CLIENT_SECRET_FILE
  2) ./credentials/client_secret.json (relative to workspace root)
- Stores token at ./credentials/youtube_token.json

Scopes:
- https://www.googleapis.com/auth/youtube
- https://www.googleapis.com/auth/youtube.force-ssl

Usage:
  py -3 scripts/youtube_oauth_setup.py
"""
import os
import sys
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    except Exception:
        print("Missing dependencies. Run: powershell -File scripts/setup_youtube_bot_env.ps1", file=sys.stderr)
        sys.exit(2)

    workspace = Path(__file__).resolve().parents[1]
    cred_dir = workspace / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)

    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
    if not client_secret:
        client_secret = str(cred_dir / "client_secret.json")

    client_secret_path = Path(client_secret)
    if not client_secret_path.exists():
        print(f"Client secret not found: {client_secret_path}", file=sys.stderr)
        print("Place your OAuth client secret JSON there or set GOOGLE_OAUTH_CLIENT_SECRET_FILE.")
        sys.exit(2)

    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = cred_dir / "youtube_token.json"
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"Saved OAuth token to: {token_path}")

if __name__ == "__main__":
    main()
