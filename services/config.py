"""
Configuration for AGI Unified Frontend Services
"""
from agi_core.utils.paths import get_workspace_root, add_to_sys_path

# 워크스페이스 루트 및 경로 설정
WINDOWS_AGI_ROOT = add_to_sys_path()

from credentials_manager import get_linux_vm_credentials

# API Ports
CONSCIOUSNESS_PORT = 8100
UNCONSCIOUS_PORT = 8101
BACKGROUND_SELF_PORT = 8102
AGGREGATOR_PORT = 8104

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Linux VM Credentials
LINUX_CREDS = get_linux_vm_credentials()
LINUX_HOST = LINUX_CREDS['host']
LINUX_USER = LINUX_CREDS['user']
LINUX_PASSWORD = LINUX_CREDS['password']

# Paths
# WINDOWS_AGI_ROOT는 위에서 이미 설정됨 (WINDOWS_AGI_ROOT was already set above)
BODY_PATH = WINDOWS_AGI_ROOT / "body"
MIND_PATH = WINDOWS_AGI_ROOT / "mind"
OUTPUTS_PATH = WINDOWS_AGI_ROOT / "outputs"
INPUTS_PATH = WINDOWS_AGI_ROOT / "inputs"
LOGS_PATH = WINDOWS_AGI_ROOT / "logs"
MEMORY_PATH = WINDOWS_AGI_ROOT / "memory"
CONFIG_PATH = WINDOWS_AGI_ROOT / "config"

# Sub-component Paths
OBS_INTAKE_DIR = INPUTS_PATH / "intake" / "exploration" / "sessions"
RESONANCE_LEDGER = MEMORY_PATH / "resonance_ledger.jsonl"
ARI_BUFFER = MEMORY_PATH / "ari_learning_buffer.json"

# Linux Paths
LINUX_AGI_ROOT = "/home/bino/agi"
LINUX_OUTPUTS = f"{LINUX_AGI_ROOT}/outputs"

# Update Intervals (seconds)
RHYTHM_UPDATE_INTERVAL = 5  # How often to poll Linux for rhythm data
CONSCIOUSNESS_UPDATE_INTERVAL = 10  # How often to check Windows state
