import yt_dlp
import json

url = "https://www.youtube.com/watch?v=yYyWwQo_wKk"
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'extract_flat': True,
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(json.dumps(info, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
