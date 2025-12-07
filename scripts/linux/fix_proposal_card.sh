#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd ~/agi/dashboard/src/components

echo "Current line 27:"
sed -n '27p' ProposalCard.tsx

echo ""
echo "Applying fix..."
sed -i "s/\[proposal\.metadata\.severity\]/[proposal.metadata?.severity || 'low']/g" ProposalCard.tsx

echo "Fixing line 47..."
sed -i "s/proposal\.metadata\.severity === 'critical'/proposal.metadata?.severity === 'critical'/g" ProposalCard.tsx

echo ""
echo "Modified line 27:"
sed -n '27p' ProposalCard.tsx

echo ""
echo "Restarting dashboard..."
cd ~/agi/dashboard
rm -rf .next
pm2 restart agi-dashboard

echo "✅ Fix applied and restarted!"
