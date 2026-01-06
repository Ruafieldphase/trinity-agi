#!/bin/bash
# AGI Systemd Service Installer
# 이 스크립트는 AGI의 모든 systemd 서비스를 설치하고 활성화합니다.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/systemd"
SYSTEMD_DIR="/etc/systemd/system"

echo "═══════════════════════════════════════"
echo "🌟 AGI Systemd Service Installer"
echo "═══════════════════════════════════════"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Create log directory
echo "📁 Creating log directory..."
mkdir -p /home/bino/agi/logs
chown bino:bino /home/bino/agi/logs

# Install services
for service_file in "$SERVICE_DIR"/*.service; do
    service_name=$(basename "$service_file")
    echo "📦 Installing $service_name..."
    
    cp "$service_file" "$SYSTEMD_DIR/"
    chmod 644 "$SYSTEMD_DIR/$service_name"
    
    echo "   ✅ Copied to $SYSTEMD_DIR/"
done

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "🚀 Enabling services..."
systemctl enable agi-rhythm.service
systemctl enable agi-body.service
systemctl enable agi-collaboration.service
systemctl enable agi-sena.service

echo ""
echo "═══════════════════════════════════════"
echo "✅ Installation Complete!"
echo "═══════════════════════════════════════"
echo ""
echo "📊 To start all services:"
echo "   sudo systemctl start agi-rhythm"
echo "   sudo systemctl start agi-body "
echo "   sudo systemctl start agi-collaboration"
echo "   sudo systemctl start agi-sena"
echo ""
echo "Or start everything at once:"
echo "   sudo systemctl start agi-*"
echo ""
echo "📋 To check status:"
echo "   sudo systemctl status agi-*"
echo ""
echo "📜 To view logs:"
echo "   sudo journalctl -u agi-rhythm -f"
echo "   tail -f /home/bino/agi/logs/*.log"
