#!/bin/bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js v20
nvm install 20
nvm use 20
nvm alias default 20

# Install PM2 globally
npm install -g pm2

# Navigate to dashboard
cd ~/agi/dashboard

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the project
echo "Building dashboard..."
npm run build

# Start with PM2
echo "Starting dashboard..."
pm2 delete agi-dashboard 2>/dev/null || true
pm2 start npm --name "agi-dashboard" -- start

# Save PM2 list
pm2 save

echo "✅ Dashboard Setup Complete!"
