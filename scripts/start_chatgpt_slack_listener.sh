#!/bin/bash
# Start ChatGPT Slack Listener
# Uses the python from ~/.agi_venv

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXEC="$HOME/.agi_venv/bin/python"
SCRIPT_PATH="$BASE_DIR/scripts/chatgpt_slack_listener.py"

echo "Starting ChatGPT Slack Listener..."
echo "Python: $PYTHON_EXEC"
echo "Script: $SCRIPT_PATH"

"$PYTHON_EXEC" "$SCRIPT_PATH"
