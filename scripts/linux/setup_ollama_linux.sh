#!/bin/bash

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure to listen on all interfaces (0.0.0.0)
# This allows the Windows Orchestrator to connect to it.
sudo mkdir -p /etc/systemd/system/ollama.service.d
echo "[Service]
Environment=\"OLLAMA_HOST=0.0.0.0\"" | sudo tee /etc/systemd/system/ollama.service.d/environment.conf

# Reload and Restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo "✅ Ollama Setup Complete! Listening on 0.0.0.0:11434"
