#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=== Checking API route file ==="
tail -25 ~/agi/dashboard/src/app/api/proposals/approve/route.ts

echo ""
echo "=== Restarting dashboard ==="
pm2 restart agi-dashboard

sleep 3

echo ""
echo "=== Recent PM2 logs ==="
pm2 logs agi-dashboard --lines 30 --nostream
