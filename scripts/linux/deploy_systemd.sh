#!/bin/bash
# Deploy AGI Systemd Services to Linux VM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_HOST="binoche@192.168.190.146"
REMOTE_DIR="/home/bino/agi/scripts/linux"

echo "═══════════════════════════════════════"
echo "📦 Deploying AGI Systemd Services"
echo "═══════════════════════════════════════"

# Copy service files and installer
echo "📁 Copying files to Linux VM..."
ssh "$LINUX_HOST" "mkdir -p $REMOTE_DIR/systemd"
scp "$SCRIPT_DIR/systemd/"*.service "$LINUX_HOST:$REMOTE_DIR/systemd/"
scp "$SCRIPT_DIR/install_systemd_services.sh" "$LINUX_HOST:$REMOTE_DIR/"

# Make installer executable
echo "🔧 Setting permissions..."
ssh "$LINUX_HOST" "chmod +x $REMOTE_DIR/install_systemd_services.sh"

echo ""
echo "✅ Files deployed successfully!"
echo ""
echo "📋 Next steps (run on Linux VM):"
echo "   ssh $LINUX_HOST"
echo "   cd $REMOTE_DIR"
echo "   sudo ./install_systemd_services.sh"
echo ""
echo "Or run remotely from Windows:"
echo "   ssh $LINUX_HOST 'cd $REMOTE_DIR && sudo ./install_systemd_services.sh'"
