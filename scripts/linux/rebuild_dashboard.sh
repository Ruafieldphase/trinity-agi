#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Navigate to dashboard
cd ~/agi/dashboard

# Build the project
echo "Building dashboard..."
npm run build

# Restart PM2
echo "Restarting dashboard..."
pm2 restart agi-dashboard

echo "✅ Dashboard Rebuild Complete!"
