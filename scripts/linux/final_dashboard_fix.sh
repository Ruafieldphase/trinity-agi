#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=== Installing Python dependencies globally (user) ==="
pip3 install --user google-generativeai python-dot env

echo ""
echo "=== Deleting PM2 app and restarting fresh ==="
pm2 delete agi-dashboard 2>/dev/null || true

cd ~/agi/dashboard
rm -rf .next

pm2 start npm --name "agi-dashboard" -- run dev
pm2 save

echo ""
echo "✅ Dashboard restarted with python3!"
sleep 5
pm2 logs agi-dashboard --lines 10 --nostream
