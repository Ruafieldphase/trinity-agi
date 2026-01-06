#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Stopping dashboard..."
pm2 stop agi-dashboard

echo "Clearing Next.js cache..."
cd ~/agi/dashboard
rm -rf .next

echo "Restarting dashboard..."
pm2 restart agi-dashboard

echo "✅ Cache cleared and restarted!"
sleep 3
pm2 logs agi-dashboard --lines 5 --nostream
