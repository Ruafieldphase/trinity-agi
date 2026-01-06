#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd ~/agi/dashboard

echo "Stopping PM2..."
pm2 delete agi-dashboard 2>/dev/null || true

echo "Starting dashboard in dev mode..."
pm2 start npm --name "agi-dashboard" -- run dev

pm2 save

echo "✅ Dashboard started in dev mode!"
pm2 logs agi-dashboard --lines 5 --nostream
