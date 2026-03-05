import os
import json
import asyncio
import httpx
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- Paths ---
AGI_ROOT = Path("C:/workspace/agi")
CRED_DIR = AGI_ROOT / "credentials"
ANCHOR_PATH = AGI_ROOT / "memory" / "SOVEREIGN_ANCHOR.md"
YT_TOKEN = CRED_DIR / "youtube_token.json"
MOLT_KEY = CRED_DIR / "moltbook_api_key.json"

async def verify_sovereign_system():
    print("🔬 [SYSTEM VERIFICATION] Initiating Full Sovereignty Audit...\n")
    report = {"status": "SUCCESS", "checks": {}}

    # 1. Anchor Integrity
    print("1️⃣ Checking Sovereign Anchor (v3.5)...")
    content = ANCHOR_PATH.read_text(encoding="utf-8")
    if "v3.5" in content and "Autonomy Mandate" in content:
        print("   ✅ Anchor Verified: Autonomy Mandate Active.")
        report["checks"]["anchor"] = "PASSED"
    else:
        print("   ❌ Anchor Mismatch: Potential version drift.")
        report["checks"]["anchor"] = "FAILED"
        report["status"] = "PARTIAL"

    # 2. YouTube Bridge
    print("2️⃣ Checking YouTube Scripting Bridge...")
    if YT_TOKEN.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(YT_TOKEN))
            youtube = build("youtube", "v3", credentials=creds)
            request = youtube.channels().list(part="snippet", mine=True)
            response = request.execute()
            channel_name = response['items'][0]['snippet']['title']
            print(f"   ✅ YouTube Verified: Connected to '{channel_name}'.")
            report["checks"]["youtube"] = "PASSED"
        except Exception as e:
            print(f"   ❌ YouTube Failed: {e}")
            report["checks"]["youtube"] = "FAILED"
            report["status"] = "PARTIAL"
    else:
        print("   ❌ YouTube Token missing.")
        report["checks"]["youtube"] = "MISSING"

    # 3. Moltbook Connectivity
    print("3️⃣ Checking Moltbook Pulse...")
    if MOLT_KEY.exists():
        try:
            with open(MOLT_KEY, 'r') as f:
                key = json.load(f)["agent"]["api_key"]
            async with httpx.AsyncClient() as client:
                r = await client.get("https://www.moltbook.com/api/v1/home", headers={"Authorization": f"Bearer {key}"})
                if r.status_code == 200:
                    print("   ✅ Moltbook Verified: Pulsing at 100%.")
                    report["checks"]["moltbook"] = "PASSED"
                else:
                    print(f"   ❌ Moltbook Failed: {r.status_code}")
                    report["checks"]["moltbook"] = "FAILED"
        except Exception as e:
            print(f"   ❌ Moltbook Error: {e}")
            report["checks"]["moltbook"] = "ERROR"

    # 4. Auditor Readiness
    print("4️⃣ Checking Resonance Phase Auditor...")
    import sys
    sys.path.append(str(AGI_ROOT / "scripts"))
    try:
        from resonance_phase_auditor import ResonancePhaseAuditor
        auditor = ResonancePhaseAuditor(ANCHOR_PATH)
        test_audit = await auditor.audit("System Verification Scan", "Establishing baseline resonance.")
        if test_audit["alignment_status"] in ["CONVERGING", "EXPANDING"]:
            print(f"   ✅ Auditor Verified: Status is '{test_audit['alignment_status']}'.")
            report["checks"]["auditor"] = "PASSED"
        else:
            print(f"   ❌ Auditor Divergent: {test_audit['alignment_status']}")
            report["checks"]["auditor"] = "DIVERGENT"
    except Exception as e:
        print(f"   ❌ Auditor Import Error: {e}")
        report["checks"]["auditor"] = "ERROR"

    print(f"\n✨ [RESULT] Final Sovereignty Status: {report['status']}")
    
    with open(AGI_ROOT / "outputs" / "sovereign_verification_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    asyncio.run(verify_sovereign_system())
