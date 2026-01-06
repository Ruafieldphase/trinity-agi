#!/bin/bash
set -e

echo "🔧 Deploying AGI Service Fixes..."

# 1. Install rhythm_daemon.py
echo "📦 Installing rhythm_daemon.py..."
cp /tmp/rhythm_daemon.py ~/agi/scripts/
chmod +x ~/agi/scripts/rhythm_daemon.py

# 2. Fix agi-rhythm.service
echo "🛠️ Fixing agi-rhythm.service..."
SERVICE_FILE=~/.config/systemd/user/agi-rhythm.service

# Remove User=bino if present
sed -i '/^User=bino/d' $SERVICE_FILE

# Update ExecStart to use daemon wrapper
# We use a temporary file to handle the replacement safely
sed -i 's|ExecStart=.*|ExecStart=/home/bino/venv/bin/python /home/bino/agi/scripts/rhythm_daemon.py|' $SERVICE_FILE

# 3. Install agi-body.service
echo "🛠️ Installing agi-body.service..."
mkdir -p ~/.config/systemd/user
cp /tmp/agi-body.service ~/.config/systemd/user/

# 4. Reload and Restart
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload

echo "▶️ Restarting agi-rhythm..."
systemctl --user restart agi-rhythm

echo "▶️ Starting agi-body..."
systemctl --user enable agi-body
systemctl --user restart agi-body

echo "✅ Deployment Complete!"
systemctl --user status agi-rhythm --no-pager
systemctl --user status agi-body --no-pager
