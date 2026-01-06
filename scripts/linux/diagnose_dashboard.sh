#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=== PM2 Status ==="
pm2 status

echo ""
echo "=== Port Binding ==="
sudo ss -tulpn | grep 3000

echo ""
echo "=== Recent Logs ==="
pm2 logs agi-dashboard --lines 20 --nostream

echo ""
echo "=== Process Details ==="
pm2 describe agi-dashboard
