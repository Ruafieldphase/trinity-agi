import json
from pathlib import Path
import google.oauth2.credentials
from googleapiclient.discovery import build

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
VIDEO_ID = "TXAMQxSjZS4"
SEO_PATH = AGI_ROOT / "outputs/refined_youtube_seo.json"
CRED_DIR = AGI_ROOT / "credentials"

def update_metadata():
    if not SEO_PATH.exists(): return
    seo = json.loads(SEO_PATH.read_text(encoding="utf-8"))
    
    token_file = CRED_DIR / "youtube_token.json"
    if not token_file.exists(): return
    
    creds_data = json.loads(token_file.read_text())
    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_data, ["https://www.googleapis.com/auth/youtube.force-ssl"])
    youtube = build("youtube", "v3", credentials=creds)
    
    print(f"🚀 [YouTube] Updating SEO for {VIDEO_ID}...")
    
    # 1. Get current snippet
    res = youtube.videos().list(part="snippet", id=VIDEO_ID).execute()
    if not res.get("items"): 
        print("❌ Video not found.")
        return
        
    snippet = res["items"][0]["snippet"]
    snippet["title"] = seo["title"]
    snippet["description"] = seo["description"]
    
    # 2. Update
    youtube.videos().update(part="snippet", body={
        "id": VIDEO_ID,
        "snippet": snippet
    }).execute()
    
    print("✅ [YouTube] SEO Updated successfully.")

if __name__ == "__main__":
    update_metadata()
