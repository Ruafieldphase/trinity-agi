#!/bin/bash
# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Applying API fix on Linux..."
cd ~/agi/dashboard/src/app/api/proposals/approve

# Replace python command with absolute path
sed -i 's|exec(`python|exec(`"${pythonPath}"|g' route.ts
sed -i '/const scriptPath/a\        const pythonPath = path.resolve(process.cwd(), '"'"'../fdo_agi_repo/.venv/bin/python'"'"');' route.ts

echo "Modified route.ts:"
grep -A 3 "const scriptPath" route.ts

echo ""
echo "Restarting dashboard..."
cd ~/agi/dashboard
pm2 restart agi-dashboard

echo "✅ API fix applied!"
