"""
Configuration for AGI Unified Frontend Services
"""
import sys
from pathlib import Path

# Add scripts directory to path for credentials_manager
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

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
WINDOWS_AGI_ROOT = Path(__file__).parent.parent
BODY_PATH = WINDOWS_AGI_ROOT / "body"
MIND_PATH = WINDOWS_AGI_ROOT / "mind"
OUTPUTS_PATH = WINDOWS_AGI_ROOT / "outputs"

# Linux Paths
LINUX_AGI_ROOT = "/home/bino/agi"
LINUX_OUTPUTS = f"{LINUX_AGI_ROOT}/outputs"

# Update Intervals (seconds)
RHYTHM_UPDATE_INTERVAL = 5  # How often to poll Linux for rhythm data
CONSCIOUSNESS_UPDATE_INTERVAL = 10  # How often to check Windows state
