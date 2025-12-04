#!/bin/bash
# Fix Dashboard Startup with NVM

# 1. Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 2. Use Node 20
nvm use 20

# 3. Go to directory
cd ~/agi/dashboard

# 4. Get absolute path to Node
NODE_BIN=$(which node)
echo "Using Node: $NODE_BIN"

# 5. Clean PM2
pm2 delete agi-dashboard 2>/dev/null || true

# 6. Start directly using Next.js JS binary
# Point to the actual JS file, not the bin wrapper
NEXT_JS_PATH="./node_modules/next/dist/bin/next"

pm2 start $NEXT_JS_PATH --name agi-dashboard --interpreter "$NODE_BIN" -- dev

# 7. Save PM2 list
pm2 save

echo "✅ Dashboard started with PM2"
sleep 5
pm2 list
