#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=== Setting up Python venv on Linux ==="
cd ~/agi/fdo_agi_repo

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install google-generativeai python-dotenv
    echo "✅ Python venv created!"
else
    echo "✅ Python venv already exists"
fi

echo ""
echo "=== Testing Python venv ==="
~/agi/fdo_agi_repo/.venv/bin/python --version

echo ""
echo "=== Stopping dashboard ==="
pm2 stop agi-dashboard

echo "=== Clearing cache ==="
cd ~/agi/dashboard
rm -rf .next

echo "=== Starting dashboard fresh ==="
pm2 start npm --name "agi-dashboard" -- run dev
pm2 save

echo ""
echo "✅ Setup complete!"
sleep 3
pm2 logs agi-dashboard --lines 10 --nostream
