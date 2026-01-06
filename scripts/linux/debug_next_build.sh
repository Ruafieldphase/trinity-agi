#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd ~/agi/dashboard

echo "=== Checking .next directory ==="
ls -la .next 2>&1 || echo ".next directory not found!"

echo ""
echo "=== Stopping PM2 ==="
pm2 stop agi-dashboard

echo ""
echo "=== Running next start directly ==="
timeout 10s npm start || true

echo ""
echo "=== Restarting with PM2 ==="
pm2 restart agi-dashboard
pm2 logs agi-dashboard --lines 10 --nostream
