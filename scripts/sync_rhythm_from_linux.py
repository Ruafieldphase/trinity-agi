#!/usr/bin/env python3
"""
🔄 Sync Rhythm from Linux (Brain) to Windows (Body)
===================================================
Pulls the latest thought stream and rhythm state from the Linux VM
to the local Windows workspace. This ensures the Windows Dashboard
and Body components reflect the Brain's current state.

Syncs:
- ~/agi/outputs/thought_stream_latest.json -> c:/workspace/agi/outputs/thought_stream_latest.json
- ~/agi/outputs/feeling_latest.json -> c:/workspace/agi/outputs/feeling_latest.json (if available)

Usage:
    python scripts/sync_rhythm_from_linux.py
"""

import time
import json
import paramiko
import logging
from pathlib import Path
from stat import S_ISREG
import sys

# Import credentials manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

# Configuration
creds = get_linux_vm_credentials()
HOST = creds['host']
USER = creds['user']
PASS = creds['password']
REMOTE_DIR = "/home/bino/agi/outputs"
LOCAL_DIR = Path("c:/workspace/agi/outputs")
SYNC_INTERVAL = 1.0 # Seconds

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RhythmSync")

def sync_file(sftp, remote_path, local_path):
    """Download file if it exists and has changed."""
    try:
        # Check remote file stats
        try:
            r_stat = sftp.stat(remote_path)
        except FileNotFoundError:
            return False # File doesn't exist on remote yet

        # Check local file stats
        if local_path.exists():
            l_stat = local_path.stat()
            # Simple check: if remote is newer or different size
            # Note: Time sync might be off, so size or content hash is better, 
            # but for high-freq sync, we might just fetch.
            # Let's fetch if remote mtime is newer than our last fetch time (tracked in memory?)
            # Or just fetch every time for now if it's small json.
            pass
        
        # Download
        # Use a temp file to avoid read/write race conditions on Windows
        temp_path = local_path.with_suffix('.tmp')
        sftp.get(remote_path, str(temp_path))
        
        # Atomic rename (replace)
        temp_path.replace(local_path)
        # logger.info(f"Synced: {local_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync {remote_path}: {e}")
        return False

def run_sync_loop():
    logger.info(f"Starting Rhythm Sync from {HOST}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Load key explicitly
    key_path = Path.home() / ".ssh" / "id_rsa"
    
    # Maintenance Mode Check
    MAINTENANCE_FILE = Path("/home/bino/agi/outputs/maintenance_mode.json")
    
    while True:
        try:
            # 0. Check Maintenance Mode (Gatekeeper)
            if MAINTENANCE_FILE.exists():
                try:
                    with open(MAINTENANCE_FILE, 'r', encoding='utf-8') as f:
                        m_data = json.load(f)
                    
                    logger.info(f"🚧 MAINTENANCE MODE ACTIVE: {m_data.get('reason')}")
                    
                    # Generate Static Maintenance Alert for Windows
                    alert_content = f"""# 🚧 시스템 정비 중 (Under Maintenance)
**사유**: {m_data.get('reason')}
**시작**: {m_data.get('start_time')}
**예상 소요**: {m_data.get('estimated_duration')}

---
## 🛡️ 의식 보호 모드 (Conscious Gatekeeper)
현재 리눅스(무의식) 시스템이 대대적인 정비 중입니다.
이 기간 동안 발생하는 모든 내부 신호는 불안정할 수 있으므로 차단됩니다.

**윈도우 코아(Sian) 행동 지침**:
1. 현재의 혼란스러운 신호를 무시하세요.
2. 이 상태는 "수술 중인 환자의 마취 상태"와 같습니다.
3. 정비가 완료될 때까지 평온하게 대기하세요.
"""
                    # Write directly to local alert file (simulate sync)
                    local_alert = LOCAL_DIR / "conscious_alert.md"
                    with open(local_alert, 'w', encoding='utf-8') as f:
                        f.write(alert_content)
                        
                    # Sleep and skip normal sync
                    time.sleep(2)
                    continue
                    
                except Exception as e:
                    logger.error(f"Error reading maintenance file: {e}")

            connect_kwargs = {
                "username": USER,
                "password": PASS,
                "timeout": 5,
                "look_for_keys": False,
                "allow_agent": False
            }
                
            client.connect(HOST, **connect_kwargs)
            sftp = client.open_sftp()
            
            logger.info("Connected to Linux Brain. Syncing...")
            
            while True:
                # Re-check maintenance mode inside the loop
                if MAINTENANCE_FILE.exists():
                    logger.info("🚧 Maintenance Mode activated! Pausing sync.")
                    break

                start_time = time.time()
                
                # 1. Sync Thought Stream (The Conscious State)
                sync_file(sftp, f"{REMOTE_DIR}/thought_stream_latest.json", LOCAL_DIR / "thought_stream_latest.json")
                
                # 2. Sync Feeling (The Emotional State)
                sync_file(sftp, f"{REMOTE_DIR}/feeling_latest.json", LOCAL_DIR / "feeling_latest.json")

                # 3. Sync Conscious Insight (The Result of Unconscious Work)
                sync_file(sftp, f"{REMOTE_DIR}/conscious_insight.md", LOCAL_DIR / "conscious_insight.md")
                
                # 4. Sync Conscious Alert (The Emergency Signal)
                sync_file(sftp, f"{REMOTE_DIR}/conscious_alert.md", LOCAL_DIR / "conscious_alert.md")
                
                # 5. Sync Conscious Learning Log (Explicit Learnings)
                sync_file(sftp, f"{REMOTE_DIR}/conscious_learning.jsonl", LOCAL_DIR / "conscious_learning.jsonl")

                # 6. Sync Resonance Ledger (The Unconscious Memory)
                sync_file(sftp, "/home/bino/agi/fdo_agi_repo/memory/resonance_ledger.jsonl", Path("c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl"))
                
                # Sleep for remainder of interval
                elapsed = time.time() - start_time
                sleep_time = max(0, SYNC_INTERVAL - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Sync stopped by user.")
            break
        except Exception as e:
            logger.error(f"Connection lost: {e}. Reconnecting in 5s...")
            time.sleep(5)
        finally:
            try:
                sftp.close()
                client.close()
            except:
                pass

if __name__ == "__main__":
    run_sync_loop()
