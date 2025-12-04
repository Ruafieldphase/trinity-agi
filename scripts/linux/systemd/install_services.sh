#!/bin/bash
# Install AGI Systemd Services
# This script installs user-level systemd services for AGI components

set -e

echo "🔧 Installing AGI Systemd Services..."

# Service directory
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

# AGI directory
AGI_DIR="$HOME/agi"

# Copy service files
echo "📋 Copying service files..."
cp "$AGI_DIR/scripts/linux/systemd/agi-rhythm.service" "$SERVICE_DIR/"
cp "$AGI_DIR/scripts/linux/systemd/agi-collaboration.service" "$SERVICE_DIR/"
cp "$AGI_DIR/scripts/linux/systemd/agi-sena.service" "$SERVICE_DIR/"

echo "✅ Service files copied"

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload

# Enable services
echo "⚙️  Enabling services..."
systemctl --user enable agi-rhythm.service
systemctl --user enable agi-collaboration.service

echo "✅ Services enabled"

# Start services
echo "▶️  Starting services..."
systemctl --user start agi-rhythm.service
systemctl --user start agi-collaboration.service

echo "✅ Services started"

# Check status
echo ""
echo "📊 Service Status:"
echo "=================="
systemctl --user status agi-rhythm.service --no-pager || true
echo ""
systemctl --user status agi-collaboration.service --no-pager || true

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Useful commands:"
echo "  systemctl --user status agi-rhythm"
echo "  systemctl --user restart agi-rhythm"
echo "  systemctl --user stop agi-rhythm"
echo "  journalctl --user -u agi-rhythm -f"
