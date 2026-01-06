#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Applying cache fix to API..."
cd ~/agi/dashboard/src/app/api/system-status

# Add force-dynamic export
sed -i '/import path from/a\export const dynamic = "force-dynamic";' route.ts

echo "Modified route.ts:"
head -10 route.ts

echo ""
echo "Restarting dashboard..."
cd ~/agi/dashboard
rm -rf .next
pm2 restart agi-dashboard

echo "✅ Cache fix applied!"
