#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Restarting dashboard to force file sync..."
pm2 restart agi-dashboard

sleep 3

echo ""
echo "Checking file content on Linux..."
grep -A 2 "const severityColor" ~/agi/dashboard/src/components/ProposalCard.tsx

echo ""
echo "✅ Dashboard restarted!"
