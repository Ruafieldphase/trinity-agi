#!/bin/bash
# AGI Dashboard Startup Script for Linux

cd ~/agi/dashboard || exit 1

# Kill any existing Next.js processes
pkill -f "next dev" 2>/dev/null || true
sleep 2

# Start Next.js dev server
echo "Starting AGI Dashboard..."
nohup npm run dev > ~/agi/outputs/dashboard.log 2>&1 &

sleep 5

# Verify
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Dashboard is running at http://192.168.119.128:3000"
else
    echo "❌ Dashboard failed to start. Check ~/agi/outputs/dashboard.log"
    exit 1
fi
