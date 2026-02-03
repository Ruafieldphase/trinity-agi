import httpx
import json
import asyncio
import time

async def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "glm-4.7-flash:latest",
        "prompt": "Say 'Pong'",
        "stream": False
    }
    try:
        print(f"[{time.strftime('%H:%M:%S')}] Connecting to {url}...")
        async with httpx.AsyncClient(timeout=300.0) as client:
            start = time.time()
            response = await client.post(url, json=payload)
            duration = time.time() - start
            print(f"[{time.strftime('%H:%M:%S')}] Status: {response.status_code} (took {duration:.2f}s)")
            print(f"Response Content: {response.text[:200]}...")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
