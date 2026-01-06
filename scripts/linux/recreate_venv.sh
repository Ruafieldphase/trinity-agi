#!/bin/bash
echo "=== Removing broken venv ==="
rm -rf ~/agi/fdo_agi_repo/.venv

echo "=== Creating fresh Python venv ==="
cd ~/agi/fdo_agi_repo
python3 -m venv .venv

echo "=== Activating and installing dependencies ==="
source .venv/bin/activate
pip install --upgrade pip
pip install google-generativeai python-dotenv psutil requests

echo ""
echo "=== Testing venv ==="
~/.venv/bin/python --version
which python

echo ""
echo "✅ Python venv ready!"
